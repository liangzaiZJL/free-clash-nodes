# -*- coding: utf-8 -*-
"""GitHub 可达性测试：验证每个节点能否访问 github.com 与 raw.githubusercontent.com。

依赖：mihomo 正在运行（update.bat 里放在 verify_nodes.py 之后、speed_test.py 之前）。
结果写入 nodes/verified_nodes.json（github_ms / raw_ms 字段），供 gen_outputs 生成 GitHub 分组。
"""
import io, json, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
API = "http://127.0.0.1:9098"
URLS = {"github_ms": "https://github.com",
        "raw_ms": "https://raw.githubusercontent.com"}

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
    verified = json.load(open("nodes/verified_nodes.json", encoding="utf-8"))
    names = [n["test_name"] for n in verified]
    for label, url in URLS.items():
        by_name = {}
        with ThreadPoolExecutor(max_workers=12) as ex:
            futs = {ex.submit(test_delay, n, url): n for n in names}
            for fut in as_completed(futs):
                n = futs[fut]
                by_name[n] = fut.result()
        for n in verified:
            n[label] = by_name.get(n["test_name"])
    ok = sum(1 for n in verified if n.get("github_ms") is not None and n.get("raw_ms") is not None)
    only_gh = sum(1 for n in verified if n.get("github_ms") is not None and n.get("raw_ms") is None)
    print(f"github+raw 都通: {ok}/{len(verified)} | 仅 github.com 通: {only_gh}", flush=True)
    with open("nodes/verified_nodes.json", "w", encoding="utf-8") as f:
        json.dump(verified, f, ensure_ascii=False, indent=1)
    print("saved nodes/verified_nodes.json (含 github_ms/raw_ms)", flush=True)

if __name__ == "__main__":
    main()
