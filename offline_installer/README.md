# 离线安装包使用说明

适用场景：Windows 7/10/11 x64，**无网络**环境，需要在本机调试源码并打包为 .exe

---

## 文件夹内容

```
offline_installer\
  install.bat                          ← 一键安装脚本（双击运行）
  README.md                            ← 本文件
  wheels\                              ← 所有依赖的离线安装包（11 个）
    altgraph-0.17.5-py2.py3-none-any.whl
    et_xmlfile-2.0.0-py3-none-any.whl
    lxml-6.1.0-cp310-cp310-win_amd64.whl
    macholib-1.16.4-py2.py3-none-any.whl
    openpyxl-3.1.5-py2.py3-none-any.whl
    packaging-26.2-py3-none-any.whl
    pyinstaller-6.11.1-py3-none-win_amd64.whl
    pyinstaller_hooks_contrib-2026.4-py3-none-any.whl
    python_docx-1.1.2-py3-none-any.whl
    setuptools-82.0.1-py3-none-any.whl
    typing_extensions-4.15.0-py3-none-any.whl
```

**还需要你自行下载的文件（在有网络的电脑上下载，用 U 盘拷过来）：**

| 文件名 | 大小 | 用途 |
|--------|------|------|
| `python-3.10.11-amd64.exe` | 约 27 MB | Python 运行环境 |
| `windows6.1-KB2533623-x64.msu` | 约 600 KB | Win7 必备补丁（仅 Win7 需要） |
| `windows6.1-KB976932-X64.exe` | 约 900 MB | Win7 SP1（仅未装 SP1 的 Win7 需要） |

> Win10/Win11 电脑跳过所有补丁步骤，直接从第二步开始。

---

## 第一步：检查并修复 Win7 系统（仅 Win7 需要）

> **Win10 / Win11 用户跳过此步骤，直接看第二步。**

Python 3.10 要求 Win7 必须安装 SP1 和 KB2533623 补丁，否则安装时会报错：
```
This program is not supported on this operating system.
```

### 1-1 检查是否已安装 SP1

按 `Win + R`，输入 `winver`，回车，查看弹出窗口：

```
┌──────────────────────────────────────────────┐
│  关于 Windows                                │
│                                              │
│  Windows 7 旗舰版                            │
│  版本 6.1 (内部版本 7601)   ← 7601 = 已装SP1 │
│                              7600 = 未装SP1  │
└──────────────────────────────────────────────┘
```

- 显示 **7601**：已安装 SP1，跳到 1-3
- 显示 **7600**：未安装 SP1，需要先装 SP1

---

### 1-2 安装 Win7 SP1（KB976932）

> 仅内部版本为 7600 的电脑需要此步骤。

**下载地址（在有网络的电脑上下载）：**

```
https://catalog.update.microsoft.com/v7/site/Search.aspx?q=KB976932
```

打开上述网址后：
1. 找到 **"Windows 7 Service Pack 1 for x64-based Systems (KB976932)"** 这一行
2. 点击右侧 **Download** 按钮
3. 在弹出窗口中点击文件名链接下载
4. 文件名为 `windows6.1-KB976932-X64.exe`，约 900 MB

**安装步骤：**

1. 双击 `windows6.1-KB976932-X64.exe`
2. 点击「是」允许程序运行
3. 点击「我接受许可条款」→「下一步」
4. 等待安装完成（约 10~30 分钟，期间屏幕可能变黑，属正常现象）
5. 提示重启时，点击「立即重启」
6. 重启后系统会继续完成 SP1 配置，**不要强制关机**，等待自动完成

安装完成后再次运行 `winver`，确认版本号变为 **7601**。

---

### 1-3 安装 KB2533623 补丁

此补丁让 Win7 支持现代 DLL 加载机制，Python 3.10 依赖它。

**下载地址（在有网络的电脑上下载）：**

```
https://catalog.update.microsoft.com/v7/site/Search.aspx?q=KB2533623
```

打开上述网址后：
1. 找到 **"Update for Windows 7 for x64-based Systems (KB2533623)"** 这一行
   （注意选 x64 版本，不要选 x86）
2. 点击右侧 **Download** 按钮下载
3. 文件名为 `windows6.1-KB2533623-x64.msu`，约 600 KB

**安装步骤：**

1. 双击 `windows6.1-KB2533623-x64.msu`
2. 弹出「Windows Update 独立安装程序」窗口，点击「是」

```
┌──────────────────────────────────────────────────┐
│  Windows Update 独立安装程序                      │
│                                                  │
│  是否要安装以下 Windows 软件更新？                │
│  Update for Windows 7 (KB2533623)                │
│                                                  │
│              [是]    [否]                        │
└──────────────────────────────────────────────────┘
```

3. 等待安装完成（约 1~2 分钟）
4. 提示「安装完成」后点击「关闭」
5. **重启电脑**

---

### 1-4 验证补丁安装结果

重启后，打开命令提示符（Win+R → 输入 `cmd` → 回车），输入：

```bat
wmic qfe get HotFixID | findstr "KB2533623"
```

如果输出 `KB2533623`，说明补丁安装成功，可以继续下一步。

---

## 第二步：安装 Python 3.10

**下载地址（在有网络的电脑上下载）：**

```
https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
```

直接将上述地址粘贴到浏览器地址栏，回车即开始下载。文件约 27 MB。

**安装步骤：**

