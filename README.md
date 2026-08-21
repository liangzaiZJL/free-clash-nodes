# 免费 Clash 节点订阅收集与测试

从 GitHub 收集免费 Clash/V2Ray 订阅源，解析全部节点，并用真实请求测试**可用率、延迟、带宽**，输出可直接导入的配置和测试报告。

## 快速开始

```bash
# 1. 收集订阅源（GitHub 仓库 README 提取链接）
python collect_sources.py

# 2. 下载精选订阅文件
python download_subs.py

# 3. 解析为统一节点（标准库 YAML/URI 解析器，去重）
python parse_nodes.py

# 4. TCP 连通性预筛（400 线程并发）
python test_tcp.py

# 5. 生成 mihomo 配置并启动核心（需要 mihomo 二进制，见 bin/）
python gen_config.py

# 6. 协议级延迟测试（mihomo 真实请求 gstatic 204）
python test_delay.py

# 7. 二次验证 + 8MB 真实下载测速
python verify_nodes.py
python speed_test.py

# 8. 生成报告与可导入配置
python make_summary.py
python gen_outputs.py   # → output/report.md + output/best-nodes.yaml
```

## 输出

| 文件 | 说明 |
|---|---|
| `output/report.md` | 完整测试报告（来源可用率 / 协议可用率 / 节点排名） |
| `output/best-nodes.yaml` | 已验证节点 Clash 配置，可直接导入（⚡ 为测速较快节点） |
| `output/summary.json` | 结构化统计数据 |
| `nodes/` | 中间数据（解析结果、各阶段测试结果） |
| `subs/` | 下载的原始订阅文件 |

## 测试方法

1. **收集**：从 GitHub 知名免费节点仓库抓取订阅（Clash YAML / V2Ray base64，含镜像回退）
2. **解析**：标准库手写 YAML 子集解析 + URI 解析（vmess/ss/ssr/vless/trojan/hy2/tuic），去重
3. **TCP 预筛**：TCP 建连测试（3s 超时），过滤死主机
4. **协议延迟**：mihomo 加载全部节点，逐节点真实请求 `http://www.gstatic.com/generate_204` 测延迟
5. **真实测速**：经 mihomo mixed-port 下载 Cloudflare 8MB 测速文件，测 MB/s

## 2026-08-21 测试快照（摘要）

- 24 个订阅源 → 15,573 节点 → 去重 **10,299**
- TCP 可达 **3,195**（31%），协议可用 **70**（约 0.7%）
- 最推荐订阅：[Au1rxx/free-vpn-subscriptions](https://github.com/Au1rxx/free-vpn-subscriptions)（实测可用率 75%）
- 最快节点：hysteria2 约 0.76 MB/s；ss 节点多被限速 ~0.01 MB/s

## 扩展途径（2026-08-21 实测）

除了 GitHub README 抓取，还实测了以下新途径（脚本见 `fetch_extra.py` / `fetch_nodefree.py`）：

| 途径 | 可行性 | 实测结果 | 备注 |
|---|---|---|---|
| Telegram 频道预览页 `t.me/s/<频道>` | ✅ 可抓（无需 token） | 无网络重置时可拿到 20 条消息 | 节点常以图片/不定期发布，需多频道+翻页+去重 |
| 聚合仓库自身节点池（如 `sinspired/airport/subs/_pool.yaml`） | ✅ 已跑通 | 744 节点，TCP 可达 258，协议存活 2 | 池是"多源合并"，质量≈源的平均水平 |
| 分享站文章页（nodefree.me） | ⚠️ 部分 | 文章页为 JS 渲染，HTML 直接抓无节点 | 需浏览器渲染（selenium/playwright） |
| 代码搜索（grep.app / GitHub Code Search） | ⚠️ 限流 | 无 token 时被限流 | 适合发现散落的新仓库 |
| SEO 内容农场站（clashnode.org 等） | ❌ | 全是机场广告，无真实节点 | 需过滤 |

**结论**：渠道数量不是瓶颈，**质量天花板取决于源的维护质量**（实测 Au1rxx 可用率 75%，多数源 <1%）。
推荐做法 = 多源并取 + 定时自测 + 只保留可用节点的"反馈闭环"。

## 更新方式

### 方式一：手动更新（Windows）

双击运行 `update.bat`（或在命令行执行），自动完成 抓源 → 下载 → 解析 → TCP 预筛 → 延迟测试 → 二次验证 → 测速 → 生成报告，全程约 20-40 分钟。

### 方式二：GitHub Actions 每日自动更新

1. 把本目录推送到 GitHub（如 `https://github.com/<你的用户名>/free-clash-nodes`）
2. 仓库自带 `.github/workflows/daily-sub.yml`：
   - 每天 UTC 21:30（北京时间次日 05:30）自动运行完整流水线
   - 也可在 Actions 页面点击 **Run workflow** 手动触发
   - 运行结果自动提交 `output/best-nodes.yaml` 与 `output/report.md` 回仓库，并上传为 artifact
3. 更新后的订阅可直接用 raw 链接导入 Clash：
   `https://raw.githubusercontent.com/<你的用户名>/free-clash-nodes/main/output/best-nodes.yaml`

## 免责声明

免费节点随时可能失效，请定期自测；节点来自第三方公开仓库，不保证安全性，请勿传输敏感信息，风险自负；请遵守当地法律法规。
