# -*- coding: utf-8 -*-
"""解析下载的订阅文件为统一节点列表（标准库实现，不依赖第三方包）。"""
import base64, binascii, json, os, re, sys, urllib.parse

# ---------------- 轻量 YAML 子集解析（仅用于 proxies 列表） ----------------
def _parse_inline_dict(rest):
    """递归下降解析行内字典 {k: v, 'k2': 'v2', n: {..}}，兼容无引号键与裸值。"""
    s = rest.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None
    try:
        return json.loads(s)
    except Exception:
        pass
    pos = [0]

    def skip_ws():
        while pos[0] < len(s) and s[pos[0]] in " \t\r\n":
            pos[0] += 1

    def parse_value():
        skip_ws()
        if pos[0] >= len(s):
            return None
        c = s[pos[0]]
        if c == "{":
            return parse_dict()
        if c == "[":
            return parse_list()
        if c in ('"', "'"):
            quote = c
            pos[0] += 1
            buf = []
            while pos[0] < len(s):
                ch = s[pos[0]]
                if ch == "\\" and pos[0] + 1 < len(s):
                    buf.append(s[pos[0] + 1]); pos[0] += 2; continue
                if ch == quote:
                    pos[0] += 1
                    return "".join(buf)
                buf.append(ch); pos[0] += 1
            return "".join(buf)
        buf = []
        while pos[0] < len(s) and s[pos[0]] not in ",}]":
            buf.append(s[pos[0]]); pos[0] += 1
        tok = "".join(buf).strip()
        if tok.lower() == "true":
            return True
        if tok.lower() == "false":
            return False
        if tok.lower() in ("null", "none"):
            return None
        if re.fullmatch(r"-?\d+", tok):
            return int(tok)
        if re.fullmatch(r"-?\d+\.\d+", tok):
            return float(tok)
        return tok

    def parse_list():
        pos[0] += 1
        out = []
        skip_ws()
        if pos[0] < len(s) and s[pos[0]] == "]":
            pos[0] += 1
            return out
        while True:
            out.append(parse_value())
            skip_ws()
            if pos[0] < len(s) and s[pos[0]] == ",":
                pos[0] += 1
                continue
            break
        skip_ws()
        if pos[0] < len(s) and s[pos[0]] == "]":
            pos[0] += 1
        return out

    def parse_dict():
        pos[0] += 1
        out = {}
        skip_ws()
        if pos[0] < len(s) and s[pos[0]] == "}":
            pos[0] += 1
            return out
        while True:
            skip_ws()
            if pos[0] < len(s) and s[pos[0]] in ('"', "'"):
                k = parse_value()
            else:
                kbuf = []
                while pos[0] < len(s) and s[pos[0]] not in ":":
                    kbuf.append(s[pos[0]]); pos[0] += 1
                k = "".join(kbuf).strip()
            skip_ws()
            if pos[0] < len(s) and s[pos[0]] == ":":
                pos[0] += 1
            out[k] = parse_value()
            skip_ws()
            if pos[0] < len(s) and s[pos[0]] == ",":
                pos[0] += 1
                continue
            break
        skip_ws()
        if pos[0] < len(s) and s[pos[0]] == "}":
            pos[0] += 1
        return out

    try:
        return parse_dict()
    except Exception:
        return None

