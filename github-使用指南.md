# GitHub Desktop 安装与配置指南（已注册账号版）

> 目标：装好 GitHub Desktop → 登录你的账号 → 把 free-clash-nodes 项目推到 GitHub → 开启每日自动更新

## 一、安装

- 推荐方式：`winget install --id GitHub.GitHubDesktop -e --accept-source-agreements --accept-package-agreements`
- 或官网下载：https://desktop.github.com/ （下载后双击安装，一路下一步）
- GitHub Desktop 自带 Git，装这一个就够

## 二、登录你的账号

1. 打开 GitHub Desktop（开始菜单搜索 "GitHub Desktop"）
2. 点 **Sign in to GitHub.com**
3. 会自动打开浏览器 → 输入你的 GitHub 账号密码登录 → 点授权（Authorize）
4. 回到 GitHub Desktop 会显示你的用户名，点 **Finish**

> 如果弹出 "Configure git"，保持默认即可（GitHub Desktop 会自动写入你的用户名和邮箱）。
> 也可在命令行验证：`git config --global user.name` 和 `git config --global user.email`。

## 三、把项目发布到 GitHub

1. GitHub Desktop 菜单 → **File → Add local repository…**
2. 路径填：`C:\Users\95752\Documents\dsh\free-clash-nodes` → 点 **Add Repository**
3. 顶部会提示有未提交的更改，先点 **Commit to main** 提交（填个描述，如 "初始提交"）
4. 点窗口右上角 **Publish repository**
5. 仓库名填 `free-clash-nodes`；可见性建议选 **Private**（节点信息属于敏感内容）
6. 点 **Publish repository** → 完成推送

> 项目里已配好 `.gitignore`，生成的节点数据（subs/nodes/bin 等）不会上传，只会上传脚本和 output 结果。

## 四、开启每日自动更新（GitHub Actions）

1. 浏览器打开 `https://github.com/<你的用户名>/free-clash-nodes`
2. 点顶部 **Actions** 标签页 → 第一次会提示启用，点 **I understand my workflows, go ahead and enable them**
3. 左侧点 **每日免费节点更新** → 右侧 **Run workflow** → 绿色按钮立即手动跑一次
4. 之后每天 UTC 21:30（北京时间 05:30）自动运行，结果自动提交回仓库

## 五、把最新节点加进 Clash

更新完成后，订阅地址为：

```
https://raw.githubusercontent.com/<你的用户名>/free-clash-nodes/main/output/best-nodes.yaml
```

在 Clash Verge / Mihomo 里：**订阅 → 新建 → 填入上面的链接 → 导入**。
以后 Clash 会自动拉取最新节点；也可以随时在 Actions 页面手动 **Run workflow** 强制刷新。

## 六、常见问题

| 问题 | 解决 |
|---|---|
| 推送失败 "Authentication failed" | 在 GitHub Desktop 重新登录：File → Options → Accounts |
| Actions 不自动跑 | 确认仓库默认分支是 main，且 workflow 文件在 `.github/workflows/` 下 |
| 想改更新频率 | 编辑 `.github/workflows/daily-sub.yml` 里的 cron 表达式 |
| 不想自动提交 | 删掉 workflow 里 "Commit results" 那一步，只保留 artifact 下载 |

## 七、替代方案：纯命令行（不需要 GitHub Desktop）

```bash
# 安装 Git for Windows: https://git-scm.com/download/win （一路下一步）

git config --global user.name "你的用户名"
git config --global user.email "你的注册邮箱"
cd C:\Users\95752\Documents\dsh\free-clash-nodes
git init
git add .
git commit -m "初始提交"
git branch -M main
git remote add origin https://github.com/你的用户名/free-clash-nodes.git
git push -u origin main
```
