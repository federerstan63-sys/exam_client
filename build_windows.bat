@echo off
:: ============================================================
:: build_windows.bat — 一键打包脚本
:: 功能：在 Windows 上将离线题库练习系统打包为单文件 .exe
::
:: 使用前提：
::   1. 已安装 Python 3.7 ~ 3.12（推荐 3.10 或 3.11）
::      下载地址：https://www.python.org/downloads/
::      安装时务必勾选 "Add Python to PATH"
::   2. 能访问互联网（首次运行需要下载依赖包）
::
:: 使用方法：
::   双击本文件，或在命令提示符中运行：build_windows.bat
::
:: 输出结果：
::   dist\ExamClient.exe  ← 单文件可执行程序，可直接分发给用户
:: ============================================================

chcp 65001 >nul
:: chcp 65001：将命令行切换为 UTF-8 编码，防止中文乱码

echo ============================================================
echo  离线题库练习系统 — Windows 打包工具
echo ============================================================
echo.

:: ── 步骤 1：检查 Python 是否已安装 ──────────────────────────
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python！
    echo 请先安装 Python 3.7 或以上版本：
    echo   https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: 检查 Python 版本是否 >= 3.7（dataclass 需要 3.7+）
python -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] Python 版本过低！
    python --version
    echo 本程序需要 Python 3.7 或以上版本（不支持 3.6）
    echo 请升级 Python：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] 检测到 %PYVER%
echo.

:: ── 步骤 2：创建虚拟环境 ─────────────────────────────────────
echo [2/5] 创建虚拟环境 (.venv)...
if exist .venv (
    echo [跳过] 虚拟环境已存在，直接使用
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败，请检查 Python 安装是否完整
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
)
echo.

:: ── 步骤 3：安装依赖 ─────────────────────────────────────────
echo [3/5] 安装依赖包（首次运行需要联网下载，请耐心等待）...
.venv\Scripts\pip install --upgrade pip -q
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败！
    echo 可能原因：
    echo   1. 网络连接问题，请检查网络后重试
    echo   2. pip 版本过旧，已尝试自动升级，请重新运行本脚本
    echo.
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

:: ── 步骤 4：执行打包 ─────────────────────────────────────────
echo [4/5] 正在打包（此步骤需要 1~3 分钟，请勿关闭窗口）...
.venv\Scripts\pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    echo 请查看上方错误信息，或将错误截图发给技术人员处理
    echo.
    pause
    exit /b 1
)
echo [OK] 打包完成
echo.

:: ── 步骤 5：验证输出 ─────────────────────────────────────────
echo [5/5] 验证输出文件...
if exist dist\ExamClient.exe (
    echo [OK] 打包成功！
    echo.
    echo ============================================================
    echo  输出文件：dist\ExamClient.exe
    echo  可以将此文件复制到任意 Windows 电脑直接双击运行
    echo  无需安装 Python 或任何其他软件
    echo ============================================================
    echo.
    :: 询问是否立即测试运行
    set /p RUNTEST=是否立即测试运行？(y/n):
    if /i "%RUNTEST%"=="y" (
        echo 正在启动程序...
        start dist\ExamClient.exe
    )
) else (
    echo [错误] 未找到输出文件 dist\ExamClient.exe
    echo 打包可能未成功完成，请检查上方日志
)

echo.
pause
