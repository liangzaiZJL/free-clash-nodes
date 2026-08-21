@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

rem ============================================
rem  自动把 output 结果提交并推送到 GitHub
rem  其他电脑用 raw 链接拉取最新 best-nodes.yaml
rem ============================================

rem --- 查找 git（先 PATH，再找 GitHub Desktop 自带的） ---
set "GIT="
where git >nul 2>nul && set "GIT=git"
if not defined GIT (
    for /f "delims=" %%i in ('where /r "%LOCALAPPDATA%\GitHubDesktop" git.exe 2^>nul') do (
        if not defined GIT set "GIT=%%i"
    )
)
if not defined GIT (
    echo [错误] 未找到 git。请安装 GitHub Desktop 或 Git for Windows。
    pause
    exit /b 1
)

echo [1/3] 提交 output 结果...
"%GIT%" add output/ README.md
"%GIT%" commit -m "update: 节点更新 %date%" >nul 2>nul
if errorlevel 1 (
    echo       没有新变化需要提交，直接推送。
) else (
    echo       已提交。
)

echo [2/3] 拉取远端（若 CI 有自动提交则以本地结果为准）...
"%GIT%" pull origin main --no-rebase -X ours >nul 2>nul

echo [3/3] 推送到 GitHub...
"%GIT%" push origin main
if errorlevel 1 (
    echo.
    echo [错误] 推送失败。请检查：
    echo   1. Clash 代理是否在运行（git 已配置走 127.0.0.1:7897）
    echo   2. GitHub Desktop 是否登录过（用于保存凭据）
    pause
    exit /b 1
)

echo.
echo [成功] 已推送到 GitHub ✓
echo   订阅链接: https://raw.githubusercontent.com/liangzaiZJL/free-clash-nodes/main/output/best-nodes.yaml
pause
exit /b 0
