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

    # 按 TCP 延迟升序测试：先测快的，Ctrl-C 提前中断也能拿到较好的结果
    order = sorted(range(len(tcp_ok)),
                   key=lambda i: (tcp_ok[i].get("tcp_ms") is None, tcp_ok[i].get("tcp_ms") or 99999))
    names_ordered = [names[i] for i in order]

    results = {}
    done = 0
    for s in range(0, len(names_ordered), CHUNK):
        chunk = names_ordered[s:s + CHUNK]
        chunk_res = run_chunk(chunk)
        results.update(chunk_res)
        done += len(chunk)
        alive = sum(1 for r in results.values() if r["delay_ms"] is not None)
        print(f"  {done}/{len(names_ordered)} alive={alive}", flush=True)
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

if __name__ == "__main__":
    main()
