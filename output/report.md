# 免费 Clash 节点订阅收集与测试报告

> 生成时间: 2026-08-21 10:25 (UTC+8) | 测试环境: Windows 11 + Python 3.12 + mihomo v1.19.30

## 一、总体结果

| 阶段 | 节点数 | 说明 |
|---|---|---|
| 抓取解析 | **10,299** | 24 个订阅源去重后 |
| TCP 可达 | **3,195** (31%) | 3s 内 TCP 建连成功 |
| 协议可用 | **70** | 通过节点实际请求 HTTP 204 成功 |
| 二次验证 | **66** | 两次延迟测试均通过 |
| 测速成功 | **56** | 8MB 真实下载可完成 |

> 结论：免费节点**整体可用率约 0.7%**（10,299 去重节点中 70 个协议可用）。大量节点 TCP 能连（多为 Cloudflare 前置）但后端已死。**推荐直接订阅高质量来源 + 定期自测**。

## 二、订阅来源（GitHub）

| 来源 | 抓取到的节点 | 协议可用 | 可用率 | 质量评价 |
|---|---|---|---|---|
| Au1rxx-clash-full.yaml | 81 | 61 | 75% | ✅ 推荐 |
| NiceVPN-clash.yaml | 1088 | 3 | 0% | ⚠️ 一般 |
| Ruk1ng001-clash.yaml | 72 | 2 | 2% | ⚠️ 一般 |
| NoMoreWalls-list.yml | 11 | 1 | 9% | ⚠️ 一般 |
| Pawdroid-Free-servers | 20 | 1 | 5% | ⚠️ 一般 |
| anaer-clash.yaml | 409 | 1 | 0% | ⚠️ 一般 |
| free18-c.yaml | 99 | 1 | 1% | ⚠️ 一般 |
| BestClash-proxies.yaml | 12 | 0 | 0% | ❌ 基本不可用 |
| SSAggregator-merge.yml | 1050 | 0 | 0% | ❌ 基本不可用 |
| airport-tested.yaml | 310 | 0 | 0% | ❌ 基本不可用 |
| ermaozi-clash.yml | 4 | 0 | 0% | ❌ 基本不可用 |
| ermaozi-v2ray.txt | 7 | 0 | 0% | ❌ 基本不可用 |
| mfbpn-trial.yaml | 4 | 0 | 0% | ❌ 基本不可用 |
| ts-sf-clash | 24 | 0 | 0% | ❌ 基本不可用 |
| mfuu-v2ray | 3 | 0 | 0% | ❌ 基本不可用 |
| ts-sf-v2 | 1 | 0 | 0% | ❌ 基本不可用 |

**最推荐订阅（实测可用率最高）：**

- `https://github.com/Au1rxx/free-vpn-subscriptions/raw/main/output/clash.yaml`

## 三、协议类型可用率

| 协议 | TCP可达 | 协议可用 | 可用率 |
|---|---|---|---|
| 131 | 131 | 58 | 44% |
| 12 | 12 | 5 | 41% |
| 800 | 800 | 3 | 0% |
| 441 | 441 | 3 | 0% |
| 1755 | 1755 | 1 | 0% |
| 56 | 56 | 0 | 0% |

> ss / hysteria2 存活率最高（40%+）；vmess / trojan / vless 多为 Cloudflare 前置的死节点。

## 四、测速最快的节点（8MB 下载）

| 速度 | 延迟 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 0.76 MB/s | 407ms | hysteria2 | `45.32.252.144:443` | Au1rxx-clash-full.yaml |
| 0.36 MB/s | 510ms | hysteria2 | `66.94.121.46:443` | Au1rxx-clash-full.yaml |
| 0.24 MB/s | 388ms | hysteria2 | `player.wwwinternetvideo.click:443` | Au1rxx-clash-full.yaml |
| 0.14 MB/s | 407ms | hysteria2 | `starlink-ft.251313.xyz:443` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 282ms | vless | `120.227.1.43:12528` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 305ms | hysteria2 | `fast.wwwinternetvideo.click:443` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 406ms | ss | `211.91.158.44:21110` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 497ms | ss | `211.91.158.26:21103` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 509ms | ss | `211.91.158.26:21121` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 509ms | ss | `211.91.158.26:21119` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 510ms | ss | `211.91.158.26:21109` | Au1rxx-clash-full.yaml |
| 0.01 MB/s | 510ms | ss | `211.91.158.44:21119` | Au1rxx-clash-full.yaml |

## 五、延迟最低的节点

| 延迟 | 速度 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 282ms | 0.01 MB/s | vless | `120.227.1.43:12528` | Ruk1ng001-clash.yaml |
| 305ms | 0.01 MB/s | hysteria2 | `fast.wwwinternetvideo.click:443` | Au1rxx-clash-full.yaml |
| 384ms | 0.00 MB/s | vmess | `112.132.215.108:50002` | anaer-clash.yaml |
| 388ms | 0.24 MB/s | hysteria2 | `player.wwwinternetvideo.click:443` | Au1rxx-clash-full.yaml |
| 406ms | 0.01 MB/s | ss | `211.91.158.44:21110` | Au1rxx-clash-full.yaml |
| 407ms | 0.76 MB/s | hysteria2 | `45.32.252.144:443` | Au1rxx-clash-full.yaml |
| 407ms | 0.14 MB/s | hysteria2 | `starlink-ft.251313.xyz:443` | Au1rxx-clash-full.yaml |
| 497ms | 0.01 MB/s | ss | `211.91.158.26:21103` | Au1rxx-clash-full.yaml |
| 509ms | 0.01 MB/s | ss | `211.91.158.26:21121` | Au1rxx-clash-full.yaml |
| 509ms | 0.01 MB/s | ss | `211.91.158.26:21119` | Au1rxx-clash-full.yaml |
| 510ms | 0.36 MB/s | hysteria2 | `66.94.121.46:443` | Au1rxx-clash-full.yaml |
| 510ms | 0.01 MB/s | ss | `211.91.158.26:21109` | Au1rxx-clash-full.yaml |

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