1. 双击 `python-3.10.11-amd64.exe`
2. 看到安装界面后，**先勾选底部的 "Add Python 3.10 to PATH"**，再点击 Install Now

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   [Install Now]                                         │
│   C:\Users\用户名\AppData\Local\Programs\Python\...     │
│                                                         │
│   [Customize installation]                              │
│                                                         │
│   ☑ Install launcher for all users (recommended)       │
│   ☑ Add Python 3.10 to PATH    ← 必须勾选，默认未勾选！ │
└─────────────────────────────────────────────────────────┘
```

3. 等待安装完成（约 1~3 分钟）
4. 看到以下界面即安装成功：

```
┌─────────────────────────────────────────────────────────┐
│   Setup was successful                                  │
│                                                         │
│   Python 3.10.11 (64-bit) was installed successfully.  │
│                                                         │
│   [Disable path length limit]   [Close]                 │
└─────────────────────────────────────────────────────────┘
```

建议点击 **"Disable path length limit"**（解除路径长度限制），然后点 Close。

**验证安装：**

打开命令提示符（Win+R → `cmd` → 回车），输入：

```bat
python --version
```

输出 `Python 3.10.11` 即安装成功。

---

## 第三步：安装 Python 依赖库（离线）

将整个 `exam_client` 文件夹（含 `offline_installer` 子文件夹）拷贝到目标电脑后：

**双击 `offline_installer\install.bat`**

脚本会自动完成：
1. 检查 Python 版本
2. 在项目目录创建虚拟环境（`.venv` 文件夹）
3. 从本地 `wheels` 文件夹离线安装所有依赖
4. 显示安装结果

安装成功后会看到：

```
============================================================
 安装完成！
============================================================

现在可以：
  1. 调试运行程序：双击项目目录中的 run_dev.bat
  2. 打包为 .exe ：双击项目目录中的 build_windows.bat
```

---

## 第四步：调试运行程序

安装完成后，回到 `exam_client` 根目录，**双击 `run_dev.bat`**。

程序窗口弹出即表示运行成功，可以开始调试。

---

## 第五步：打包为 .exe

调试完成、确认功能正常后，**双击 `build_windows.bat`** 进行打包。

打包过程约 1~3 分钟，完成后：

```
============================================================
 输出文件：dist\ExamClient.exe
 可以将此文件复制到任意 Windows 电脑直接双击运行
 无需安装 Python 或任何其他软件
============================================================
```

将 `dist\ExamClient.exe`（约 30~50 MB）通过 U 盘分发给所有同事，双击即用。

---

## 手动安装依赖（备用方案）

如果 `install.bat` 运行失败，可以手动执行。

打开命令提示符（Win+R → `cmd` → 回车），将以下命令逐行输入（将路径替换为实际路径）：

```bat
:: 进入项目目录（根据实际路径修改）
cd /d D:\exam_client

:: 创建虚拟环境
python -m venv .venv

:: 离线安装所有依赖
.venv\Scripts\pip install ^
    --no-index ^
    --find-links=offline_installer\wheels ^
    python-docx openpyxl pyinstaller
```

---

## 完整操作流程总览

```
有网络的电脑（下载文件）
    │
    ├─ 下载 python-3.10.11-amd64.exe
    ├─ 下载 windows6.1-KB2533623-x64.msu   （Win7 必须）
    └─ 下载 windows6.1-KB976932-X64.exe    （Win7 未装SP1时才需要）
    │
    ▼ U盘拷贝
    │
Win7 目标电脑（无网络）
    │
    ├─ [仅Win7] 检查 winver 版本号
    │     7600 → 先装 KB976932(SP1) → 重启 → 再装 KB2533623 → 重启
    │     7601 → 直接装 KB2533623 → 重启
    │
    ├─ 安装 python-3.10.11-amd64.exe
    │     务必勾选 "Add Python 3.10 to PATH"
    │
    ├─ 双击 offline_installer\install.bat
    │     自动创建虚拟环境 + 离线安装依赖
    │
    ├─ 双击 run_dev.bat → 调试程序
    │
    └─ 双击 build_windows.bat → 打包为 dist\ExamClient.exe
              │
              ▼ U盘拷贝
              │
    所有同事电脑（双击 ExamClient.exe 即用）
```

---

## 常见问题

**Q：Win7 安装 Python 时提示 "This program is not supported on this operating system"**

A：系统缺少补丁，按以下顺序处理：
1. 运行 `winver` 查看版本号
2. 版本号为 7600：先安装 SP1（KB976932），重启
3. 安装 KB2533623 补丁，重启
4. 重新安装 Python

---

**Q：KB2533623 安装时提示"此更新不适用于你的计算机"**

A：两种可能：
- 该补丁已经安装过了（运行 `wmic qfe get HotFixID | findstr KB2533623` 验证）
- 下载的是 x86 版本但系统是 x64，重新下载 x64 版本（文件名含 `x64`）

---

**Q：SP1 安装过程中卡住不动超过 1 小时**

A：SP1 安装时间较长，属正常现象。请确保：
- 电脑接通电源，不要断电
- 不要强制重启
- 如果超过 2 小时仍无进展，可尝试重启后再次运行安装包

---

**Q：双击 install.bat 提示"未找到 Python"**

A：Python 安装时没有勾选 "Add Python to PATH"。
解决：重新运行 Python 安装包，选择 **Modify** → 勾选 **"Add Python to environment variables"** → Next → Install。

---

**Q：install.bat 提示"安装失败"**

A：检查 wheels 文件夹中是否有 11 个 .whl 文件，对照本文件开头的文件列表逐一核对，确认没有文件在拷贝过程中丢失或损坏。

---

**Q：安装成功但运行程序时提示"No module named xxx"**

A：确认 `exam_client` 目录下存在 `.venv\Scripts\python.exe` 文件。
如果存在但仍报错，删除 `.venv` 文件夹，重新双击 `install.bat`。

---

**Q：打包时提示"pyinstaller 不是内部或外部命令"**

A：不要直接在命令行输入 `pyinstaller`，请使用项目根目录的 `build_windows.bat` 进行打包。
