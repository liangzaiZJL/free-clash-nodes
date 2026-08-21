# -*- coding: utf-8 -*-
"""下载 mihomo (Clash.Meta) 核心。用法: python get_mihomo.py [windows|linux]"""
import gzip, io, json, os, re, sys, urllib.request, zipfile

PLATFORMS = {
    "windows": {"tag": "windows-amd64-compatible", "ext": ".zip", "out": "mihomo.exe"},
    "linux":   {"tag": "linux-amd64-compatible", "ext": ".gz", "out": "mihomo"},
}

def get(url, tries=4, timeout=90):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print(f"  retry {i+1} {url}: {type(e).__name__}", flush=True)
            if i == tries - 1:
                raise
    return None

def main():
    platform = (sys.argv[1] if len(sys.argv) > 1 else "windows").lower()
    if platform not in PLATFORMS:
        print(f"unknown platform: {platform}; use windows|linux")
        sys.exit(1)
    info = PLATFORMS[platform]
    os.makedirs("bin", exist_ok=True)
    out_path = os.path.join("bin", info["out"])
    if os.path.exists(out_path):
        print(f"already exists: {out_path}, skip download")
        return

    # 通过 GitHub API 找最新 release 对应资产
    api = json.loads(get("https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"))
    tag = api["tag_name"]
    url = None
    for a in api["assets"]:
        if info["tag"] in a["name"] and a["name"].endswith(info["ext"]):
            url = a["browser_download_url"]
            break
    if not url:
        print("asset not found for", info["tag"])
        sys.exit(1)
    print(f"downloading {url}", flush=True)
    data = get(url)
    print(f"  {len(data)} bytes", flush=True)

    if info["ext"] == ".zip":
        zip_path = os.path.join("bin", "mihomo.zip")
        with open(zip_path, "wb") as f:
            f.write(data)
        with zipfile.ZipFile(zip_path) as z:
            for n in z.namelist():
                if n.endswith(".exe"):
                    with z.open(n) as src, open(out_path, "wb") as dst:
                        dst.write(src.read())
                    break
        os.remove(zip_path)
    else:
        raw = gzip.decompress(data)
        with open(out_path, "wb") as f:
            f.write(raw)
        os.chmod(out_path, 0o755)
    print(f"saved {out_path} ({platform})", flush=True)

if __name__ == "__main__":
    main()