def parse_proxies_yaml(text):
    """从 clash yaml 文本中提取 proxies 列表。返回 list[dict]。"""
    lines = text.splitlines()
    proxies = []
    in_proxies = False
    cur = None
    entry_indent = None
    for raw in lines:
        if raw.strip().startswith("#") or not raw.strip():
            continue
        stripped = raw.strip()
        # 顶层 proxies 键
        m = re.match(r"^proxies\s*:\s*(.*)$", raw)
        if m and not raw.startswith(" "):
            in_proxies = True
            cur = None
            rest = m.group(1).strip()
            if rest and rest not in ("[]", "{}"):
                d = _parse_inline_dict(rest)
                if d:
                    proxies.append(d)
            continue
        # 顶层其他键 → 退出 proxies 区域（列表项 "- " 除外）
        if in_proxies and raw and not raw.startswith((" ", "\t")) and not raw.lstrip().startswith("-"):
            in_proxies = False
            cur = None
            entry_indent = None
            continue
        if not in_proxies:
            continue
        # 列表项开始（同一缩进下的 "- "）
        m = re.match(r"^(\s*)-\s*(.*)$", raw)
        if m:
            indent = len(m.group(1))
            if entry_indent is None or indent == entry_indent:
                if cur:
                    proxies.append(cur)
                entry_indent = indent
                cur = None
                rest = m.group(2).strip()
                if rest.startswith("{"):
                    d = _parse_inline_dict(rest)
                    cur = d if d else {}
                    continue
                m2 = re.match(r"^name\s*:\s*(.*)$", rest)
                if m2:
                    cur = {"name": _unquote(m2.group(1).strip())}
                    continue
                cur = {}
                _parse_inline_kv(cur, rest)
                continue
        if cur is None:
            continue
        # 普通 key: value
        m = re.match(r"^(\s*)([A-Za-z0-9_\-\.]+)\s*:\s*(.*)$", raw)
        if m:
            key, val = m.group(2).strip(), m.group(3).strip()
            _assign(cur, key, _parse_scalar(val))
    if cur:
        proxies.append(cur)
    # 清洗
    out = []
    for p in proxies:
        if not isinstance(p, dict):
            continue
        name = p.pop("_name_raw", None) or p.get("name")
        if not name:
            continue
        p = {k: v for k, v in p.items() if v not in (None, "")}
        p["name"] = _unquote(str(name))
        out.append(p)
    return out

def _parse_inline_kv(cur, rest):
    # 处理 "- key: value" 行内形式
    m = re.match(r"^([A-Za-z0-9_\-\.]+)\s*:\s*(.*)$", rest)
    if m:
        _assign(cur, m.group(1).strip(), _parse_scalar(m.group(2).strip()))

def _parse_scalar(val):
    if val == "" or val in ("~", "null", "Null", "NULL"):
        return None
    # 行内 dict {a: b, c: d}
    if val.startswith("{") and val.endswith("}"):
        inner = val[1:-1].strip()
        d = {}
        for part in _split_top(inner):
            if ":" in part:
                k, v = part.split(":", 1)
                d[k.strip()] = _parse_scalar(v.strip())
        return d
    # 行内 list
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        return [_parse_scalar(x.strip()) for x in _split_top(inner) if x.strip()]
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    m = re.match(r"^-?\d+$", val)
    if m:
        return int(val)
    m = re.match(r"^-?\d+\.\d+$", val)
    if m:
        return float(val)
    return _unquote(val)

def _unquote(val):
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    # 处理结尾注释
    if "#" in val and not val.startswith(("'", '"')):
        val = val.split("#")[0].rstrip()
    return val

def _split_top(s):
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur))
    return parts

def _assign(d, key, value):
    d[key] = value

# ---------------- URI 解析 ----------------
def b64d(s, alt=False):
    """base64 解码，容忍缺失 padding；失败返回 None。"""
    s = s.strip()
    s = re.sub(r"\s+", "", s)
    for pad in ("=" * (4 - len(s) % 4)):
        pass
    if len(s) % 4:
        s += "=" * (4 - len(s) % 4)
    try:
        return base64.b64decode(s).decode("utf-8", "replace")
    except Exception:
        return None

