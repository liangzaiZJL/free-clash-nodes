# -*- coding: utf-8 -*-
"""新途径抓取：Telegram 频道预览页 + 节点分享站 + 聚合仓库二级展开。

途径：
  A. t.me/s/<频道> 公开预览页（无需 token），提取消息中的订阅链接与内联节点
  B. nodefree.org 等分享站 HTML 里的 base64 订阅块
  C. 聚合仓库（sinspired/airport 等）里的 sub 链接列表，逐个下载
"""
import base64, io, json, os, re, sys, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

TG_CHANNELS = ["nodefree", "v2rayshare", "freefq", "freenodes", "maobuzhi", "mianfeijiedian", "sanfenjian", "free_airport"]
SITES = ["https://nodefree.org/", "https://clashnode.org/", "https://nodefree.top/"]
AGGREGATOR_SUBS = [
    "https://raw.githubusercontent.com/sinspired/airport/main/subs/_pool.yaml",
    "https://raw.githubusercontent.com/sinspired/airport/main/subs/_previous.yaml",
]

def fetch(url, tries=5, timeout=25):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=H)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), r.status
        except Exception as e:
            if i == tries - 1:
                return None, f"{type(e).__name__}: {str(getattr(e, 'reason', e))[:60]}"
            time.sleep(1.5 + i)

def save(name, data, ext="txt"):
    os.makedirs("subs", exist_ok=True)
    path = os.path.join("subs", f"extra-{name}.{ext}")
    with open(path, "wb") as f:
        f.write(data)
    print(f"[SAVED] {path} ({len(data)}B)", flush=True)
    return path

def extract_tg_messages(html):
    """提取 TG 预览页每条消息的纯文本。"""
    msgs = re.findall(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.S)
    out = []
    for m in msgs:
        clean = re.sub(r"<br\s*/?>", "\n", m)
        clean = re.sub(r"<[^>]+>", "", clean)
        out.append(clean.strip())
    return out

