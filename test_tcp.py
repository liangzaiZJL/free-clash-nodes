# -*- coding: utf-8 -*-
"""TCP 连通性预筛：对每个节点 server:port 做 TCP 连接测试，记录延迟。"""
import io, json, socket, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TIMEOUT = 3.0
MAX_WORKERS = 400

def tcp_test(node):
    host, port = node["server"], node.get("port") or 0
    try:
        port = int(port)
    except Exception:
        port = 0
    if not host or not (1 <= port <= 65535):
        node["tcp_ok"] = False
        node["tcp_ms"] = None
        node["tcp_err"] = "bad addr"
        return node
    t0 = None
    try:
        import time
        t0 = time.time()
        s = socket.create_connection((host, port), timeout=TIMEOUT)
        s.close()
        node["tcp_ok"] = True
        node["tcp_ms"] = round((time.time() - t0) * 1000, 1)
        node["tcp_err"] = None
    except Exception as e:
        node["tcp_ok"] = False
        node["tcp_ms"] = None
        node["tcp_err"] = type(e).__name__
    return node

def main():
    nodes = json.load(open("nodes/dedup_nodes.json", encoding="utf-8"))
    print(f"total nodes: {len(nodes)}", flush=True)
    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(tcp_test, n): n for n in nodes}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            if done % 1000 == 0:
                print(f"  {done}/{len(nodes)}", flush=True)
    ok = [r for r in results if r["tcp_ok"]]
    print(f"TCP OK: {len(ok)}/{len(results)} ({len(ok)*100//max(len(results),1)}%)", flush=True)
    with open("nodes/tcp_ok.json", "w", encoding="utf-8") as f:
        json.dump(ok, f, ensure_ascii=False)
    with open("nodes/tcp_all.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)
    # 汇总延迟分布
    ms = sorted(r["tcp_ms"] for r in ok if r.get("tcp_ms") is not None)
    if ms:
        import statistics
        print(f"delay: median={statistics.median(ms):.0f}ms p90={ms[int(len(ms)*0.9)]:.0f}ms min={ms[0]:.0f}ms", flush=True)

if __name__ == "__main__":
    main()
