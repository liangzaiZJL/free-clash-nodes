# -*- coding: utf-8 -*-
"""汇总统计 + 生成最终报告数据与可导入的 Clash 配置。"""
import io, json, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def main():
    import os as _os
    _os.makedirs("output", exist_ok=True)
    final = json.load(open("nodes/final_nodes.json", encoding="utf-8"))
    merged = json.load(open("nodes/merged_results.json", encoding="utf-8"))
    manifest = json.load(open("subs_manifest.json", encoding="utf-8"))

    alive = [n for n in final if n.get("delay2_ms") is not None]
    with_speed = [n for n in alive if n.get("speed_mbps") is not None]
    print(f"verified(alive x2): {len(alive)}")
    print(f"speed measured ok : {len(with_speed)}")
    speeds = sorted((n["speed_mbps"] for n in with_speed), reverse=True)
    if speeds:
        import statistics
        print(f"speed: max={max(speeds):.2f} median={statistics.median(speeds):.2f} MB/s")
    print("\n== TOP 15 by speed ==")
    for n in sorted(with_speed, key=lambda x: -x["speed_mbps"])[:15]:
        print(f"  {n['speed_mbps']:.2f} MB/s  {n['delay2_ms']:5d}ms  {n['type']:10s} {n['server']}:{n['port']}  <{n.get('_sub','?')}>  {n.get('name','')[:30]}")

    print("\n== TOP 15 by delay ==")
    for n in sorted(alive, key=lambda x: x["delay2_ms"])[:15]:
        sp = f"{n['speed_mbps']:.2f}MB/s" if n.get("speed_mbps") is not None else "n/a"
        print(f"  {n['delay2_ms']:5d}ms  {sp:10s}  {n['type']:10s} {n['server']}:{n['port']}  <{n.get('_sub','?')}>  {n.get('name','')[:30]}")

    # 汇总：per sub
    print("\n== per-sub usable rate ==")
    by_sub = defaultdict(lambda: [0, 0])
    for n in merged:
        by_sub[n.get("_sub", "?")][1] += 1
        if n.get("delay_ms") is not None:
            by_sub[n["_sub"]][0] += 1
    total_nodes = len(json.load(open("nodes/dedup_nodes.json", encoding="utf-8")))
    total_alive = sum(v[0] for v in by_sub.values())
    print(f"  OVERALL: {total_alive}/{total_nodes} protocol-alive ({total_alive*100//max(total_nodes,1)}%)")
    for sub, (a, tot) in sorted(by_sub.items(), key=lambda x: -x[1][0]):
        print(f"  {a:4d}/{tot:5d} ({a*100//max(tot,1):3d}%)  {sub}")

    # 汇总：per type
    print("\n== per-type ==")
    by_type = defaultdict(lambda: [0, 0])
    for n in merged:
        by_type[n["type"]][1] += 1
        if n.get("delay_ms") is not None:
            by_type[n["type"]][0] += 1
    for t, (a, tot) in sorted(by_type.items(), key=lambda x: -x[1][0]):
        print(f"  {a:4d}/{tot:5d} ({a*100//max(tot,1):3d}%)  {t}")

    # 保存汇总 json
    summary = {
        "total_dedup_nodes": total_nodes,
        "tcp_ok": len(json.load(open("nodes/tcp_ok.json", encoding="utf-8"))),
        "protocol_alive": total_alive,
        "verified_alive": len(alive),
        "speed_ok": len(with_speed),
        "top_by_speed": [
            {"name": n.get("name", ""), "type": n["type"], "server": n["server"], "port": n["port"],
             "delay_ms": n["delay2_ms"], "speed_mbps": n["speed_mbps"], "sub": n.get("_sub", "")}
            for n in sorted(with_speed, key=lambda x: -x["speed_mbps"])[:20]
        ],
        "per_sub": {s: {"alive": a, "total": t} for s, (a, t) in by_sub.items()},
        "per_type": {t: {"alive": a, "total": t} for t, (a, t) in by_type.items()},
    }
    with open("output/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\nsaved output/summary.json")

if __name__ == "__main__":
    main()
