# -*- coding: utf-8 -*-
"""等待 mihomo API 就绪（update.bat 与 CI 共用）。"""
import sys, time, urllib.request

API = "http://127.0.0.1:9098"

def main():
    for i in range(60):
        try:
            with urllib.request.urlopen(API + "/version", timeout=3) as r:
                print("mihomo ready:", r.read().decode()[:60], flush=True)
                return 0
        except Exception:
            time.sleep(1)
    print("mihomo did not become ready in 60s", flush=True)
    return 1

if __name__ == "__main__":
    sys.exit(main())
