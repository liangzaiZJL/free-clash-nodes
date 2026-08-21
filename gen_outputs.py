# -*- coding: utf-8 -*-
"""生成最终交付物：best-nodes.yaml（可导入配置）+ report.md（整理报告）。"""
import io, json, sys
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def yq(v):
    """YAML 双引号字符串。"""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v)
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'

def dump_proxy(p):
    """把规范化节点转成 mihomo proxy 行列表。"""
    typ = p["type"]
    lines = [f"    - name: {yq(p['name'])}", f"      type: {typ}",
             f"      server: {yq(p['server'])}", f"      port: {int(p['port'])}"]
    if typ == "vmess":
        if not p.get("uuid"):
            return None
        lines += [f"      uuid: {yq(p['uuid'])}", f"      alterId: {int(p.get('alterId') or 0)}",
                  f"      cipher: {yq(p.get('cipher') or 'auto')}"]
        if p.get("network"):
            lines.append(f"      network: {p['network']}")
        if p.get("tls"):
            lines.append("      tls: true")
        if p.get("servername"):
            lines.append(f"      servername: {yq(p['servername'])}")
        if p.get("client-fingerprint"):
            lines.append(f"      client-fingerprint: {yq(p['client-fingerprint'])}")
        ws = p.get("ws-opts") or {}
        if p.get("network") == "ws":
            path = ws.get("path") or "/"
            hdr = ws.get("headers") or {}
            host = hdr.get("Host") or hdr.get("HOST") or p.get("servername")
            if host:
                lines.append(f"      ws-opts: {{path: {yq(path)}, headers: {{Host: {yq(host)}}}}}")
            else:
                lines.append(f"      ws-opts: {{path: {yq(path)}}}")
        if p.get("skip-cert-verify"):
            lines.append("      skip-cert-verify: true")
    elif typ == "ss":
        if not p.get("password") or not p.get("cipher"):
            return None
        lines += [f"      cipher: {yq(p['cipher'])}", f"      password: {yq(p['password'])}"]
        if p.get("plugin"):
            po = p.get("plugin-opts") or {}
            mode = po.get("mode") or (p.get("mode") or "http")
            host = po.get("host") or p.get("host") or p["server"]
            if p.get("plugin") == "obfs" and mode in ("http", "tls"):
                lines.append("      plugin: obfs")
                lines.append(f"      plugin-opts: {{mode: {mode}, host: {yq(host)}}}")
    elif typ == "ssr":
        if not p.get("password") or not p.get("cipher") or not p.get("protocol") or not p.get("obfs"):
            return None
        lines += [f"      protocol: {p['protocol']}", f"      cipher: {yq(p['cipher'])}",
                  f"      obfs: {p['obfs']}", f"      password: {yq(p['password'])}"]
        if p.get("obfs-param"):
            lines.append(f"      obfs-param: {yq(p['obfs-param'])}")
        if p.get("protocol-param"):
            lines.append(f"      protocol-param: {yq(p['protocol-param'])}")
    elif typ == "trojan":
        if not p.get("password"):
            return None
        lines.append(f"      password: {yq(p['password'])}")
        if p.get("sni"):
            lines.append(f"      sni: {yq(p['sni'])}")
        if p.get("network") == "ws":
            ws = p.get("ws-opts") or {}
            lines.append("      network: ws")
            host = (ws.get("headers") or {}).get("Host") or p.get("sni") or p["server"]
            lines.append(f"      ws-opts: {{path: {yq(ws.get('path') or '/')}, headers: {{Host: {yq(host)}}}}}")
        if p.get("tls"):
            lines.append("      tls: true")
        if p.get("skip-cert-verify"):
            lines.append("      skip-cert-verify: true")
    elif typ == "vless":
        if not p.get("uuid"):
            return None
        lines.append(f"      uuid: {yq(p['uuid'])}")
        if p.get("network"):
            lines.append(f"      network: {p['network']}")
        if p.get("tls"):
            lines.append("      tls: true")
        if p.get("servername"):
            lines.append(f"      servername: {yq(p['servername'])}")
        if p.get("client-fingerprint"):
            lines.append(f"      client-fingerprint: {yq(p['client-fingerprint'])}")
        ro = p.get("reality-opts") or {}
        if p.get("tls") and p.get("servername") and ro.get("public-key"):
            lines.append(f"      reality-opts: {{public-key: {yq(ro['public-key'])}, short-id: {yq(ro.get('short-id') or '')}}}")
        elif p.get("reality-opts"):
            return None
        if p.get("network") == "ws":
            ws = p.get("ws-opts") or {}
            host = (ws.get("headers") or {}).get("Host") or p.get("servername") or p["server"]
            lines.append(f"      ws-opts: {{path: {yq(ws.get('path') or '/')}, headers: {{Host: {yq(host)}}}}}")
        if p.get("network") == "grpc":
            go = p.get("grpc-opts") or {}
            lines.append(f"      grpc-opts: {{grpc-service-name: {yq(go.get('grpc-service-name') or '')}}}")
        if p.get("skip-cert-verify"):
            lines.append("      skip-cert-verify: true")
    elif typ == "hysteria2":
        if not p.get("password"):
            return None
        lines.append(f"      password: {yq(p['password'])}")
        if p.get("sni"):
            lines.append(f"      sni: {yq(p['sni'])}")
        if p.get("skip-cert-verify"):
            lines.append("      skip-cert-verify: true")
    elif typ == "tuic":
        if not p.get("uuid") or not p.get("password"):
            return None
        lines += [f"      uuid: {yq(p['uuid'])}", f"      password: {yq(p['password'])}"]
        if p.get("sni"):
            lines.append(f"      sni: {yq(p['sni'])}")
        if p.get("congestion-controller"):
            lines.append(f"      congestion-controller: {p['congestion-controller']}")
        if p.get("skip-cert-verify"):
            lines.append("      skip-cert-verify: true")
    else:
        return None
    return lines

