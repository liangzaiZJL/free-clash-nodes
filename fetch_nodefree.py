# -*- coding: utf-8 -*-
"""抓取 nodefree.me 文章页里的节点订阅（base64 块 / 内联 URI）。"""
import base64, io, os, re, sys, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(url, tries=5, timeout=25):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=H)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.5)

def save(name, text):
    os.makedirs("subs", exist_ok=True)
    p = os.path.join("subs", f"extra-{name}.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[SAVED] {p} ({len(text)}B)", flush=True)

def extract(text):
    """从文章 HTML 提取节点订阅文本。"""
    out = []
    # base64 大块
    for b in re.findall(r"[A-Za-z0-9+/]{400,}={0,2}", text):
        try:
            dec = base64.b64decode(b).decode("utf-8", "replace")
            if "://" in dec:
                out.append(dec)
        except Exception:
            pass
    # 内联 URI 行
    uri_lines = [ln.strip() for ln in text.splitlines()
                 if "://" in ln and any(p in ln for p in
                 ("vmess://", "ss://", "vless://", "trojan://", "hysteria2://", "hy2://", "ssr://"))]
    if uri_lines:
        out.append("\n".join(uri_lines))
    return out

def main():
    home = get("https://nodefree.me/")
    if not home:
        print("homepage fail", flush=True)
        return
    arts = list(dict.fromkeys(re.findall(r'href="(https?://nodefree\.me/p/\d+\.html)"', home)))
    print(f"articles found: {len(arts)}", flush=True)
    got = 0
    for a in arts[:10]:
        h = get(a)
        if not h:
            continue
        subs = extract(h)
        nid = re.search(r"/p/(\d+)", a).group(1)
        for i, s in enumerate(subs):
            save(f"nodefree-p{nid}-{i}", s)
            got += 1
        print(f"  {a}: {len(subs)} subs", flush=True)
        time.sleep(0.3)
    print(f"total saved: {got}", flush=True)

if __name__ == "__main__":
    main()
