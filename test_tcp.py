# -*- coding: utf-8 -*-
"""TCP 连通性预筛：对每个节点 server:port 做 TCP 连接测试。

优化：
  - 超时 2s（原 3s）
  - 源质量反馈：跳过连续 2 次 0 产出的源（每 3 次全量测一次以便恢复）
  - 订阅缓存：文件 hash 未变且缓存 <=2 天的节点直接复用上次结果
"""
import hashlib, io, json, os, socket, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TIMEOUT = 2.0
MAX_WORKERS = 400
CACHE_TTL = 2 * 86400  # 2 天

def file_md5(sub_name):
    try:
        with open(os.path.join("subs", sub_name), "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def node_key(n):
    return "{}|{}|{}".format(n["type"], str(n.get("server", "")).lower(), n.get("port"))

def tcp_test(node):
    try:
        host = node["server"]
        port = int(str(node.get("port") or 0).strip().rstrip("?"))
    except Exception:
        node["tcp_ok"] = False
        node["tcp_ms"] = None
        node["tcp_err"] = "bad addr"
        return node
    if not host or not (1 <= port <= 65535):
        node["tcp_ok"] = False
        node["tcp_ms"] = None
        node["tcp_err"] = "bad addr"
        return node
    t0 = time.time()
    try:
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
    total = len(nodes)
    print(f"total nodes: {total}", flush=True)

    # ---- 1) 源质量反馈：跳过连续 2 次 0 产出的源（每 3 次全量测一次） ----
    dead_subs = set()
    try:
        st = json.load(open("source_stats.json", encoding="utf-8"))
        if st.get("runs", 0) % 3 != 0:
            for sub, info in st.get("subs", {}).items():
                if info.get("zero_streak", 0) >= 2:
                    dead_subs.add(sub)
        if dead_subs:
            print(f"source feedback: skip {len(dead_subs)} dead subs: {sorted(dead_subs)}", flush=True)
    except Exception:
        pass

    # ---- 2) 订阅缓存：hash 未变且未过期 -> 复用上次结果 ----
    try:
        cache = json.load(open("nodes/sub_cache.json", encoding="utf-8"))
    except Exception:
        cache = {"subs": {}}
    now = time.time()
    cache_hit = 0

    pre = []
    for n in nodes:
        sub = n.get("_sub", "")
        if sub in dead_subs:
            continue
        csub = cache.get("subs", {}).get(sub)
        if csub and csub.get("hash") == file_md5(sub) and (now - csub.get("ts", 0)) <= CACHE_TTL:
            cn = csub.get("nodes", {}).get(node_key(n))
            if cn and cn.get("tcp_ok"):
                n = dict(n)
                n["tcp_ok"] = True
                n["tcp_ms"] = cn.get("tcp_ms")
                n["tcp_err"] = None
                n["cached"] = True
                n["_cached_delay"] = cn.get("delay_ms")
                pre.append(n)
                cache_hit += 1
                continue
        pre.append(n)
    nodes = pre
    print(f"after dead-src skip & cache: {len(nodes)} to test (cache hits: {cache_hit})", flush=True)

    # ---- 3) 并发 TCP 测试 ----
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
