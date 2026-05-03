@echo off
:: ============================================================
:: run_dev.bat — 开发调试运行脚本
:: 功能：在 Windows 上直接运行源代码（无需打包），用于开发和调试
::
:: 与 build_windows.bat 的区别：
::   - 本脚本：直接运行 Python 源代码，修改代码后立即生效
::   - build_windows.bat：打包为 .exe，分发给最终用户使用
::
:: 使用方法：双击本文件，或在命令提示符中运行：run_dev.bat
:: ============================================================

chcp 65001 >nul

echo ============================================================
echo  离线题库练习系统 — 开发调试模式
echo ============================================================
echo.

:: ── 检查 Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先运行 build_windows.bat 完成环境配置
    pause
    exit /b 1
)

:: ── 检查虚拟环境 ─────────────────────────────────────────────
if not exist .venv\Scripts\python.exe (
    echo [提示] 虚拟环境不存在，正在自动创建并安装依赖...
    echo 首次运行需要联网下载，请耐心等待...
    echo.
    python -m venv .venv
    .venv\Scripts\pip install --upgrade pip -q
    .venv\Scripts\pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [OK] 环境准备完成
    echo.
)

:: ── 启动程序 ─────────────────────────────────────────────────
echo 正在启动程序（源代码模式）...
echo 日志输出如下：
echo ────────────────────────────────────────────────────────────
.venv\Scripts\python main.py
echo ────────────────────────────────────────────────────────────
echo.
echo 程序已退出
pause
