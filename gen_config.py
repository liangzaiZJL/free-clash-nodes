# -*- coding: utf-8 -*-
"""把 TCP 通过的节点转为 mihomo 配置（标准库 YAML 输出）。"""
import io, json, sys

yq = None  # 占位，实际在下方定义

def _yq(v):
    """YAML 双引号字符串。"""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v)
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{s}"'

yq = _yq

def dump_proxy(p):
    """把规范化节点转成 mihomo proxy 行列表。返回 None 表示字段缺失需丢弃。"""
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
        if p.get("alpn"):
            lines.append(f"      alpn: {json.dumps(p['alpn'])}")
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
            # 其他插件（gost/v2ray-plugin 等）mihomo 不支持 → 按普通 ss 测试
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
            lines.append(f"      network: ws")
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
            # reality 标记但缺公钥 → 无法使用
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

def main():
    import os as _os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    _os.makedirs("mihomo", exist_ok=True)
    nodes = json.load(open("nodes/tcp_ok.json", encoding="utf-8"))
    print(f"tcp_ok nodes: {len(nodes)}", flush=True)
    used = {}
    proxy_blocks = []
    kept = 0
    for n in nodes:
        lines = dump_proxy(n)
        if lines is None:
            continue
        base = (n.get("name") or f"{n['type']}-{n['server']}")[:60]
        if base in used:
            used[base] += 1
            base = f"{base}#{used[base]}"
        else:
            used[base] = 1
        # 把唯一名替换进 name 行
        lines[0] = f"    - name: {yq(base)}"
        proxy_blocks.append("\n".join(lines))
        kept += 1
    print(f"kept for mihomo: {kept}", flush=True)
    cfg = [
        "mixed-port: 7898",
        "allow-lan: false",
        "mode: global",
        "log-level: silent",
        "ipv6: false",
        "external-controller: 127.0.0.1:9098",
        "proxies:",
        "\n".join(proxy_blocks),
        "",
    ]
    with open("mihomo/config.yaml", "w", encoding="utf-8") as f:
        f.write("\n".join(cfg))
    print("written mihomo/config.yaml", flush=True)

if __name__ == "__main__":
    main()
