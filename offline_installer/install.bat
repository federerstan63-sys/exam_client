@echo off
:: ============================================================
:: install.bat — 离线环境一键安装脚本
:: 适用：Windows 7/10/11 x64，无网络环境
::
:: 功能：
::   1. 检查 Python 3.10 是否已安装
::   2. 在项目目录创建虚拟环境
::   3. 从本地 wheels 文件夹离线安装所有依赖
::   4. 验证安装结果
::
:: 使用前提：
::   - 已安装 Python 3.10 x64（见 README.md 第一步）
::   - 本脚本与 wheels 文件夹、项目源码放在同一目录结构中
::
:: 目录结构要求：
::   exam_client\
::     offline_installer\
::       install.bat        ← 本脚本
::       wheels\            ← 所有 .whl 文件
::     main.py
::     requirements.txt
::     ...
:: ============================================================

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  离线题库练习系统 — 离线依赖安装工具
echo  适用平台：Windows 7/10/11 x64（无网络环境）
echo ============================================================
echo.

:: ── 定位项目根目录（本脚本的上一级目录）────────────────────
set "SCRIPT_DIR=%~dp0"
:: %~dp0 = 本脚本所在目录（含末尾反斜杠）

set "PROJECT_DIR=%SCRIPT_DIR%.."
:: 上一级即项目根目录（exam_client\）

set "WHEELS_DIR=%SCRIPT_DIR%wheels"
:: wheels 文件夹与本脚本同级

set "VENV_DIR=%PROJECT_DIR%\.venv"
:: 虚拟环境创建在项目根目录下

:: ── 步骤 1：检查 Python ──────────────────────────────────────
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python！
    echo.
    echo 请先安装 Python 3.10 x64：
    echo   安装包文件名：python-3.10.11-amd64.exe
    echo   安装时务必勾选底部的 "Add Python to PATH"
    echo.
    echo 安装完成后，关闭本窗口，重新双击 install.bat
    echo.
    pause
    exit /b 1
)

:: 检查版本是否 >= 3.7（dataclass 需要 3.7+）
python -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] Python 版本过低！
    python --version
    echo 本程序需要 Python 3.7 或以上版本
    echo 请安装 Python 3.10：python-3.10.11-amd64.exe
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] 检测到 %PYVER%
echo.

:: ── 步骤 2：检查 wheels 文件夹 ──────────────────────────────
echo [2/4] 检查离线安装包...
if not exist "%WHEELS_DIR%" (
    echo [错误] 未找到 wheels 文件夹：%WHEELS_DIR%
    echo 请确认 wheels 文件夹与 install.bat 在同一目录下
    pause
    exit /b 1
)

:: 统计 whl 文件数量
set WHL_COUNT=0
for %%f in ("%WHEELS_DIR%\*.whl") do set /a WHL_COUNT+=1

if %WHL_COUNT% EQU 0 (
    echo [错误] wheels 文件夹中没有找到任何 .whl 文件
    pause
    exit /b 1
)

echo [OK] 找到 %WHL_COUNT% 个离线安装包
echo.

:: ── 步骤 3：创建虚拟环境 ────────────────────────────────────
echo [3/4] 创建虚拟环境...
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [跳过] 虚拟环境已存在，直接使用
) else (
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        echo 请确认 Python 安装完整，包含 venv 模块
        pause
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功：%VENV_DIR%
)
echo.

:: ── 步骤 4：离线安装所有依赖 ────────────────────────────────
echo [4/4] 从本地离线安装依赖包...
echo 安装目录：%WHEELS_DIR%
echo.

"%VENV_DIR%\Scripts\pip" install ^
    --no-index ^
    --find-links="%WHEELS_DIR%" ^
    python-docx openpyxl pyinstaller

:: --no-index    : 禁止访问网络（PyPI），只从本地查找
:: --find-links  : 指定本地 wheel 文件夹作为包来源

if errorlevel 1 (
    echo.
    echo [错误] 安装失败！
    echo.
    echo 可能原因：
    echo   1. wheels 文件夹中缺少某个依赖包的 .whl 文件
    echo   2. Python 版本与 .whl 文件不匹配（需要 Python 3.10 x64）
    echo.
    echo 请将错误信息截图发给技术人员处理
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  安装完成！
echo ============================================================
echo.
echo 现在可以：
echo   1. 调试运行程序：双击项目目录中的 run_dev.bat
echo   2. 打包为 .exe ：双击项目目录中的 build_windows.bat
echo.
pause