def main():
    manifest = {}
    # ---- A. TG 频道 ----
    for ch in TG_CHANNELS:
        data, st = fetch(f"https://t.me/s/{ch}")
        if data is None:
            print(f"[FAIL] tg/{ch}: {st}", flush=True)
            continue
        html = data.decode("utf-8", "replace")
        texts = extract_tg_messages(html)
        # 1) 消息内订阅链接
        links = []
        for t in texts:
            links += re.findall(r"https?://[^\s\"'<>\)\]]+", t)
        sub_links = [l for l in links if any(k in l for k in
                     (".yaml", ".yml", ".txt", "/sub", "raw.githubusercontent", "jsdelivr", "ghproxy", "ghfast"))]
        # 2) 消息内联 URI 节点（vmess:// 等）直接保存
        uri_lines = [ln.strip() for t in texts for ln in t.splitlines()
                     if "://" in ln and any(p in ln for p in ("vmess://", "ss://", "vless://", "trojan://", "hysteria2://", "hy2://", "ssr://", "tuic://"))]
        n_uri = len(uri_lines)
        if uri_lines:
            save(f"tg-{ch}", ("\n".join(uri_lines)).encode("utf-8"))
        if sub_links:
            save(f"tg-{ch}-links", ("\n".join(sub_links)).encode("utf-8"))
        manifest[f"tg/{ch}"] = {"msgs": len(texts), "sub_links": len(sub_links), "inline_uris": n_uri}
        print(f"[OK] tg/{ch}: {len(texts)} msgs, {len(sub_links)} sub links, {n_uri} inline URIs", flush=True)

    # ---- B. 分享站 ----
    for url in SITES:
        data, st = fetch(url)
        if data is None:
            print(f"[FAIL] site {url}: {st}", flush=True)
            continue
        html = data.decode("utf-8", "replace")
        # base64 大块（订阅文本）
        blocks = re.findall(r"[A-Za-z0-9+/]{400,}={0,2}", html)
        ok_b64 = 0
        for i, b in enumerate(blocks[:20]):
            try:
                dec = base64.b64decode(b).decode("utf-8", "replace")
                if "://" in dec:
                    save(f"site-{re.sub(r'[^a-z0-9]', '', url.split('//')[1].split('/')[0])}-{i}", dec.encode("utf-8"))
                    ok_b64 += 1
            except Exception:
                pass
        # 页面内订阅链接
        links = list(set(re.findall(r"https?://[^\s\"'<>\)\]]+", html)))
        sub_links = [l for l in links if any(k in l for k in (".yaml", ".txt", "sub", "raw.githubusercontent", "jsdelivr"))]
        if sub_links:
            save(f"site-{re.sub(r'[^a-z0-9]', '', url.split('//')[1].split('/')[0])}-links", ("\n".join(sub_links)).encode("utf-8"))
        manifest[url] = {"b64_blocks": ok_b64, "sub_links": len(sub_links)}
        print(f"[OK] site {url}: {ok_b64} b64 subs, {len(sub_links)} links", flush=True)

    # ---- B2. 分享站文章页（nodefree 为博客站，节点在文章内） ----
    for url in SITES:
        data, st = fetch(url)
        if data is None:
            continue
        html = data.decode("utf-8", "replace")
        domain = url.split("//")[1].split("/")[0]
        # 找文章链接
        arts = []
        for m in re.finditer(r'href="(https?://[^"]+)"', html):
            href = m.group(1)
            if domain in href and any(k in href for k in ("/p/", "/post", "/article", "/archives", "/node", "/free")):
                arts.append(href)
        arts = list(dict.fromkeys(arts))[:15]
        got = 0
        for a in arts:
            d2, st2 = fetch(a)
            if d2 is None:
                continue
            h2 = d2.decode("utf-8", "replace")
            blocks = re.findall(r"[A-Za-z0-9+/]{400,}={0,2}", h2)
            for i, b in enumerate(blocks[:10]):
                try:
                    dec = base64.b64decode(b).decode("utf-8", "replace")
                    if "://" in dec:
                        slug = re.sub(r"[^a-z0-9]", "", a.split("//")[1])[-40:]
                        save(f"site-{re.sub(r'[^a-z0-9]', '', domain)}-{slug}-{i}", dec.encode("utf-8"))
                        got += 1
                except Exception:
                    pass
            # 文章内 URI 行
            uri_lines = [ln.strip() for ln in h2.splitlines()
                         if "://" in ln and any(p in ln for p in ("vmess://", "ss://", "vless://", "trojan://", "hysteria2://"))]
            if uri_lines:
                slug = re.sub(r"[^a-z0-9]", "", a.split("//")[1])[-40:]
                save(f"site-{re.sub(r'[^a-z0-9]', '', domain)}-{slug}", ("\n".join(uri_lines)).encode("utf-8"))
                got += 1
        print(f"[OK] site articles {url}: {len(arts)} articles, {got} subs extracted", flush=True)
        manifest[url + "#articles"] = {"articles": len(arts), "subs": got}

    # ---- C. 聚合仓库二级展开 ----
    for url in AGGREGATOR_SUBS:
        data, st = fetch(url)
        if data is None:
            print(f"[FAIL] agg {url}: {st}", flush=True)
            continue
        text = data.decode("utf-8", "replace")
        # 保存池文件本身（这是精选合并后的节点池，价值最高）
        fname = re.sub(r"[^a-z0-9]", "-", url.split("/subs/")[-1]) or "pool"
        save(f"agg-pool-{fname}", data, ext="yaml")
        links = list(set(re.findall(r"https?://[^\s\"'<>\)\]]+", text)))
        sub_links = [l for l in links if any(k in l for k in (".yaml", ".txt", "/sub", "raw.githubusercontent", "jsdelivr"))]
        manifest[url] = {"children": len(sub_links)}
        print(f"[OK] agg {url}: saved pool + {len(sub_links)} child subs", flush=True)
        for j, l in enumerate(sub_links[:30]):
            d, st2 = fetch(l)
            if d is None:
                continue
            name = f"agg-{j}"
            save(name, d)
        manifest[url]["downloaded"] = j + 1 if sub_links else 0

    with open("extra_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("saved extra_manifest.json", flush=True)

if __name__ == "__main__":
    main()
