# -*- coding: utf-8 -*-
"""生成最终交付物：best-nodes.yaml（可导入配置，节点按国家命名）+ report.md。"""
import io, json, re, socket, sys, threading, urllib.request
from datetime import datetime, timezone, timedelta

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

# ---------------- 国家识别 ----------------
FLAG_CODES = {
    "US": "美国", "HK": "香港", "TW": "台湾", "JP": "日本", "KR": "韩国",
    "SG": "新加坡", "DE": "德国", "FR": "法国", "GB": "英国", "CA": "加拿大",
    "AU": "澳大利亚", "RU": "俄罗斯", "NL": "荷兰", "IN": "印度", "ID": "印尼",
    "TH": "泰国", "MY": "马来西亚", "VN": "越南", "IT": "意大利", "ES": "西班牙",
    "TR": "土耳其", "BR": "巴西", "AE": "阿联酋", "CH": "瑞士", "SE": "瑞典",
    "NO": "挪威", "FI": "芬兰", "DK": "丹麦", "PL": "波兰", "CZ": "捷克",
    "UA": "乌克兰", "PH": "菲律宾", "IR": "伊朗", "CN": "中国", "MO": "澳门",
    "NZ": "新西兰", "ZA": "南非", "AR": "阿根廷", "MX": "墨西哥", "BE": "比利时",
    "AT": "奥地利", "PT": "葡萄牙", "GR": "希腊", "IL": "以色列", "EE": "爱沙尼亚",
    "LV": "拉脱维亚", "LT": "立陶宛", "RO": "罗马尼亚", "BG": "保加利亚", "HU": "匈牙利",
    "KZ": "哈萨克斯坦", "AZ": "阿塞拜疆", "GE": "格鲁吉亚", "IS": "冰岛", "IE": "爱尔兰",
    "LU": "卢森堡", "HR": "克罗地亚", "RS": "塞尔维亚", "SI": "斯洛文尼亚", "SK": "斯洛伐克",
    "CO": "哥伦比亚", "EG": "埃及", "SA": "沙特", "PK": "巴基斯坦", "BD": "孟加拉",
    "NG": "尼日利亚", "IQ": "伊拉克", "QA": "卡塔尔", "KW": "科威特", "OM": "阿曼",
    "CL": "智利", "PE": "秘鲁", "UY": "乌拉圭", "EC": "厄瓜多尔", "CR": "哥斯达黎加",
    "PA": "巴拿马", "DO": "多米尼加", "GT": "危地马拉", "BO": "玻利维亚", "PY": "巴拉圭",
    "VE": "委内瑞拉", "CU": "古巴", "SY": "叙利亚", "LB": "黎巴嫩", "JO": "约旦",
    "YE": "也门", "MN": "蒙古", "NP": "尼泊尔", "LK": "斯里兰卡", "MM": "缅甸",
    "KH": "柬埔寨", "LA": "老挝", "BN": "文莱", "TL": "东帝汶", "FJ": "斐济",
    "CY": "塞浦路斯", "MT": "马耳他", "MD": "摩尔多瓦", "BY": "白俄罗斯", "AM": "亚美尼亚",
    "KE": "肯尼亚", "ET": "埃塞俄比亚", "GH": "加纳", "MA": "摩洛哥", "TN": "突尼斯",
    "DZ": "阿尔及利亚", "UZ": "乌兹别克斯坦", "TJ": "塔吉克斯坦", "KG": "吉尔吉斯斯坦", "TM": "土库曼斯坦",
}
KEYWORD_RULES = [
    ("美国", ["美国", "美利坚", "united states", "unitedstates", "usa", "us", "洛杉矶", "纽约", "硅谷", "圣何塞", "西雅图", "芝加哥"]),
    ("香港", ["香港", "hong kong", "hongkong", "hk"]),
    ("台湾", ["台湾", "taiwan", "tw"]),
    ("日本", ["日本", "japan", "jp", "东京", "大阪", "softbank"]),
    ("韩国", ["韩国", "korea", "kr", "首尔"]),
    ("新加坡", ["新加坡", "singapore", "sg"]),
    ("德国", ["德国", "germany", "de", "法兰克福", "frankfurt"]),
    ("英国", ["英国", "england", "united kingdom", "uk", "伦敦", "london"]),
    ("法国", ["法国", "france", "fr", "巴黎", "paris"]),
    ("加拿大", ["加拿大", "canada", "ca", "多伦多", "温哥华"]),
    ("澳大利亚", ["澳大利亚", "australia", "au", "悉尼", "sydney"]),
    ("俄罗斯", ["俄罗斯", "russia", "ru", "莫斯科"]),
    ("荷兰", ["荷兰", "netherlands", "nl"]),
    ("印度", ["印度", "india", "in"]),
    ("印尼", ["印尼", "indonesia", "id"]),
    ("泰国", ["泰国", "thailand", "th"]),
    ("马来西亚", ["马来西亚", "malaysia", "my"]),
    ("越南", ["越南", "vietnam", "vn"]),
    ("意大利", ["意大利", "italy", "it"]),
    ("西班牙", ["西班牙", "spain", "es"]),
    ("土耳其", ["土耳其", "turkey", "tr"]),
    ("巴西", ["巴西", "brazil", "br"]),
    ("中国", ["中国", "china", "cn", "国内", "上海", "广州", "北京"]),
    ("澳门", ["澳门", "macau", "mo"]),
    ("菲律宾", ["菲律宾", "philippines", "ph"]),
    ("伊朗", ["伊朗", "iran", "ir"]),
]