def parse_vmess(link, name):
    payload = link[len("vmess://"):]
    raw = b64d(payload)
    if not raw:
        return None
    try:
        j = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return None
        try:
            j = json.loads(m.group(0))
        except Exception:
            return None
    node = {
        "type": "vmess",
        "name": j.get("ps") or name,
        "server": j.get("add", ""),
        "port": int(j.get("port") or 0),
        "uuid": j.get("id", ""),
        "alterId": int(j.get("aid") or 0),
        "cipher": j.get("scy") or "auto",
        "network": j.get("net") or "tcp",
        "tls": j.get("tls") == "tls",
    }
    if j.get("host"):
        node["ws-opts"] = {"path": j.get("path", "/"), "headers": {"Host": j["host"]}}
        node["servername"] = j.get("sni") or j.get("host")
    elif j.get("path"):
        node["ws-opts"] = {"path": j["path"]}
    if j.get("sni"):
        node["servername"] = j["sni"]
    if j.get("fp"):
        node["client-fingerprint"] = j["fp"]
    if j.get("alpn"):
        node["alpn"] = [j["alpn"]] if isinstance(j["alpn"], str) else j["alpn"]
    return node

def parse_ss(link, name):
    payload = link[len("ss://"):]
    frag = None
    if "#" in payload:
        payload, frag = payload.split("#", 1)
    frag = urllib.parse.unquote(frag) if frag else name
    # 新格式: base64(method:password)@host:port 或 base64(method:pass@host:port)
    if "@" in payload:
        userinfo_b64, hostport = payload.rsplit("@", 1)
        userinfo = b64d(userinfo_b64)
        if not userinfo or ":" not in userinfo:
            return None
        method, password = userinfo.split(":", 1)
        host, port = _hostport(hostport)
    else:
        full = b64d(payload)
        if not full or "@" not in full:
            return None
        userinfo, hostport = full.rsplit("@", 1)
        method, password = userinfo.split(":", 1)
        host, port = _hostport(hostport)
    if not host or not port:
        return None
    node = {"type": "ss", "name": frag, "server": host, "port": port,
            "cipher": method, "password": password}
    # plugin
    q = urllib.parse.parse_qs(urllib.parse.urlparse("//" + hostport).query)
    if "plugin" in q:
        pl = q["plugin"][0]
        if pl.startswith("obfs-local"):
            obfs = urllib.parse.parse_qs(urllib.parse.urlparse(pl).query)
            node["plugin"] = "obfs"
            node["plugin-opts"] = {"mode": obfs.get("obfs", ["http"])[0], "host": obfs.get("obfs-host", [""])[0]}
    return node

