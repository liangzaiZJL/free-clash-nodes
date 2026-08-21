# -*- coding: utf-8 -*-
"""重试失败的订阅源：加镜像、加尝试次数；并用 GitHub API 核查 404 仓库。"""
import os, json, time, urllib.request, socket, threading

socket.setdefaulttimeout(30)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

RETRY = {
    "free18-c.yaml": [
        "https://raw.githubusercontent.com/free18/v2ray/main/c.yaml",
        "https://cdn.jsdelivr.net/gh/free18/v2ray@main/c.yaml",
        "https://ghfast.top/https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
    ],
    "anaer-clash.yaml": [
        "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
        "https://cdn.jsdelivr.net/gh/anaer/Sub@main/clash.yaml",
        "https://ghfast.top/https://raw.githubusercontent.com/anaer/Sub/refs/heads/main/clash.yaml",
    ],
    "ermaozi-clash.yml": [
        "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
        "https://ghfast.top/https://raw.githubusercontent.com/ermaozi/get_subscribe/refs/heads/main/subscribe/clash.yml",
    ],
    "clashfree-clash.yaml": [
        "https://raw.githubusercontent.com/free-nodes/clashfree/main/clash.yaml",
        "https://cdn.jsdelivr.net/gh/free-nodes/clashfree@main/clash.yaml",
        "https://ghfast.top/https://raw.githubusercontent.com/free-nodes/clashfree/refs/heads/main/clash.yaml",
    ],
    "Ruk1ng001-clash.yaml": [
        "https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml",
        "https://ghfast.top/https://raw.githubusercontent.com/Ruk1ng001/freeSub/refs/heads/main/clash.yaml",
    ],
}

API_CHECKS = [
    ("proxypool", "https://api.github.com/repos/snakem982/proxypool/contents/source?ref=main"),
    ("aiboboxx",  "https://api.github.com/repos/aiboboxx/v2rayfree/contents?ref=main"),
    ("mermeroo",  "https://api.github.com/repos/mermeroo/V2RAY-CLASH-BASE64-Subscription.Links/contents/SUB%20LINKS?ref=main"),
]

def fetch_bytes(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=35) as r:
                return r.read()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(1.5)

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def main():
    # 1) 重试
    for name, urls in RETRY.items():
        box = {}
        def run():
            for u in urls:
                try:
                    data = fetch_bytes(u)
                    box["res"] = (u, data)
                    return
                except Exception:
                    continue
            box["res"] = (None, None)
        t = threading.Thread(target=run, daemon=True)
        t.start(); t.join(timeout=120)
        u, data = box.get("res", (None, None))
        if data:
            with open(os.path.join("subs", name), "wb") as f:
                f.write(data)
            print(f"[OK]   {name}: {len(data)} bytes via {u}", flush=True)
        else:
            print(f"[FAIL] {name}: all mirrors failed", flush=True)

    # 2) API 核查
    print("---- API checks ----", flush=True)
    for label, url in API_CHECKS:
        info = fetch_json(url)
        if "error" in info:
            print(f"[API] {label}: {info['error']}", flush=True)
            continue
        if isinstance(info, list):
            print(f"[API] {label}: {[it['name'] for it in info][:20]}", flush=True)
        else:
            print(f"[API] {label}: {info.get('message')}", flush=True)

if __name__ == "__main__":
    main()
