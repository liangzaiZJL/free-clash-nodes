# -*- coding: utf-8 -*-
"""下载精选的免费订阅源（clash yaml / v2ray base64），带硬超时与镜像回退。"""
import os, sys, time, urllib.request, socket, json, threading
from concurrent.futures import ThreadPoolExecutor

socket.setdefaulttimeout(30)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SUBS = {
    "free18-c.yaml":            ["https://raw.githubusercontent.com/free18/v2ray/main/c.yaml",
                                "https://cdn.jsdelivr.net/gh/free18/v2ray@main/c.yaml"],
    "anaer-clash.yaml":         ["https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
                                "https://cdn.jsdelivr.net/gh/anaer/Sub@main/clash.yaml"],
    "ermaozi-clash.yml":        ["https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml"],
    "clashfree-clash.yaml":     ["https://raw.githubusercontent.com/free-nodes/clashfree/main/clash.yaml",
                                "https://cdn.jsdelivr.net/gh/free-nodes/clashfree@main/clash.yaml"],
    "Ruk1ng001-clash.yaml":     ["https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml"],
    "mfuu-clash.yaml":          ["https://raw.githubusercontent.com/mfuu/v2ray/master/clash.yaml",
                                "https://cdn.jsdelivr.net/gh/mfuu/v2ray@master/clash.yaml"],
    "SSAggregator-merge.yml":   ["https://raw.githubusercontent.com/mahdibland/SSAggregator/master/sub/sub_merge_yaml.yml"],
    "go4sharing-sub.yaml":      ["https://raw.githubusercontent.com/go4sharing/sub/main/sub.yaml"],
    "NoMoreWalls-list.yml":     ["https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml"],
    "Barabama-clashmeta.txt":   ["https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/clashmeta.txt"],
    "airport-tested.yaml":      ["https://raw.githubusercontent.com/dongchengjie/airport/refs/heads/main/subs/merged/tested_within.yaml"],
    "BestClash-proxies.yaml":   ["https://raw.githubusercontent.com/PuddinCat/BestClash/main/proxies.yaml"],
    "proxypool-clash-meta.yaml":["https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta.yaml"],
    "ts-sf-clash":              ["https://raw.githubusercontent.com/ts-sf/fly/main/clash"],
    "a2470982985-clash.yaml":   ["https://raw.githubusercontent.com/a2470982985/getNode/main/clash.yaml"],
    "Au1rxx-clash-full.yaml":   ["https://github.com/Au1rxx/free-vpn-subscriptions/raw/main/output/clash.yaml"],
    "vxiaov-clash-provider.yaml":["https://raw.githubusercontent.com/vxiaov/free_proxies/main/clash/clash.provider.yaml"],
    "mfbpn-trial.yaml":         ["https://raw.githubusercontent.com/mfbpn/tg_mfbpn_sub/main/trial.yaml"],
    "NiceVPN-clash.yaml":       ["https://raw.githubusercontent.com/NiceVPN123/NiceVPN/main/Clash.yaml"],
    "free18-v.txt":             ["https://raw.githubusercontent.com/free18/v2ray/main/v.txt",
                                "https://cdn.jsdelivr.net/gh/free18/v2ray@main/v.txt"],
    "Pawdroid-Free-servers":    ["https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
                                "https://fastly.jsdelivr.net/gh/Pawdroid/Free-servers@main/sub"],
    "aiboboxx-v2rayfree-v2":    ["https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2"],
    "mfuu-v2ray":               ["https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray"],
    "V2RayAggregator-Eternity": ["https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity"],
    "ShadowsocksAggregator-Eternity.yml": ["https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.yml"],
    "ermaozi-v2ray.txt":        ["https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt"],
    "ts-sf-v2":                 ["https://raw.githubusercontent.com/ts-sf/fly/main/v2"],
    "a2470982985-v2ray.txt":    ["https://raw.githubusercontent.com/a2470982985/getNode/main/v2ray.txt"],
    "ripaojiedian-freenode-clash": ["https://raw.githubusercontent.com/ripaojiedian/freenode/main/clash"],
    "mermeroo-All_base64.txt":  ["https://raw.githubusercontent.com/mermeroo/V2RAY-CLASH-BASE64-Subscription.Links/main/SUB%20LINKS/All_base64.txt"],
}

def _fetch_one(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=35) as r:
        return r.read()

def fetch_with_fallback(name, urls):
    last_err = None
    for u in urls:
        try:
            return _fetch_one(u), None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
    return None, last_err

def worker(args):
    name, urls = args
    data, err = fetch_with_fallback(name, urls)
    if data is None:
        print(f"[FAIL] {name}: {err}", flush=True)
        return (name, None, err)
    print(f"[OK]   {name}: {len(data)} bytes", flush=True)
    return (name, data, None)

def main():
    os.makedirs("subs", exist_ok=True)
    manifest = {}
    for name, urls in SUBS.items():
        result_box = {}
        def run():
            result_box["res"] = worker((name, urls))
        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(timeout=60)
        if "res" not in result_box:
            print(f"[FAIL] {name}: HARD TIMEOUT", flush=True)
            manifest[name] = {"urls": urls, "status": "FAIL", "error": "hard timeout"}
            continue
        _name, data, err = result_box["res"]
        if data is None:
            manifest[name] = {"urls": urls, "status": "FAIL", "error": err}
            continue
        path = os.path.join("subs", name)
        with open(path, "wb") as f:
            f.write(data)
        manifest[name] = {"urls": urls, "status": "OK", "bytes": len(data)}
    with open("subs_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("saved subs_manifest.json", flush=True)

if __name__ == "__main__":
    main()
