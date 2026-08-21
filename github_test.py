# -*- coding: utf-8 -*-
"""实测：已验证节点里，哪些真的能访问 github.com / raw.githubusercontent.com。"""
import io, json, os, subprocess, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
import gen_config

API = "http://127.0.0.1:9098"
URLS = {"gstatic": "http://www.gstatic.com/generate_204",
        "github": "https://github.com",
        "rawgithub": "https://raw.githubusercontent.com"}

def start_mihomo():
    verified = json.load(open("nodes/verified_nodes.json", encoding="utf-8"))
    used = {}
    blocks, names = [], []
    for n in verified:
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
    os.makedirs("mihomo", exist_ok=True)
    with open("mihomo/config.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(["mixed-port: 7898", "allow-lan: false", "mode: global",
                           "log-level: silent", "ipv6: false",
                           "external-controller: 127.0.0.1:9098", "proxies:",
                           "\n".join(blocks), ""]))
    subprocess.run(["taskkill", "/F", "/IM", "mihomo-windows-amd64-compatible.exe"],
                   capture_output=True) if os.name == "nt" else None
    time.sleep(1)
    subprocess.Popen(["bin/mihomo-windows-amd64-compatible.exe", "-d", "mihomo",
                      "-f", "mihomo/config.yaml"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        time.sleep(1)
        try:
            urllib.request.urlopen(API + "/version", timeout=3)
            return names
        except Exception:
            pass
    raise RuntimeError("mihomo failed to start")

def test_delay(name, url):
    q = urllib.parse.quote(name, safe="")
    u = "{}/proxies/{}/delay?timeout=5000&url={}".format(API, q, urllib.parse.quote(url, safe=""))
    try:
        with urllib.request.urlopen(u, timeout=15) as r:
            d = json.loads(r.read().decode())
        return d.get("delay")
    except Exception:
        return None

def main():
    names = start_mihomo()
    print(f"mihomo up, testing {len(names)} nodes x {len(URLS)} urls", flush=True)
    results = {name: {} for name in names}
    for label, url in URLS.items():
        with ThreadPoolExecutor(max_workers=12) as ex:
            futs = {ex.submit(test_delay, n, url): n for n in names}
            for fut in as_completed(futs):
                n = futs[fut]
                results[n][label] = fut.result()
        ok = sum(1 for r in results.values() if r.get(label) is not None)
        print(f"  {label}: {ok}/{len(names)} 可达", flush=True)

    # 汇总
    github_ok = [(n, r) for n, r in results.items() if r.get("github") is not None and r.get("rawgithub") is not None]
    github_only = [(n, r) for n, r in results.items() if r.get("github") is not None and r.get("rawgithub") is None]
    print(f"\ngithub+rawgithub 都通: {len(github_ok)}", flush=True)
    print(f"仅 github.com 通(raw被墙): {len(github_only)}", flush=True)
    for n, r in sorted(github_ok, key=lambda x: x[1]["github"])[:20]:
        print(f"  gh={r['github']:5d}ms raw={r['rawgithub']:5d}ms gstatic={r['gstatic']}ms  {n[:40]}", flush=True)
    with open("output/github_ok.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("saved output/github_ok.json", flush=True)

if __name__ == "__main__":
    main()
