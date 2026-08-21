# -*- coding: utf-8 -*-
"""对首轮存活的节点做二次延迟验证，过滤抖动节点。"""
import io, json, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
API = "http://127.0.0.1:9098"
DELAY_URL = "http://www.gstatic.com/generate_204"
TIMEOUT_MS = 3500

def test_one(name):
    q = urllib.parse.quote(name, safe="")
    url = "{}/proxies/{}/delay?timeout={}&url={}".format(API, q, TIMEOUT_MS, urllib.parse.quote(DELAY_URL, safe=""))
    try:
        with urllib.request.urlopen(url, timeout=12) as r:
            d = json.loads(r.read().decode())
        return name, d.get("delay"), None
    except Exception as e:
        reason = getattr(e, "reason", None)
        return name, None, (str(reason)[:60] if reason else type(e).__name__)

def main():
    merged = json.load(open("nodes/merged_results.json", encoding="utf-8"))
    alive = [n for n in merged if n.get("delay_ms") is not None]
    print(f"first-round alive: {len(alive)}", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(test_one, n["test_name"]) for n in alive]
        for fut in as_completed(futs):
            name, delay, err = fut.result()
            results[name] = {"delay2_ms": delay, "err2": err}
    keep = []
    for n in alive:
        r = results.get(n["test_name"], {})
        n = dict(n)
        n["delay2_ms"] = r.get("delay2_ms")
        n["delay2_err"] = r.get("err2")
        if r.get("delay2_ms") is not None:
            keep.append(n)
    print(f"second-round alive: {len(keep)}", flush=True)
    keep.sort(key=lambda x: x["delay2_ms"])
    with open("nodes/verified_nodes.json", "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=1)
    print("saved nodes/verified_nodes.json", flush=True)
    for n in keep[:15]:
        print(f"  {n['delay2_ms']:5d}ms {n['type']:10s} {n['server']}:{n['port']}  <{n.get('_sub','?')}>", flush=True)

if __name__ == "__main__":
    main()