def parse_ssr(link, name):
    payload = link[len("ssr://"):]
    raw = b64d(payload)
    if not raw:
        return None
    raw = raw.replace("/?", "?").replace("/", "")  # 兼容
    m = re.match(r"^([^:]+):(\d+):([^:]+):([^:]+):([^:]+):(.+)$", raw)
    if not m:
        return None
    host, port, proto, method, obfs, rest = m.groups()
    pass_b64 = rest.split("/")[0].split("?")[0]
    password = b64d(pass_b64) or ""
    params = {}
    if "?" in rest:
        qs = rest.split("?", 1)[1]
        for kv in qs.split("&"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                params[k] = b64d(v) or v
    node = {"type": "ssr", "name": params.get("remarks") or name,
            "server": host, "port": int(port), "protocol": proto,
            "cipher": method, "obfs": obfs, "password": password}
    if params.get("obfsparam"):
        node["obfs-param"] = params["obfsparam"]
    if params.get("protoparam"):
        node["protocol-param"] = params["protoparam"]
    return node

def parse_trojan(link, name):
    rest = link[len("trojan://"):]
    frag = None
    if "#" in rest:
        rest, frag = rest.split("#", 1)
    frag = urllib.parse.unquote(frag) if frag else name
    u = urllib.parse.urlparse("trojan://" + rest)
    q = urllib.parse.parse_qs(u.query)
    node = {"type": "trojan", "name": frag, "server": u.hostname or "",
            "port": u.port or 443, "password": urllib.parse.unquote(u.username or ""),
            "sni": q.get("sni", [u.hostname or ""])[0]}
    if q.get("type", ["tcp"])[0] in ("ws", "websocket"):
        node["network"] = "ws"
        node["ws-opts"] = {"path": q.get("path", ["/"])[0], "headers": {"Host": q.get("host", [u.hostname or ""])[0]}}
    if q.get("security", ["tls"])[0] == "tls":
        node["tls"] = True
    if q.get("allowInsecure", ["0"])[0] in ("1", "true"):
        node["skip-cert-verify"] = True
    return node

def parse_vless(link, name):
    rest = link[len("vless://"):]
    frag = None
    if "#" in rest:
        rest, frag = rest.split("#", 1)
    frag = urllib.parse.unquote(frag) if frag else name
    u = urllib.parse.urlparse("vless://" + rest)
    q = urllib.parse.parse_qs(u.query)
    node = {"type": "vless", "name": frag, "server": u.hostname or "",
            "port": u.port or 443, "uuid": urllib.parse.unquote(u.username or "")}
    sec = q.get("security", ["none"])[0]
    ntype = q.get("type", ["tcp"])[0]
    if sec == "tls":
        node["tls"] = True
        node["servername"] = q.get("sni", [u.hostname or ""])[0]
    elif sec == "reality":
        node["tls"] = True
        node["servername"] = q.get("sni", [""])[0]
        node["reality-opts"] = {"public-key": q.get("pbk", [""])[0], "short-id": q.get("sid", [""])[0]}
        node["client-fingerprint"] = q.get("fp", ["chrome"])[0]
    if ntype == "ws":
        node["network"] = "ws"
        node["ws-opts"] = {"path": q.get("path", ["/"])[0], "headers": {"Host": q.get("host", [u.hostname or ""])[0]}}
    elif ntype == "grpc":
        node["network"] = "grpc"
        node["grpc-opts"] = {"grpc-service-name": q.get("serviceName", [""])[0]}
    if q.get("allowInsecure", ["0"])[0] in ("1", "true"):
        node["skip-cert-verify"] = True
    return node

def parse_hy2(link, name):
    rest = link[len("hysteria2://"):]
    frag = None
    if "#" in rest:
        rest, frag = rest.split("#", 1)
    frag = urllib.parse.unquote(frag) if frag else name
    u = urllib.parse.urlparse("hysteria2://" + rest)
    q = urllib.parse.parse_qs(u.query)
    node = {"type": "hysteria2", "name": frag, "server": u.hostname or "",
            "port": u.port or 443, "password": urllib.parse.unquote(u.username or "")}
    if q.get("sni"):
        node["sni"] = q["sni"][0]
    if q.get("insecure", ["0"])[0] in ("1", "true"):
        node["skip-cert-verify"] = True
    return node

def parse_tuic(link, name):
    rest = link[len("tuic://"):]
    frag = None
    if "#" in rest:
        rest, frag = rest.split("#", 1)
    frag = urllib.parse.unquote(frag) if frag else name
    u = urllib.parse.urlparse("tuic://" + rest)
    q = urllib.parse.parse_qs(u.query)
    node = {"type": "tuic", "name": frag, "server": u.hostname or "",
            "port": u.port or 443, "uuid": urllib.parse.unquote(u.username or ""),
            "password": urllib.parse.unquote(u.password or "")}
    if q.get("sni"):
        node["sni"] = q["sni"][0]
    if q.get("congestion_control"):
        node["congestion-controller"] = q["congestion_control"][0]
    if q.get("allowInsecure", ["0"])[0] in ("1", "true"):
        node["skip-cert-verify"] = True
    return node

def _hostport(hp):
    if hp.startswith("["):  # ipv6
        m = re.match(r"^\[([^\]]+)\]:(\d+)$", hp)
        if m:
            return m.group(1), int(m.group(2))
        return hp.strip("[]"), 0
    if ":" in hp:
        h, p = hp.rsplit(":", 1)
        try:
            return h, int(p)
        except ValueError:
            return hp, 0
    return hp, 0

def parse_uri_line(line, idx):
    line = line.strip()
    name = f"node{idx}"
    try:
        if line.startswith("vmess://"):
            return parse_vmess(line, name)
        if line.startswith("ss://"):
            return parse_ss(line, name)
        if line.startswith("ssr://"):
            return parse_ssr(line, name)
        if line.startswith("trojan://"):
            return parse_trojan(line, name)
        if line.startswith("vless://"):
            return parse_vless(line, name)
        if line.startswith("hysteria2://") or line.startswith("hy2://"):
            return parse_hy2(line, name)
        if line.startswith("tuic://"):
            return parse_tuic(line, name)
    except Exception:
        return None
    return None

def parse_text_sub(text, prefix="sub"):
    """解析 base64 或 URI 文本，返回节点列表。"""
    nodes = []
    # 尝试 base64
    decoded = None
    if "://" not in text[:500] and len(text) < 5_000_000:
        s = re.sub(r"\s+", "", text)
        if re.fullmatch(r"[A-Za-z0-9+/=]+", s or "x") and len(s) > 20:
            try:
                d = b64d(s)
                if d and "://" in d:
                    decoded = d
            except Exception:
                pass
    body = decoded or text
    for i, line in enumerate(body.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 跳过可能的说明文字
        if "://" not in line:
            continue
        n = parse_uri_line(line, i)
        if n:
            nodes.append(n)
    return nodes

# ---------------- 主流程 ----------------
def main():
    os.makedirs("nodes", exist_ok=True)
    all_nodes = []
    per_sub = {}
    for fn in sorted(os.listdir("subs")):
        path = os.path.join("subs", fn)
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except Exception:
            continue
        if not raw.strip():
            continue
        text = raw.decode("utf-8", "replace")
        nodes = []
        # 先尝试 YAML 解析（有 proxies: 键或扩展名为 yaml/yml）
        if fn.endswith((".yaml", ".yml")) or "proxies:" in text[:4000]:
            nodes = parse_proxies_yaml(text)
        if not nodes:
            nodes = parse_text_sub(text, fn)
        # yaml 节点规范化：过滤无 server/port
        clean = []
        for n in nodes:
            if not isinstance(n, dict) or not n.get("server"):
                continue
            if n.get("type") not in ("ss", "ssr", "vmess", "vless", "trojan", "hysteria2", "tuic"):
                continue
            # 端口容错：可能是 "443?" 之类带尾随字符的脏数据
            try:
                port = int(str(n.get("port", "")).strip().rstrip("?"))
            except Exception:
                continue
            if not (1 <= port <= 65535):
                continue
            n["port"] = port
            n["_sub"] = fn
            clean.append(n)
        per_sub[fn] = clean
        all_nodes.extend(clean)
        print(f"{fn}: {len(clean)} nodes", flush=True)
    with open("nodes/all_nodes.json", "w", encoding="utf-8") as f:
        json.dump(all_nodes, f, ensure_ascii=False, indent=1)
    with open("nodes/per_sub.json", "w", encoding="utf-8") as f:
        json.dump(per_sub, f, ensure_ascii=False, indent=1)
    # 去重（同 type+server+port 只保留一个）
    seen = set()
    dedup = []
    for n in all_nodes:
        k = (n["type"], str(n.get("server", "")).lower(), n.get("port"))
        if k in seen:
            continue
        seen.add(k)
        dedup.append(n)
    with open("nodes/dedup_nodes.json", "w", encoding="utf-8") as f:
        json.dump(dedup, f, ensure_ascii=False)
    print(f"TOTAL: {len(all_nodes)} nodes, dedup: {len(dedup)}", flush=True)

if __name__ == "__main__":
    main()
