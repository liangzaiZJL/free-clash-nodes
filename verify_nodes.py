# -*- coding: utf-8 -*-
"""对首轮存活的节点做二次延迟验证，过滤抖动节点；并更新订阅缓存。"""
import hashlib, io, json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
API = "http://127.0.0.1:9098"
DELAY_URL = "http://www.gstatic.com/generate_204"
TIMEOUT_MS = 3500

def file_md5(sub_name):
    try:
        with open(os.path.join("subs", sub_name), "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def node_key(n):
    return "{}|{}|{}".format(n["type"], str(n.get("server", "")).lower(), n.get("port"))

def test_one(name):
    q = urllib.parse.quote(name, safe="")
    url = "{}/proxies/{}/delay?timeout={}&url={}".format(API, q, TIMEOUT_MS, urllib.parse.quote(DELAY_URL, safe=""))
    try:
        with urllib.request.urlopen(url, timeout=12) as r:
            d = json.loads(r.read().decode())
        return name, d.get("delay"), None
    except Exception as e:
        reason = getattr(e, "reason", None)
        return name, None, (str(reason)[:60] if reason else type(e).__name__)

def main():
    merged = json.load(open("nodes/merged_results.json", encoding="utf-8"))
    alive = [n for n in merged if n.get("delay_ms") is not None]
    print(f"first-round alive: {len(alive)}", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(test_one, n["test_name"]) for n in alive]
        for fut in as_completed(futs):
            name, delay, err = fut.result()
            results[name] = {"delay2_ms": delay, "err2": err}
    keep = []
    for n in alive:
        r = results.get(n["test_name"], {})
        n = dict(n)
        n["delay2_ms"] = r.get("delay2_ms")
        n["delay2_err"] = r.get("err2")
        if r.get("delay2_ms") is not None:
            keep.append(n)
    print(f"second-round alive: {len(keep)}", flush=True)
    keep.sort(key=lambda x: x["delay2_ms"])
    with open("nodes/verified_nodes.json", "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=1)
    print("saved nodes/verified_nodes.json", flush=True)
    for n in keep[:15]:
        print(f"  {n['delay2_ms']:5d}ms {n['type']:10s} {n['server']}:{n['port']}  <{n.get('_sub','?')}>", flush=True)

    # ---- 更新订阅缓存：hash + 每个节点最新结果（供下次跳过重复测试） ----
    try:
        cache = json.load(open("nodes/sub_cache.json", encoding="utf-8"))
    except Exception:
        cache = {"subs": {}}
    subs = cache.setdefault("subs", {})
    now = time.time()
    fresh_subs = set()  # 本次有"非缓存"节点的子源，标记为新鲜
    for n in merged:
        sub = n.get("_sub", "?")
        key = node_key(n)
        cs = subs.setdefault(sub, {"hash": file_md5(sub), "ts": 0, "nodes": {}})
        cs["hash"] = file_md5(sub)
        cs["nodes"][key] = {
            "tcp_ok": n.get("tcp_ok", False),
            "tcp_ms": n.get("tcp_ms"),
            "delay_ms": n.get("delay_ms"),
        }
        if not n.get("cached"):
            fresh_subs.add(sub)
    for n in keep:  # 叠加二次验证结果
        sub = n.get("_sub", "?")
        key = node_key(n)
        cs = subs.setdefault(sub, {"hash": file_md5(sub), "ts": 0, "nodes": {}})
        cs["nodes"][key]["delay2_ms"] = n.get("delay2_ms")
    # 只有"真正重新测过"的子源才刷新时间戳（避免缓存永不失效）
    for sub, cs in subs.items():
        if sub in fresh_subs:
            cs["ts"] = now
    with open("nodes/sub_cache.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    print("updated nodes/sub_cache.json", flush=True)

if __name__ == "__main__":
    main()