def decode_escapes(name):
    """解码名字里的字面 \\U0001Fxxx / \\uXXXX 转义序列（还原 emoji 国旗）。"""
    if "\\U" in name or "\\u" in name:
        try:
            return name.encode("utf-8").decode("unicode_escape", errors="replace")
        except Exception:
            return name
    return name

def flag_to_country(name):
    cps = [ord(ch) for ch in name]
    for i in range(len(cps) - 1):
        if 0x1F1E6 <= cps[i] <= 0x1F1FF and 0x1F1E6 <= cps[i + 1] <= 0x1F1FF:
            a = chr(cps[i] - 0x1F1E6 + ord("A"))
            b = chr(cps[i + 1] - 0x1F1E6 + ord("A"))
            cc = a + b
            return FLAG_CODES.get(cc, cc)
    return None

def country_from_text(text):
    if not text:
        return None
    low = text.lower()
    for country, kws in KEYWORD_RULES:
        for kw in kws:
            if len(kw) <= 3 and kw.isalpha():
                # 短代码（us/uk/jp...）要求词边界，避免 "Ruk1ng001" 里的 "uk" 误匹配
                if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", low):
                    return country
            elif kw in low:
                return country
    return None

def detect_country(node):
    """国旗 emoji -> 关键词 -> IP 地理位置（由调用方做 IP 批量查询）。"""
    name = decode_escapes(node.get("name", ""))
    server = node.get("server", "")
    c = flag_to_country(name)
    if c:
        return c
    c = country_from_text(name + " " + server)
    if c:
        return c
    return None

def ip_countries(ip_list):
    """批量查询 IP 归属国（ip-api.com 免费批量接口；失败返回空 dict）。"""
    if not ip_list:
        return {}
    result = {}
    try:
        req = urllib.request.Request(
            "http://ip-api.com/batch",
            data=json.dumps([{"query": ip} for ip in ip_list]).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read().decode())
        for item in data:
            if item.get("status") == "success" and item.get("query"):
                cc = item.get("countryCode", "")
                if cc:
                    result[item["query"]] = FLAG_CODES.get(cc, cc)
    except Exception:
        pass
    return result

def resolve_ip(host):
    """线程内解析域名（3 秒超时），失败返回 None。"""
    box = {}

    def run():
        try:
            box["ip"] = socket.gethostbyname(host)
        except Exception:
            box["ip"] = None
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout=3)
    return box.get("ip")

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

