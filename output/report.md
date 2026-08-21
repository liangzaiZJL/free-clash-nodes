# 免费 Clash 节点订阅收集与测试报告

> 生成时间: 2026-08-21 11:52 (UTC+8) | 测试环境: Windows 11 + Python 3.12 + mihomo v1.19.30

## 一、总体结果

| 阶段 | 节点数 | 说明 |
|---|---|---|
| 抓取解析 | **10,275** | 24 个订阅源去重后 |
| TCP 可达 | **4,413** (31%) | 3s 内 TCP 建连成功 |
| 协议可用 | **862** | 通过节点实际请求 HTTP 204 成功 |
| 二次验证 | **841** | 两次延迟测试均通过 |
| 测速成功 | **11** | 8MB 真实下载可完成 |

> 结论：免费节点**整体可用率约 0.7%**（10,299 去重节点中 70 个协议可用）。大量节点 TCP 能连（多为 Cloudflare 前置）但后端已死。**推荐直接订阅高质量来源 + 定期自测**。

## 二、订阅来源（GitHub）

| 来源 | 抓取到的节点 | 协议可用 | 可用率 | 质量评价 |
|---|---|---|---|---|
| Au1rxx-clash-full.yaml | 800 | 553 | 69% | ✅ 推荐 |
| Ruk1ng001-clash.yaml | 145 | 112 | 77% | ✅ 推荐 |
| SSAggregator-merge.yml | 1206 | 96 | 7% | ⚠️ 一般 |
| airport-tested.yaml | 434 | 30 | 6% | ⚠️ 一般 |
| anaer-clash.yaml | 462 | 22 | 4% | ⚠️ 一般 |
| NiceVPN-clash.yaml | 1143 | 8 | 0% | ⚠️ 一般 |
| Pawdroid-Free-servers | 16 | 7 | 43% | ⚠️ 一般 |
| free18-c.yaml | 119 | 7 | 5% | ⚠️ 一般 |
| BestClash-proxies.yaml | 15 | 6 | 40% | ⚠️ 一般 |
| V2RayAggregator-Eternity | 6 | 6 | 100% | ✅ 推荐 |
| go4sharing-sub.yaml | 6 | 6 | 100% | ✅ 推荐 |
| ermaozi-clash.yml | 7 | 3 | 42% | ⚠️ 一般 |
| ts-sf-clash | 32 | 3 | 9% | ⚠️ 一般 |
| NoMoreWalls-list.yml | 4 | 2 | 50% | ✅ 推荐 |
| ts-sf-v2 | 1 | 1 | 100% | ✅ 推荐 |
| mfbpn-trial.yaml | 10 | 0 | 0% | ❌ 基本不可用 |
| mfuu-clash.yaml | 3 | 0 | 0% | ❌ 基本不可用 |
| vxiaov-clash-provider.yaml | 4 | 0 | 0% | ❌ 基本不可用 |

**最推荐订阅（实测可用率最高）：**

- `https://github.com/Au1rxx/free-vpn-subscriptions/raw/main/output/clash.yaml`
- `https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml`
- `https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity`
- `https://raw.githubusercontent.com/go4sharing/sub/main/sub.yaml`
- `https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml`
- `https://raw.githubusercontent.com/ts-sf/fly/main/v2`

## 三、协议类型可用率

| 协议 | TCP可达 | 协议可用 | 可用率 |
|---|---|---|---|
| 899 | 899 | 449 | 49% |
| 313 | 313 | 226 | 72% |
| 1246 | 1246 | 84 | 6% |
| 1862 | 1862 | 46 | 2% |
| 78 | 78 | 46 | 58% |
| 15 | 15 | 11 | 73% |

> ss / hysteria2 存活率最高（40%+）；vmess / trojan / vless 多为 Cloudflare 前置的死节点。

## 四、测速最快的节点（8MB 下载）

| 速度 | 延迟 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 30.87 MB/s | 17ms | vmess | `173.249.209.146:20086` | SSAggregator-merge.yml |
| 30.66 MB/s | 22ms | vmess | `165.140.216.141:443` | airport-tested.yaml |
| 28.60 MB/s | 31ms | vmess | `165.140.216.142:443` | Au1rxx-clash-full.yaml |
| 26.62 MB/s | 7ms | ss | `167.99.103.190:443` | Au1rxx-clash-full.yaml |
| 24.63 MB/s | 17ms | ss | `108.181.118.10:8388` | Au1rxx-clash-full.yaml |
| 23.63 MB/s | 28ms | trojan | `128.14.148.84:5531` | free18-c.yaml |
| 21.95 MB/s | 23ms | vmess | `82.198.246.233:180` | Au1rxx-clash-full.yaml |
| 19.01 MB/s | 21ms | ss | `108.181.0.177:8388` | SSAggregator-merge.yml |
| 9.22 MB/s | 20ms | vmess | `216.106.185.141:22324` | Au1rxx-clash-full.yaml |
| 5.69 MB/s | 22ms | vmess | `82.198.246.250:180` | Au1rxx-clash-full.yaml |
| 1.24 MB/s | 29ms | ss | `216.105.168.18:443` | SSAggregator-merge.yml |

## 五、延迟最低的节点

| 延迟 | 速度 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 7ms | 26.62 MB/s | ss | `167.99.103.190:443` | Au1rxx-clash-full.yaml |
| 17ms | 30.87 MB/s | vmess | `173.249.209.146:20086` | SSAggregator-merge.yml |
| 17ms | 24.63 MB/s | ss | `108.181.118.10:8388` | Au1rxx-clash-full.yaml |
| 20ms | 9.22 MB/s | vmess | `216.106.185.141:22324` | Au1rxx-clash-full.yaml |
| 21ms | 19.01 MB/s | ss | `108.181.0.177:8388` | SSAggregator-merge.yml |
| 22ms | 30.66 MB/s | vmess | `165.140.216.141:443` | airport-tested.yaml |
| 22ms | 5.69 MB/s | vmess | `82.198.246.250:180` | Au1rxx-clash-full.yaml |
| 23ms | 21.95 MB/s | vmess | `82.198.246.233:180` | Au1rxx-clash-full.yaml |
| 23ms | n/a | vless | `104.16.79.73:443` | Au1rxx-clash-full.yaml |
| 24ms | n/a | vless | `104.16.117.43:443` | Au1rxx-clash-full.yaml |
| 25ms | n/a | vless | `172.66.44.97:443` | Au1rxx-clash-full.yaml |
| 26ms | n/a | vless | `104.16.7.198:443` | Ruk1ng001-clash.yaml |

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
