# 免费 Clash 节点订阅收集与测试报告

> 生成时间: 2026-08-21 14:58 (UTC+8) | 测试环境: Windows 11 + Python 3.12 + mihomo v1.19.30

## 一、总体结果

| 阶段 | 节点数 | 说明 |
|---|---|---|
| 抓取解析 | **20,789** | 24 个订阅源去重后 |
| TCP 可达 | **8,016** (31%) | 3s 内 TCP 建连成功 |
| 协议可用 | **113** | 通过节点实际请求 HTTP 204 成功 |
| 二次验证 | **65** | 两次延迟测试均通过 |
| 测速成功 | **12** | 8MB 真实下载可完成 |

> 结论：免费节点**整体可用率约 0.7%**（10,299 去重节点中 70 个协议可用）。大量节点 TCP 能连（多为 Cloudflare 前置）但后端已死。**推荐直接订阅高质量来源 + 定期自测**。

## 二、订阅来源（GitHub）

| 来源 | 抓取到的节点 | 协议可用 | 可用率 | 质量评价 |
|---|---|---|---|---|
| Ruk1ng001-clash.yaml | 93 | 59 | 63% | ✅ 推荐 |
| sakha1370-OpenRay | 1497 | 29 | 1% | ⚠️ 一般 |
| Au1rxx-clash-full.yaml | 122 | 10 | 8% | ⚠️ 一般 |
| Epodonios-all-configs | 1148 | 8 | 0% | ⚠️ 一般 |
| Leon406-subshare-vless | 2245 | 2 | 0% | ⚠️ 一般 |
| NiceVPN-clash.yaml | 1071 | 2 | 0% | ⚠️ 一般 |
| BestClash-proxies.yaml | 12 | 1 | 8% | ⚠️ 一般 |
| extra-agg-pool--previous-yaml.yaml | 170 | 1 | 0% | ⚠️ 一般 |
| ssrsub-v2ray | 1 | 1 | 100% | ✅ 推荐 |
| Barabama-nodefree | 11 | 0 | 0% | ❌ 基本不可用 |
| MhdiTaheri-mix | 42 | 0 | 0% | ❌ 基本不可用 |
| Pawdroid-Free-servers | 5 | 0 | 0% | ❌ 基本不可用 |
| NoMoreWalls-list.yml | 6 | 0 | 0% | ❌ 基本不可用 |
| SSAggregator-merge.yml | 1024 | 0 | 0% | ❌ 基本不可用 |
| SoliSpirit-all-configs | 184 | 0 | 0% | ❌ 基本不可用 |
| airport-tested.yaml | 146 | 0 | 0% | ❌ 基本不可用 |
| anaer-clash.yaml | 6 | 0 | 0% | ❌ 基本不可用 |
| extra-agg-pool--pool-yaml.yaml | 71 | 0 | 0% | ❌ 基本不可用 |
| ermaozi-clash.yml | 1 | 0 | 0% | ❌ 基本不可用 |
| free18-c.yaml | 156 | 0 | 0% | ❌ 基本不可用 |
| mfbpn-trial.yaml | 5 | 0 | 0% | ❌ 基本不可用 |

**最推荐订阅（实测可用率最高）：**

- `https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml`
- `https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray`

## 三、协议类型可用率

| 协议 | TCP可达 | 协议可用 | 可用率 |
|---|---|---|---|
| 152 | 152 | 54 | 35% |
| 76 | 76 | 40 | 52% |
| 5177 | 5177 | 14 | 0% |
| 1874 | 1874 | 2 | 0% |
| 709 | 709 | 2 | 0% |
| 28 | 28 | 1 | 3% |

> ss / hysteria2 存活率最高（40%+）；vmess / trojan / vless 多为 Cloudflare 前置的死节点。

## 四、测速最快的节点（8MB 下载）

