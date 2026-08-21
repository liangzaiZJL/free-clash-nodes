# -*- coding: utf-8 -*-
"""等待 mihomo API 就绪；失败时打印 mihomo 日志尾部以便排查。"""
import glob, os, sys, time, urllib.request

API = "http://127.0.0.1:9098"

def tail_logs():
    patterns = ["mihomo/run.log", "mihomo/*.log", "mihomo/logs/*.log"]
    for pat in patterns:
        for f in sorted(glob.glob(pat)):
            print(f"----- tail of {f} -----", flush=True)
            try:
                lines = open(f, encoding="utf-8", errors="replace").read().splitlines()[-30:]
                print("\n".join(lines), flush=True)
            except Exception as e:
                print("(cannot read)", e, flush=True)

def main():
    for i in range(60):
        try:
            with urllib.request.urlopen(API + "/version", timeout=3) as r:
                print("mihomo ready:", r.read().decode()[:60], flush=True)
                return 0
        except Exception:
            time.sleep(1)
    print("mihomo did not become ready in 60s", flush=True)
    tail_logs()
    return 1

if __name__ == "__main__":
    sys.exit(main())
