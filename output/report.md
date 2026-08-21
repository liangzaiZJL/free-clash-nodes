# 免费 Clash 节点订阅收集与测试报告

> 生成时间: 2026-08-21 12:46 (UTC+8) | 测试环境: Windows 11 + Python 3.12 + mihomo v1.19.30

## 一、总体结果

| 阶段 | 节点数 | 说明 |
|---|---|---|
| 抓取解析 | **20,529** | 24 个订阅源去重后 |
| TCP 可达 | **7,950** (31%) | 3s 内 TCP 建连成功 |
| 协议可用 | **101** | 通过节点实际请求 HTTP 204 成功 |
| 二次验证 | **92** | 两次延迟测试均通过 |
| 测速成功 | **10** | 8MB 真实下载可完成 |

> 结论：免费节点**整体可用率约 0.7%**（10,299 去重节点中 70 个协议可用）。大量节点 TCP 能连（多为 Cloudflare 前置）但后端已死。**推荐直接订阅高质量来源 + 定期自测**。

## 二、订阅来源（GitHub）

| 来源 | 抓取到的节点 | 协议可用 | 可用率 | 质量评价 |
|---|---|---|---|---|
| Ruk1ng001-clash.yaml | 106 | 76 | 71% | ✅ 推荐 |
| Epodonios-all-configs | 1175 | 11 | 0% | ⚠️ 一般 |
| BestClash-proxies.yaml | 14 | 6 | 42% | ⚠️ 一般 |
| Au1rxx-clash-full.yaml | 108 | 3 | 2% | ⚠️ 一般 |
| NiceVPN-clash.yaml | 1078 | 2 | 0% | ⚠️ 一般 |
| NoMoreWalls-list.yml | 7 | 1 | 14% | ⚠️ 一般 |
| extra-agg-pool--previous-yaml.yaml | 172 | 1 | 0% | ⚠️ 一般 |
| ssrsub-v2ray | 1 | 1 | 100% | ✅ 推荐 |
| ts-sf-v2 | 1 | 1 | 100% | ✅ 推荐 |
| Barabama-nodefree | 11 | 0 | 0% | ❌ 基本不可用 |
| Leon406-subshare-vless | 2217 | 0 | 0% | ❌ 基本不可用 |
| MhdiTaheri-mix | 43 | 0 | 0% | ❌ 基本不可用 |
| Pawdroid-Free-servers | 5 | 0 | 0% | ❌ 基本不可用 |
| SSAggregator-merge.yml | 1024 | 0 | 0% | ❌ 基本不可用 |
| SoliSpirit-all-configs | 204 | 0 | 0% | ❌ 基本不可用 |
| airport-tested.yaml | 152 | 0 | 0% | ❌ 基本不可用 |
| anaer-clash.yaml | 6 | 0 | 0% | ❌ 基本不可用 |
| extra-agg-pool--pool-yaml.yaml | 72 | 0 | 0% | ❌ 基本不可用 |
| ermaozi-clash.yml | 1 | 0 | 0% | ❌ 基本不可用 |
| free18-c.yaml | 23 | 0 | 0% | ❌ 基本不可用 |
| mfbpn-trial.yaml | 8 | 0 | 0% | ❌ 基本不可用 |
| sakha1370-OpenRay | 1522 | 0 | 0% | ❌ 基本不可用 |
| vxiaov-clash-provider.yaml | 4 | 0 | 0% | ❌ 基本不可用 |

**最推荐订阅（实测可用率最高）：**

- `https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml`
- `https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray`
- `https://raw.githubusercontent.com/ts-sf/fly/main/v2`

## 三、协议类型可用率

| 协议 | TCP可达 | 协议可用 | 可用率 |
|---|---|---|---|
| 140 | 140 | 47 | 33% |
| 73 | 73 | 40 | 54% |
| 5240 | 5240 | 9 | 0% |
| 1886 | 1886 | 2 | 0% |
| 590 | 590 | 2 | 0% |
| 21 | 21 | 1 | 4% |

> ss / hysteria2 存活率最高（40%+）；vmess / trojan / vless 多为 Cloudflare 前置的死节点。

## 四、测速最快的节点（8MB 下载）

| 速度 | 延迟 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 0.76 MB/s | 407ms | hysteria2 | `player.wwwinternetvideo.click:443` | Ruk1ng001-clash.yaml |
| 0.02 MB/s | 499ms | ss | `49.254.204.133:1774` | Epodonios-all-configs |
| 0.01 MB/s | 397ms | ssr | `qcg8fhp6y6v9wn.cache872671.com:1302` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 493ms | ss | `e1acw359hdvf.cdn000.com:31201` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 494ms | ssr | `5zkpq9sentjnah.cache872671.com:1322` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 494ms | ssr | `4vnx5kqwk8mxsr.cache872671.com:1320` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 496ms | ss | `121.46.230.138:65443` | Ruk1ng001-clash.yaml |
| 0.01 MB/s | 498ms | ssr | `neetb62ecrq2zg.cache872671.com:1304` | Ruk1ng001-clash.yaml |
| 0.00 MB/s | 306ms | ss | `hk.kexueyun.top:1011` | Ruk1ng001-clash.yaml |
| 0.00 MB/s | 392ms | ss | `161.118.236.226:56927` | Ruk1ng001-clash.yaml |

## 五、延迟最低的节点

| 延迟 | 速度 | 类型 | 服务器 | 来源 |
|---|---|---|---|---|
| 305ms | n/a | vmess | `112.132.215.108:50002` | Ruk1ng001-clash.yaml |
| 306ms | 0.00 MB/s | ss | `hk.kexueyun.top:1011` | Ruk1ng001-clash.yaml |
| 392ms | 0.00 MB/s | ss | `161.118.236.226:56927` | Ruk1ng001-clash.yaml |
| 397ms | 0.01 MB/s | ssr | `qcg8fhp6y6v9wn.cache872671.com:1302` | Ruk1ng001-clash.yaml |
| 397ms | n/a | ss | `95.40.120.162:8319` | Ruk1ng001-clash.yaml |
| 401ms | n/a | ss | `54.95.207.148:8316` | Epodonios-all-configs |
| 402ms | n/a | vless | `120.227.1.43:12528` | Epodonios-all-configs |
| 407ms | 0.76 MB/s | hysteria2 | `player.wwwinternetvideo.click:443` | Ruk1ng001-clash.yaml |
| 493ms | 0.01 MB/s | ss | `e1acw359hdvf.cdn000.com:31201` | Ruk1ng001-clash.yaml |
| 494ms | 0.01 MB/s | ssr | `5zkpq9sentjnah.cache872671.com:1322` | Ruk1ng001-clash.yaml |
| 494ms | 0.01 MB/s | ssr | `4vnx5kqwk8mxsr.cache872671.com:1320` | Ruk1ng001-clash.yaml |
| 496ms | 0.01 MB/s | ss | `121.46.230.138:65443` | Ruk1ng001-clash.yaml |

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
