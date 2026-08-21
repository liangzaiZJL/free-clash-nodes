# -*- coding: utf-8 -*-
"""对 extra-* 新源节点做 TCP 预筛 + mihomo 延迟测试，验证新途径质量。"""
import io, json, os, socket, subprocess, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.makedirs("mihomo", exist_ok=True)
API = "http://127.0.0.1:9098"
DELAY_URL = "http://www.gstatic.com/generate_204"

# ---------- 1. TCP 预筛 ----------
def tcp_test(node):
    host, port = node["server"], int(node.get("port") or 0)
    if not host or not (1 <= port <= 65535):
        return node, False, None
    import time as _t
    t0 = _t.time()
    try:
        s = socket.create_connection((host, port), timeout=3)
        s.close()
        return node, True, round((_t.time() - t0) * 1000, 1)
    except Exception:
        return node, False, None

def tcp_filter(nodes):
    ok = []
    with ThreadPoolExecutor(max_workers=400) as ex:
        futs = [ex.submit(tcp_test, n) for n in nodes]
        for fut in as_completed(futs):
            n, okk, ms = fut.result()
            if okk:
                n = dict(n)
                n["tcp_ms"] = ms
                ok.append(n)
    return ok

# ---------- 2. mihomo ----------
def start_mihomo(config_text):
    with open("mihomo/config.yaml", "w", encoding="utf-8") as f:
        f.write(config_text)
    subprocess.run(["taskkill", "/F", "/IM", "mihomo-windows-amd64-compatible.exe"],
                   capture_output=True) if os.name == "nt" else None
    time.sleep(1)
    subprocess.Popen(["bin/mihomo-windows-amd64-compatible.exe", "-d", "mihomo", "-f", "mihomo/config.yaml"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        time.sleep(1)
        try:
            urllib.request.urlopen(API + "/version", timeout=3)
            return True
        except Exception:
            pass
    return False

def delay_test(name):
    q = urllib.parse.quote(name, safe="")
    url = "{}/proxies/{}/delay?timeout=4000&url={}".format(API, q, urllib.parse.quote(DELAY_URL, safe=""))
    try:
        with urllib.request.urlopen(url, timeout=12) as r:
            d = json.loads(r.read().decode())
        return name, d.get("delay"), None
    except Exception as e:
        return name, None, type(e).__name__

def main():
    all_nodes = json.load(open("nodes/all_nodes.json", encoding="utf-8"))
    extra = [n for n in all_nodes if n.get("_sub", "").startswith("extra-")]
    # 按文件统计
    from collections import Counter
    cnt = Counter(n["_sub"] for n in extra)
    print("extra sources parsed:", dict(cnt), flush=True)
    print(f"extra nodes total: {len(extra)}", flush=True)

    tcp_ok = tcp_filter(extra)
    print(f"extra TCP ok: {len(tcp_ok)}/{len(extra)}", flush=True)

    if not tcp_ok:
        print("no tcp-ok extra nodes", flush=True)
        return

    # 生成 mihomo 配置（复用 gen_config 的 dump）
    sys.path.insert(0, ".")
    import gen_config
    used = {}
    blocks = []
    names = []
    for n in tcp_ok:
        lines = gen_config.dump_proxy(dict(n))
        if lines is None:
            continue
        base = (n.get("name") or f"{n['type']}-{n['server']}")[:60]
        if base in used:
            used[base] += 1
            base = f"{base}#{used[base]}"
        else:
            used[base] = 1
        lines[0] = f"    - name: {gen_config.yq(base)}"
        blocks.append("\n".join(lines))
        names.append(base)
    cfg = ["mixed-port: 7898", "allow-lan: false", "mode: global", "log-level: silent",
           "ipv6: false", "external-controller: 127.0.0.1:9098", "proxies:",
           "\n".join(blocks), ""]
    if not start_mihomo("\n".join(cfg)):
        print("mihomo failed to start", flush=True)
        return
    print(f"mihomo up, testing {len(names)} proxies...", flush=True)

    results = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(delay_test, n) for n in names]
        for fut in as_completed(futs):
            name, delay, err = fut.result()
            results[name] = {"delay_ms": delay, "err": err}
    alive = [(n, r) for n, r in results.items() if r["delay_ms"] is not None]
    print(f"extra protocol-alive: {len(alive)}/{len(results)}", flush=True)
    for n, r in sorted(alive, key=lambda x: x[1]["delay_ms"])[:20]:
        print(f"  {r['delay_ms']:5d}ms  {n[:45]}", flush=True)

    with open("output/extra_results.json", "w", encoding="utf-8") as f:
        json.dump({"tcp_ok": len(tcp_ok), "tested": len(results), "alive": len(alive),
                   "alive_list": [{"name": n, "delay": r["delay_ms"]} for n, r in alive]},
                  f, ensure_ascii=False, indent=2)
    print("saved output/extra_results.json", flush=True)

if __name__ == "__main__":
    main()
