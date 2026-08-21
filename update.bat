@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title 免费节点 - 手动更新

echo ============================================
echo   免费 Clash 节点 - 手动更新
echo   全流程: 抓源 - 下载 - 解析 - TCP预筛
echo          - 延迟测试 - 二次验证 - 测速 - 报告
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 python，请安装 Python 3.10+ 并勾选 "Add to PATH"
    pause
    exit /b 1
)

echo [1/9] 收集 GitHub 订阅源...
python collect_sources.py
if errorlevel 1 goto :err

echo [2/9] 下载订阅文件...
python download_subs.py
if errorlevel 1 goto :err

echo [3/9] 解析节点...
python parse_nodes.py
if errorlevel 1 goto :err

echo [4/9] TCP 连通性预筛 ^(约 2-4 分钟^)...
python test_tcp.py
if errorlevel 1 goto :err

echo [5/9] 生成 mihomo 配置...
python gen_config.py
if errorlevel 1 goto :err

echo [6/9] 检查 mihomo 核心...
if not exist "bin\mihomo-windows-amd64-compatible.exe" (
    echo   未找到 mihomo，正在下载...
    python get_mihomo.py
    if errorlevel 1 goto :err
)

echo [7/9] 启动 mihomo 并做协议延迟测试 ^(约 5-10 分钟^)...
taskkill /F /IM mihomo-windows-amd64-compatible.exe >nul 2>nul
start "mihomo" /min "bin\mihomo-windows-amd64-compatible.exe" -d "mihomo" -f "mihomo\config.yaml"
python wait_mihomo.py
if errorlevel 1 goto :err
python test_delay.py
if errorlevel 1 goto :err
python verify_nodes.py
if errorlevel 1 goto :err

echo [8/9] 真实下载测速 ^(约 5-10 分钟^)...
python speed_test.py
if errorlevel 1 goto :err

taskkill /F /IM mihomo-windows-amd64-compatible.exe >nul 2>nul

echo [9/9] 生成报告与可导入配置...
python make_summary.py
if errorlevel 1 goto :err
python gen_outputs.py
if errorlevel 1 goto :err

echo.
echo ============================================
echo   更新完成!
echo   - output\best-nodes.yaml   可导入 Clash
echo   - output\report.md         完整测试报告
echo   - output\summary.json      结构化数据
echo ============================================
pause
exit /b 0

:err
echo.
echo [错误] 某一步骤失败，请查看上方日志
taskkill /F /IM mihomo-windows-amd64-compatible.exe >nul 2>nul
pause
exit /b 1
