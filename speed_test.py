# -*- coding: utf-8 -*-
"""通过 mihomo mixed-port 对延迟最低的 N 个节点做真实下载测速（默认前 15 个、4MB）。

可调环境变量:
  SPEED_TOP   测速节点数量（默认 15）
  SPEED_BYTES 下载字节数（默认 4194304 = 4MB）
"""
import io, json, os, sys, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
API = "http://127.0.0.1:9098"
MIXED = "http://127.0.0.1:7898"
TOP = int(os.environ.get("SPEED_TOP", "15"))
BYTES = int(os.environ.get("SPEED_BYTES", str(4 * 1024 * 1024)))
SPEED_URL = "http://speed.cloudflare.com/__down?bytes={}".format(BYTES)
TIME_LIMIT = 15  # 秒
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
    print(f"verified nodes: {len(nodes)}, will speed-test top {TOP} by delay", flush=True)

    # 基线：直连（不走任何代理）
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    t0 = time.time()
    try:
        got = 0
        with op.open(urllib.request.Request(SPEED_URL, headers=UA), timeout=TIME_LIMIT) as r:
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

    # 按延迟升序取前 N 个测速
    order = sorted(nodes, key=lambda x: (x.get("delay2_ms") is None, x.get("delay2_ms") or 99999))
    to_test = order[:TOP]
    total = len(to_test)
    for i, n in enumerate(to_test, 1):
        name = n["test_name"]
        try:
            select_proxy(name)
        except Exception as e:
            n["speed_mbps"] = None
            n["speed_err"] = f"select: {type(e).__name__}"
            print(f"[{i}/{total}] {name[:40]} SELECT FAIL", flush=True)
            continue
        mbps, err = speed_via_proxy()
        n["speed_mbps"] = round(mbps, 2) if mbps is not None else None
        n["speed_err"] = err
        if err:
            print(f"[{i}/{total}] {name[:40]} SPEED FAIL: {err}", flush=True)
        else:
            print(f"[{i}/{total}] {name[:40]} {mbps:.2f} MB/s", flush=True)

    # 按速度排序（未测速的排后面，保留全部节点）
    nodes.sort(key=lambda x: (x.get("speed_mbps") is None, -(x.get("speed_mbps") or 0)))
    with open("nodes/final_nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=1)
    print("saved nodes/final_nodes.json", flush=True)

if __name__ == "__main__":
    main()