def assign_countries(nodes):
    """给节点赋 country（可缓存复用）。返回 {index: 国家}。"""
    import os as _os
    cache = {}
    if _os.path.exists("nodes/country_cache.json"):
        try:
            with open("nodes/country_cache.json", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass
    result = {}
    pending = []
    for i, n in enumerate(nodes):
        c = detect_country(n)
        if c:
            result[i] = c
            continue
        server = n.get("server", "")
        if server in cache:
            result[i] = cache[server] or "未知"
            continue
        pending.append((i, n, server))
    # 批量 IP 查询
    ip_map = {}
    for i, n, server in pending:
        ip = server if IP_RE.match(server or "") else resolve_ip(server)
        if ip:
            ip_map.setdefault(ip, []).append((i, server))
    if ip_map:
        lookup = ip_countries(list(ip_map.keys()))
        for ip, items in ip_map.items():
            cc = lookup.get(ip, "未知")
            for i, server in items:
                result[i] = cc
                cache[server] = cc
    for i, n, server in pending:
        if i not in result:
            result[i] = "未知"
            cache[server] = "未知"
    try:
        with open("nodes/country_cache.json", "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass
    return result

def build_clash_yaml(nodes):
    """生成按国家分组的可导入 Clash 配置，节点命名: 美国1 / 美国2 ..."""
    import time as _time
    _t0 = _time.time()
    country = assign_countries(nodes)
    print(f"  country detection: {_time.time()-_t0:.1f}s", flush=True)

    # 分组：国家 -> [节点]，组内按 速度降序、延迟升序
    groups = {}
    for i, n in enumerate(nodes):
        groups.setdefault(country[i], []).append(n)
    for c in groups:
        groups[c].sort(key=lambda x: (x.get("speed_mbps") is None,
                                      -(x.get("speed_mbps") or 0),
                                      x.get("delay2_ms") or 99999))
    order = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0] == "未知", kv[0]))

    lines = [
        "# ====================================================",
        "# 免费节点已验证配置 (按国家分组命名)",
        "# 测试: TCP连通 -> mihomo协议延迟x2 -> 真实下载测速",
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
    name2country = {}
    all_names = []
    gh_names = []
    for c, members in order:
        for seq, n in enumerate(members, 1):
            sp = n.get("speed_mbps")
            tag = "⚡" if (sp is not None and sp >= 0.10) else ""
            name = f"{tag}{c}{seq}"
            nn = dict(n)
            nn["name"] = name
            blk = dump_proxy(nn)
            if blk is None:
                continue
            sp_s = f"{n.get('speed_mbps') or 0:.2f}MB/s" if n.get("speed_mbps") is not None else "n/a"
            lines.append(f"    # {n['type']} {n['server']}:{n['port']} 延迟{n.get('delay2_ms')}ms 速度{sp_s}")
            lines.append("\n".join(blk))
            name2country[name] = c
            all_names.append(name)
            if n.get("github_ms") is not None and n.get("raw_ms") is not None:
                gh_names.append(name)

    # proxy-groups：每国家一组 + 手动/自动 + GitHub 可用组
    lines += ["", "proxy-groups:"]
    lines += ["  - name: 🚀 手动选择", "    type: select", "    proxies:",
              "      - ♻️ 自动选择", "      - DIRECT"]
    if gh_names:
        lines.append("      - 🌐 GitHub")
    for c, members in order:
        lines.append(f"      - {c}")
    lines += ["  - name: ♻️ 自动选择", "    type: url-test",
              "    url: http://www.gstatic.com/generate_204",
              "    interval: 300", "    tolerance: 100", "    proxies:"]
    lines += ["      - " + "\n      - ".join(all_names)]
    if gh_names:
        lines += ["  - name: 🌐 GitHub", "    type: select", "    proxies:",
                  "      - ♻️ 自动选择",
                  "      - " + "\n      - ".join(gh_names)]
    for c, members in order:
        names = [f"{'⚡' if (m.get('speed_mbps') is not None and m.get('speed_mbps') >= 0.10) else ''}{c}{seq}"
                 for seq, m in enumerate(members, 1)]
        lines += [f"  - name: {c}", "    type: select", "    proxies:",
                  "      - " + "\n      - ".join(names)]
    lines += ["", "rules:", "  - MATCH,🚀 手动选择", ""]
    return "\n".join(lines)

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    import os as _os
    _os.makedirs("output", exist_ok=True)
    final = json.load(open("nodes/final_nodes.json", encoding="utf-8"))
    verified = [n for n in final if n.get("delay2_ms") is not None]
    # 合并 GitHub 可达性测试结果（test_github.py 写在 verified_nodes.json 里）
    try:
        vf = json.load(open("nodes/verified_nodes.json", encoding="utf-8"))
        gh_by_name = {n.get("test_name"): n for n in vf}
        for n in verified:
            g = gh_by_name.get(n.get("test_name"), {})
            if "github_ms" in g:
                n["github_ms"] = g.get("github_ms")
                n["raw_ms"] = g.get("raw_ms")
    except Exception:
        pass
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
