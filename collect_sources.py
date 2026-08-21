# -*- coding: utf-8 -*-
"""从 GitHub 仓库收集免费 Clash/V2Ray 订阅链接。"""
import json, re, sys, time, urllib.request, socket, threading

socket.setdefaulttimeout(20)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

REPOS = [
    "jichangx/free-nodes",
    "flik6/Free-Node",
    "Au1rxx/free-vpn-subscriptions",
    "pannaconda/FreeNodes-autoUp",
    "xiaoji235/airport-free",
    "lza6/free-VPN",
    "free18/v2ray",
]

def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                return None
            time.sleep(2)
    return None

def candidates(repo):
    """返回可能的 raw 文件路径列表。"""
    base = f"https://raw.githubusercontent.com/{repo}/main/"
    files = ["README.md", "readme.md", "Readme.md",
             "sub.txt", "clash.yaml", "nodes.txt", "sub", "clash.yml",
             "config.yaml", "subscription.txt", "url.txt", "links.txt"]
    return [base + f for f in files]

def main():
    out = {}
    boxes = []
    def run_repo(repo, box):
        got = False
        for url in candidates(repo):
            text = fetch(url)
            if not text:
                continue
            got = True
            urls = set(re.findall(r'https?://[^\s"\'<>\)\]\}]+', text))
            box["res"] = (repo, url, sorted(urls), len(text))
            return
        box["res"] = (repo, None, None, 0)
    for repo in REPOS:
        box = {}
        t = threading.Thread(target=run_repo, args=(repo, box), daemon=True)
        t.start()
        boxes.append((repo, t, box))
    for repo, t, box in boxes:
        t.join(timeout=90)
        repo2, url, urls, text_len = box.get("res", (repo, None, None, 0))
        if url is None:
            print(f"[{repo}] FAILED", flush=True)
            continue
        out[repo] = {"source": url, "urls": urls, "text_len": text_len}
        print(f"[{repo}] OK {url} ({text_len}B, {len(urls)} urls)", flush=True)
    with open("sources_raw.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved sources_raw.json", flush=True)

if __name__ == "__main__":
    main()