| 速度 | 延迟 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 0.02 MB/s | 407ms | ss | `103.169.67.34:65443` | BestClash-proxies.yaml |
| 0.01 MB/s | 292ms | ss | `hk.kexueyun.top:1011` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 383ms | vless | `120.227.1.43:12528` | Epodonios-all-configs |
| 0.01 MB/s | 383ms | ss | `211.91.158.26:21121` | sakha1370-OpenRay |
| 0.01 MB/s | 388ms | ss | `118.107.222.231:65443` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 509ms | ss | `211.91.158.26:21119` | sakha1370-OpenRay |
| 0.01 MB/s | 510ms | ss | `211.91.158.44:21121` | sakha1370-OpenRay |
| 0.01 MB/s | 526ms | ss | `211.91.158.26:21103` | sakha1370-OpenRay |
| 0.01 MB/s | 551ms | ss | `211.91.158.44:21119` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 552ms | ss | `211.91.158.44:21110` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 585ms | ss | `211.91.158.44:21103` | sakha1370-OpenRay |
| 0.01 MB/s | 593ms | ss | `211.91.158.26:21107` | Au1rxx-clash-full.yaml |

## 五、延迟最低的节点

| 延迟 | 速度 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 292ms | 0.01 MB/s | ss | `hk.kexueyun.top:1011` | Au1rxx-clash-full.yaml |
| 383ms | 0.01 MB/s | vless | `120.227.1.43:12528` | Epodonios-all-configs |
| 383ms | 0.01 MB/s | ss | `211.91.158.26:21121` | sakha1370-OpenRay |
| 388ms | 0.01 MB/s | ss | `118.107.222.231:65443` | Ruk1ng001-clash.yaml |
| 405ms | n/a | ss | `54.95.207.148:8316` | Epodonios-all-configs |
| 407ms | 0.02 MB/s | ss | `103.169.67.34:65443` | BestClash-proxies.yaml |
| 407ms | n/a | ss | `138.2.81.62:56927` | Ruk1ng001-clash.yaml |
| 441ms | n/a | ss | `95.40.120.162:8319` | Au1rxx-clash-full.yaml |
| 509ms | 0.01 MB/s | ss | `211.91.158.26:21119` | sakha1370-OpenRay |
| 510ms | 0.01 MB/s | ss | `211.91.158.44:21121` | sakha1370-OpenRay |
| 526ms | 0.01 MB/s | ss | `211.91.158.26:21103` | sakha1370-OpenRay |
| 551ms | 0.01 MB/s | ss | `211.91.158.44:21119` | Au1rxx-clash-full.yaml |

## 六、使用方法

1. **导入配置**：将 `best-nodes.yaml` 导入 Clash Verge / Clash Meta / Mihomo（节点名带 ⚡ 为测速较快的）
2. **订阅更新**：把「二、订阅来源」中的推荐链接加进客户端的订阅列表，定期更新
3. **自行测速**：运行本项目脚本 `python test_tcp.py && python test_delay.py && python speed_test.py`

## 七、测试方法

1. **收集**：从 GitHub 知名免费节点仓库抓取订阅文件（Clash YAML / V2Ray base64）
2. **解析**：标准库实现 YAML 子集解析器 + URI 解析器（vmess/ss/ssr/vless/trojan/hy2/tuic），去重后 10,299 节点
3. **TCP 预筛**：400 线程并发 TCP 建连测试（3s 超时）
4. **协议延迟**：mihomo 加载全部节点，逐个真实请求 `http://www.gstatic.com/generate_204`，4s 超时
5. **真实测速**：经 mihomo mixed-port 下载 Cloudflare 8MB 测速文件，记录 MB/s

## 八、免责声明

- 免费节点**随时可能失效或变慢**，本报告数据仅为测试时刻的快照
- 节点来自第三方公开仓库，**不保证安全性**，请勿传输敏感信息，风险自负
- 请遵守当地法律法规，合法合规使用网络