def build_clash_yaml(nodes):
    """生成含全部已验证节点的可导入 Clash 配置。"""
    lines = [
        "# ====================================================",
        "# 免费节点已验证配置 (2026-08-21 测试)",
        "# 测试: TCP连通 -> mihomo协议延迟x2 -> 8MB真实下载测速",
        "# 说明: 免费节点随时可能失效，请定期重新测试",
        "# ====================================================",
        "mixed-port: 7890",
        "allow-lan: false",
        "mode: rule",
        "log-level: info",
        "ipv6: false",
        "external-controller: 127.0.0.1:9090",
        "proxies:",
    ]
    used = {}
    fast_names = []
    for n in nodes:
        sp = n.get("speed_mbps")
        tag = "⚡" if (sp is not None and sp >= 0.10) else ""
        base = (n.get("name") or f"{n['type']}-{n['server']}")[:40]
        if base in used:
            used[base] += 1
            base = f"{base}#{used[base]}"
        else:
            used[base] = 1
        name = tag + base
        nn = dict(n)
        nn["name"] = name
        blk = dump_proxy(nn)
        if blk is None:
            continue
        sp_s = f"{sp:.2f}MB/s" if sp is not None else "n/a"
        lines.append(f"    # {n['type']} {n['server']}:{n['port']} 延迟{n['delay2_ms']}ms 速度{sp_s}")
        lines.append("\n".join(blk))
        if tag:
            fast_names.append(name)
    group_members = "    - " + "\n    - ".join(fast_names) if fast_names else ""
    lines += [
        "",
        "proxy-groups:",
        "  - name: 🚀 手动选择",
        "    type: select",
        "    proxies:",
        "      - ♻️ 自动选择",
        "      - DIRECT",
    ]
    if fast_names:
        lines += ["      - " + "\n      - ".join(fast_names)]
    lines += [
        "  - name: ♻️ 自动选择",
        "    type: url-test",
        "    url: http://www.gstatic.com/generate_204",
        "    interval: 300",
        "    tolerance: 100",
    ]
    if fast_names:
        lines += ["    proxies:"]
        lines += ["      - " + "\n      - ".join(fast_names)]
    lines += [
        "",
        "rules:",
        "  - MATCH,🚀 手动选择",
        "",
    ]
    return "\n".join(lines)

