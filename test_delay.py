# -*- coding: utf-8 -*-
"""通过 mihomo API 对每个节点做真实协议延迟测试（分块 + 健康检查 + 重试）。"""
import io, json, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API = "http://127.0.0.1:9098"
DELAY_URL = "http://www.gstatic.com/generate_204"
TIMEOUT_MS = 3500
CONCURRENCY = 16
CHUNK = 400

def api_get(path, timeout=12):
    with urllib.request.urlopen(API + path, timeout=timeout) as r:
        return r.read()

def healthy():
    try:
        api_get("/version", timeout=4)
        return True
    except Exception:
        return False

def test_one(name):
    q = urllib.parse.quote(name, safe="")
    url = "{}/proxies/{}/delay?timeout={}&url={}".format(API, q, TIMEOUT_MS, urllib.parse.quote(DELAY_URL, safe=""))
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=12) as r:
                body = r.read().decode()
            d = json.loads(body)
            return name, d.get("delay"), None
        except Exception as e:
            reason = getattr(e, "reason", None)
            detail = str(reason)[:60] if reason else type(e).__name__
            if attempt < 2 and ("timed out" in detail or "timedout" in detail.lower() or "reset" in detail.lower()):
                time.sleep(1.5)
                continue
            return name, None, detail
    return name, None, "retry-exhausted"

def run_chunk(names):
    results = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(test_one, n): n for n in names}
        for fut in as_completed(futs):
            name, delay, err = fut.result()
            results[name] = {"delay_ms": delay, "err": err}
    return results

def main():
    tcp_ok = json.load(open("nodes/tcp_ok.json", encoding="utf-8"))
    used = {}
    names = []
    for i, n in enumerate(tcp_ok):
        base = (n.get("name") or f"{n['type']}-{n['server']}")[:60]
        if base in used:
            used[base] += 1
            base = f"{base}#{used[base]}"
        else:
            used[base] = 1
        names.append(base)
    print(f"nodes: {len(names)}", flush=True)
    if not healthy():
        print("API DOWN at start", flush=True)
        return

    # 源质量权重（alive/total），用于排序：优质源的节点优先测
    sub_rate = {}
    try:
        st = json.load(open("source_stats.json", encoding="utf-8"))
        for sub, info in st.get("subs", {}).items():
            t = info.get("total", 0)
            sub_rate[sub] = (info.get("alive", 0) / t) if t else 0.0
    except Exception:
        pass

    # 排序：源质量权重降序 -> TCP 延迟升序（先测快的，Ctrl-C 中断也有好结果）
    order = sorted(
        range(len(tcp_ok)),
        key=lambda i: (-sub_rate.get(tcp_ok[i].get("_sub", ""), 0.0),
                       tcp_ok[i].get("tcp_ms") is None,
                       tcp_ok[i].get("tcp_ms") or 99999),
    )

    # 缓存节点直接复用上次延迟结果，不重复测试
    cached_results = {}
    to_test = []
    for i in order:
        nm = names[i]
        if tcp_ok[i].get("cached"):
            cached_results[nm] = {"delay_ms": tcp_ok[i].get("_cached_delay"), "err": None}
        else:
            to_test.append(nm)
    if cached_results:
        print(f"cache reuse: {len(cached_results)} nodes skip re-test", flush=True)

    results = dict(cached_results)
    done = len(cached_results)
    for s in range(0, len(to_test), CHUNK):
        chunk = to_test[s:s + CHUNK]
        chunk_res = run_chunk(chunk)
        results.update(chunk_res)
        done += len(chunk)
        alive = sum(1 for r in results.values() if r["delay_ms"] is not None)
        print(f"  {done}/{len(names)} alive={alive}", flush=True)
        # 健康检查
        if not healthy():
            print(f"  API down after chunk, waiting for recovery...", flush=True)
            for _ in range(30):
                time.sleep(2)
                if healthy():
                    break

    alive = [r for r in results.values() if r["delay_ms"] is not None]
    print(f"delay-test alive: {len(alive)}/{len(results)}", flush=True)
    # 保存
    out = []
    for i, n in enumerate(tcp_ok):
        r = results.get(names[i], {})
        n = dict(n)
        n["test_name"] = names[i]
        n["delay_ms"] = r.get("delay_ms")
        n["delay_err"] = r.get("err")
        out.append(n)
    with open("nodes/merged_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    with open("nodes/delay_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved nodes/merged_results.json & delay_results.json", flush=True)

    # 更新源质量统计（供下次运行跳过 0 产出的源）
    from collections import defaultdict
    by_sub = defaultdict(lambda: [0, 0])
    for n in out:
        sub = n.get("_sub", "?")
        by_sub[sub][1] += 1
        if n.get("delay_ms") is not None:
            by_sub[sub][0] += 1
    try:
        stats = json.load(open("source_stats.json", encoding="utf-8"))
    except Exception:
        stats = {"runs": 0, "subs": {}}
    stats["runs"] = stats.get("runs", 0) + 1
    subs = stats.setdefault("subs", {})
    for sub, (a, t) in by_sub.items():
        prev = subs.get(sub, {})
        zs = 0 if a > 0 else prev.get("zero_streak", 0) + 1
        subs[sub] = {"alive": a, "total": t, "zero_streak": zs,
                     "checked_at": time.strftime("%Y-%m-%d")}
    with open("source_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("updated source_stats.json", flush=True)

if __name__ == "__main__":
    main()
