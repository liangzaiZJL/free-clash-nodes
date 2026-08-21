# -*- coding: utf-8 -*-
"""通过 mihomo mixed-port 对已验证节点做真实下载速度测试（8MB）。"""
import io, json, sys, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
API = "http://127.0.0.1:9098"
MIXED = "http://127.0.0.1:7898"
SPEED_URL = "http://speed.cloudflare.com/__down?bytes=8388608"  # 8MB
BYTES = 8 * 1024 * 1024
TIME_LIMIT = 30  # 秒
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

def select_proxy(name):
    req = urllib.request.Request(
        API + "/proxies/GLOBAL",
        data=json.dumps({"name": name}).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        r.read()

def speed_via_proxy():
    """通过 7898 混合端口下载，返回 (MB/s, 错误)。"""
    op = urllib.request.build_opener(urllib.request.ProxyHandler({
        "http": MIXED, "https": MIXED}))
    t0 = time.time()
    got = 0
    try:
        with op.open(urllib.request.Request(SPEED_URL, headers=UA), timeout=TIME_LIMIT) as r:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                got += len(chunk)
                if time.time() - t0 > TIME_LIMIT:
                    break
        dt = time.time() - t0
        return got / 1024 / 1024 / max(dt, 0.01), None
    except Exception as e:
        reason = getattr(e, "reason", None)
        return None, (str(reason)[:60] if reason else type(e).__name__)

def main():
    nodes = json.load(open("nodes/verified_nodes.json", encoding="utf-8"))
    print(f"verified nodes: {len(nodes)}", flush=True)
    # 基线：直连（不走任何代理）
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    t0 = time.time()
    try:
        got = 0
        with op.open(SPEED_URL, timeout=TIME_LIMIT) as r:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                got += len(chunk)
                if time.time() - t0 > TIME_LIMIT:
                    break
        print(f"baseline direct: {got/1024/1024/max(time.time()-t0,0.01):.2f} MB/s", flush=True)
    except Exception as e:
        print(f"baseline direct: FAIL {type(e).__name__}", flush=True)

    results = []
    for i, n in enumerate(nodes, 1):
        name = n["test_name"]
        try:
            select_proxy(name)
        except Exception as e:
            results.append({"node": name, "speed_mbps": None, "speed_err": f"select: {type(e).__name__}"})
            print(f"[{i}/{len(nodes)}] {name[:40]} SELECT FAIL", flush=True)
            continue
        mbps, err = speed_via_proxy()
        if err:
            results.append({"node": name, "speed_mbps": None, "speed_err": err})
            print(f"[{i}/{len(nodes)}] {name[:40]} SPEED FAIL: {err}", flush=True)
        else:
            results.append({"node": name, "speed_mbps": round(mbps, 2), "speed_err": None})
            print(f"[{i}/{len(nodes)}] {name[:40]} {mbps:.2f} MB/s", flush=True)
        # 合并回节点
        n["speed_mbps"] = results[-1]["speed_mbps"]
        n["speed_err"] = results[-1]["speed_err"]
    # 排序
    nodes.sort(key=lambda x: (x.get("speed_mbps") is None, -(x.get("speed_mbps") or 0)))
    with open("nodes/final_nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=1)
    print("saved nodes/final_nodes.json", flush=True)

if __name__ == "__main__":
    main()