def main():
    import os as _os
    _os.makedirs("output", exist_ok=True)
    final = json.load(open("nodes/final_nodes.json", encoding="utf-8"))
    verified = [n for n in final if n.get("delay2_ms") is not None]
    summary = json.load(open("output/summary.json", encoding="utf-8"))
    manifest = json.load(open("subs_manifest.json", encoding="utf-8"))

    # 1) best-nodes.yaml
    yaml_text = build_clash_yaml(verified)
    with open("output/best-nodes.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_text)
    print(f"written output/best-nodes.yaml ({len(verified)} nodes)")

    # 2) report.md
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    lines = []
    A = lines.append
    A("# 免费 Clash 节点订阅收集与测试报告")
    A("")
    A(f"> 生成时间: {now} (UTC+8) | 测试环境: Windows 11 + Python 3.12 + mihomo v1.19.30")
    A("")
    A("## 一、总体结果")
    A("")
    A("| 阶段 | 节点数 | 说明 |")
    A("|---|---|---|")
    A(f"| 抓取解析 | **{summary['total_dedup_nodes']:,}** | 24 个订阅源去重后 |")
    A(f"| TCP 可达 | **{summary['tcp_ok']:,}** (31%) | 3s 内 TCP 建连成功 |")
    A(f"| 协议可用 | **{summary['protocol_alive']}** | 通过节点实际请求 HTTP 204 成功 |")
    A(f"| 二次验证 | **{summary['verified_alive']}** | 两次延迟测试均通过 |")
    A(f"| 测速成功 | **{summary['speed_ok']}** | 8MB 真实下载可完成 |")
    A("")
    A("> 结论：免费节点**整体可用率约 0.7%**（10,299 去重节点中 70 个协议可用）。"
      "大量节点 TCP 能连（多为 Cloudflare 前置）但后端已死。**推荐直接订阅高质量来源 + 定期自测**。")
    A("")
    A("## 二、订阅来源（GitHub）")
    A("")
    A("| 来源 | 抓取到的节点 | 协议可用 | 可用率 | 质量评价 |")
    A("|---|---|---|---|---|")
    fast_subs = []
    by_sub = summary["per_sub"]
    for sub in sorted(by_sub, key=lambda s: -by_sub[s]["alive"]):
        a, t = by_sub[sub]["alive"], by_sub[sub]["total"]
        rate = a * 100 // max(t, 1)
        note = "✅ 推荐" if rate >= 50 else ("⚠️ 一般" if a > 0 else "❌ 基本不可用")
        A(f"| {sub} | {t} | {a} | {rate}% | {note} |")
        if rate >= 50:
            fast_subs.append(sub)
    A("")
    A("**最推荐订阅（实测可用率最高）：**")
    A("")
    for s in fast_subs:
        A(f"- `{manifest[s]['urls'][0] if s in manifest else s}`")
    A("")
    A("## 三、协议类型可用率")
    A("")
    A("| 协议 | TCP可达 | 协议可用 | 可用率 |")
    A("|---|---|---|---|")
    for t in sorted(summary["per_type"], key=lambda x: -summary["per_type"][x]["alive"]):
        a, tot = summary["per_type"][t]["alive"], summary["per_type"][t]["total"]
        A(f"| {t} | {tot} | {a} | {a*100//max(tot,1)}% |")
    A("")
    A("> ss / hysteria2 存活率最高（40%+）；vmess / trojan / vless 多为 Cloudflare 前置的死节点。")
    A("")
    A("## 四、测速最快的节点（8MB 下载）")
    A("")
    A("| 速度 | 延迟 | 类型 | 服务器 | 来源 |")
    A("|---|---|---|---|---|")
    for n in sorted((x for x in verified if x.get("speed_mbps") is not None), key=lambda x: -x["speed_mbps"])[:12]:
        A(f"| {n['speed_mbps']:.2f} MB/s | {n['delay2_ms']}ms | {n['type']} | `{n['server']}:{n['port']}` | {n.get('_sub','?')} |")
    A("")
    A("## 五、延迟最低的节点")
    A("")
    A("| 延迟 | 速度 | 类型 | 服务器 | 来源 |")
    A("|---|---|---|---|---|")
    for n in sorted(verified, key=lambda x: x["delay2_ms"])[:12]:
        sp = f"{n['speed_mbps']:.2f} MB/s" if n.get("speed_mbps") is not None else "n/a"
        A(f"| {n['delay2_ms']}ms | {sp} | {n['type']} | `{n['server']}:{n['port']}` | {n.get('_sub','?')} |")
    A("")
    A("## 六、使用方法")
    A("")
    A("1. **导入配置**：将 `best-nodes.yaml` 导入 Clash Verge / Clash Meta / Mihomo（节点名带 ⚡ 为测速较快的）")
    A("2. **订阅更新**：把「二、订阅来源」中的推荐链接加进客户端的订阅列表，定期更新")
    A("3. **自行测速**：运行本项目脚本 `python test_tcp.py && python test_delay.py && python speed_test.py`")
    A("")
    A("## 七、测试方法")
    A("")
    A("1. **收集**：从 GitHub 知名免费节点仓库抓取订阅文件（Clash YAML / V2Ray base64）")
    A("2. **解析**：标准库实现 YAML 子集解析器 + URI 解析器（vmess/ss/ssr/vless/trojan/hy2/tuic），去重后 10,299 节点")
    A("3. **TCP 预筛**：400 线程并发 TCP 建连测试（3s 超时）")
    A("4. **协议延迟**：mihomo 加载全部节点，逐个真实请求 `http://www.gstatic.com/generate_204`，4s 超时")
    A("5. **真实测速**：经 mihomo mixed-port 下载 Cloudflare 8MB 测速文件，记录 MB/s")
    A("")
    A("## 八、免责声明")
    A("")
    A("- 免费节点**随时可能失效或变慢**，本报告数据仅为测试时刻的快照")
    A("- 节点来自第三方公开仓库，**不保证安全性**，请勿传输敏感信息，风险自负")
    A("- 请遵守当地法律法规，合法合规使用网络")
    A("")
    with open("output/report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written output/report.md")

if __name__ == "__main__":
    main()
