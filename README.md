# 离线题库练习系统

版本：1.0.0 | 适用平台：Windows 7 / 10 / 11（打包版）/ macOS（开发版）

---

## 目录

1. [功能概览](#功能概览)
2. [快速开始](#快速开始)
3. [题库文件格式](#题库文件格式)
4. [功能说明](#功能说明)
5. [项目结构](#项目结构)
6. [打包为 .exe](#打包为-exe)
7. [单位批量部署](#单位批量部署)
8. [常见问题](#常见问题)

---

## 功能概览

| 功能 | 说明 |
|------|------|
| 题库导入 | 从 Word (.docx) 或 Excel (.xlsx) 文件导入题目 |
| 考试模式 | 随机组卷、计时、自动评分 |
| 学习模式 | 顺序浏览全部题目，显示答案和解析 |
| 错题本 | 自动记录答错题目，支持标记已掌握、错题专项练习 |
| 历史记录 | 查看历次考试成绩、得分趋势图、答题详情 |
| 题库更新 | 随时导入新题库文件，支持多个题库并存 |

---

## 快速开始

### 方式一：使用打包好的 .exe（推荐，面向最终用户）

直接双击 `ExamClient.exe` 即可运行，**无需安装 Python 或任何其他软件**。

数据文件保存在：`C:\Users\<用户名>\AppData\Roaming\ExamClient\`

> 如何获得 .exe：在 Windows 上运行 `build_windows.bat` 即可自动打包生成。

---

### 方式二：Windows 上直接运行源代码（开发/调试）

**Python 版本要求：3.7 ~ 3.12（不支持 3.6，不支持 3.13 的部分旧依赖）**

> 推荐使用 Python 3.10 或 3.11，兼容性最佳。

双击项目目录中的 `run_dev.bat`，脚本会自动完成以下操作：
1. 检查 Python 版本
2. 创建虚拟环境（首次运行）
3. 安装依赖（首次运行）
4. 启动程序

或手动执行：

```bat
:: 创建虚拟环境（仅首次）
python -m venv .venv

:: 安装依赖
.venv\Scripts\pip install -r requirements.txt

:: 启动程序
.venv\Scripts\python main.py
```

---

### 方式三：macOS 上运行源代码（开发环境）

**Python 版本要求：3.7+（推荐通过 Homebrew 安装 Python 3.13）**

> **注意（macOS）：** 系统中可能同时存在多个 Python 版本。`pip3` 可能指向旧版本（如 3.9），
> 而 `python3` 实际运行的是 3.13。必须使用虚拟环境确保依赖安装到正确的 Python 中。

```bash
# 1. 在项目目录下创建虚拟环境（仅首次需要）
python3 -m venv .venv313

# 2. 安装依赖到虚拟环境
.venv313/bin/pip install -r requirements.txt

# 3. 启动程序
.venv313/bin/python main.py
```

也可以先激活虚拟环境，之后直接使用 `python` / `pip`：

```bash
source .venv313/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 题库文件格式

### Excel 格式（推荐）

文件扩展名：`.xlsx`

**列格式（第一行为表头，从第二行开始填写数据）：**

| 列 | 列名 | 说明 | 是否必填 |
|----|------|------|----------|
| A | 题型 | single / multi / truefalse / scenario | 必填 |
| B | 题干 | 题目内容 | 必填 |
| C | 选项A | 选项文本 | 选择题必填 |
| D | 选项B | 选项文本 | 选择题必填 |
| E | 选项C | 选项文本 | 可选 |
| F | 选项D | 选项文本 | 可选 |
| G | 选项E | 选项文本 | 可选 |
| H | 正确答案 | A / B / AB / True / False | 必填 |
| I | 解析 | 答案解释 | 可选 |
| J | 分类 | 章节/标签 | 可选 |
| K | 难度 | 1（易）/ 2（中）/ 3（难） | 可选 |

**题型填写规则：**

| 题型 | 填写值 | 说明 |
|------|--------|------|
| 单选题 | `single` 或 `单选题` | 答案填单个字母，如 `B` |
| 多选题 | `multi` 或 `多选题` | 答案填多个字母，如 `ABD` |
| 判断题 | `truefalse` 或 `判断题` | 答案填 `True` 或 `False` |
| 场景题 | `scenario` 或 `场景题` | 同单选题 |

**多 Sheet 支持：** 每个 Sheet 代表一个分类，Sheet 名称作为默认分类（若 J 列为空则使用 Sheet 名）。

**示例（Excel 数据行）：**

```
single | Python中定义函数的关键字是？ | class | def | func | function | | B | Python使用def关键字 | 基础语法 | 1
multi  | 以下属于Python内置类型的有？ | list | tuple | dict | array | set | ABCE | array需要import | 数据类型 | 2
truefalse | Python字符串是不可变的。 | | | | | | True | 字符串是不可变类型 | 数据类型 | 1
```

---

### Word 格式

文件扩展名：`.docx`

每道题按固定格式书写，题目之间用**空行**分隔：

```
【单选题】
1. Python中用于定义函数的关键字是？
A. class
B. def
C. func
D. function
答案：B
解析：Python使用def关键字定义函数。
分类：基础语法
难度：1

【多选题】
2. 以下属于Python内置数据类型的有？
A. list
B. tuple
C. dict
D. array
E. set
答案：ABCE
解析：array不是Python内置类型，需要import。
分类：数据类型
难度：2

【判断题】
3. Python中字符串是不可变的。
答案：True
解析：Python字符串是不可变类型，修改字符串会创建新对象。

【场景题】
4. 某系统需要通过姓名快速查找成绩，最适合使用哪种数据结构？
A. list（列表）
B. tuple（元组）
C. dict（字典）
D. set（集合）
答案：C
解析：字典以键值对存储，查找时间复杂度O(1)。
```

**格式说明：**
- 题型标记：`【单选题】` `【多选题】` `【判断题】` `【场景题】` 或 `【情景题】`
- 选项格式：`A.` `A、` `A）` 均可识别
- 答案行：必须以 `答案：` 或 `答案:` 开头
- 解析、分类、难度行均为可选
- 题目之间用空行分隔（或直接跟下一个题型标记）

---

## 功能说明

### 题库导入

1. 点击左侧导航「导入」
2. 点击「浏览文件...」选择 .docx 或 .xlsx 文件
3. 填写题库名称（默认使用文件名）
4. 点击「开始导入」，查看导入日志
5. 导入完成后，题库出现在「已有题库」列表中

**题库更新：** 直接导入新版本文件即可，旧题库不会被覆盖，可在列表中手动删除旧版本。

---

### 考试模式

1. 点击「考试」进入考试设置页面
2. 选择题库、设置题目数量和时间限制
3. 可筛选题型（单选/多选/判断/场景）
4. 点击「开始考试」
5. 答题过程中可标记题目、跳题、查看导航面板
6. 点击「交卷」查看成绩和错题分析

**评分规则：** 每题等分，多选题必须全部选项正确才得分。

---

### 学习模式

1. 点击「学习」进入学习配置页面
2. 选择题库和分类（可选「全部」）
3. 点击「开始学习」
4. 题目显示时自动展示正确答案和解析
5. 使用「上一题」「下一题」或输入题号跳转

---

### 错题本

- 每次考试结束后，答错的题目自动加入错题本
- 同一道题多次答错会累计错误次数
- 点击「标记已掌握」将题目标记为已掌握（可隐藏）
- 点击「开始错题练习」对所有未掌握错题进行专项练习
- 双击题目可查看题目详情和解析

---

### 历史记录

- 显示所有历史考试记录
- 顶部折线图展示得分趋势
- 双击记录可查看该次考试的完整答题详情和解析

---

## 项目结构

```
exam_client/
├── main.py                    # 程序入口
├── config.py                  # 全局配置（路径、颜色、字体等）
├── requirements.txt           # Python 依赖（Python 3.7+ 兼容版本）
├── build.spec                 # PyInstaller 打包配置
├── build_windows.bat          # Windows 一键打包脚本
├── run_dev.bat                # Windows 开发调试运行脚本
├── 示例题库.xlsx              # 示例题库文件
├── 技术文档.md                # 完整技术文档（架构、数据库、打包原理）
├── 使用手册.md                # 面向非技术用户的操作手册
│
├── database/
│   ├── db_manager.py          # SQLite 数据库管理（单例）
│   └── models.py              # 数据模型（dataclass，需 Python 3.7+）
│
├── importer/
│   ├── base_importer.py       # 导入器基类（校验、写库）
│   ├── docx_importer.py       # Word 文件解析
│   └── xlsx_importer.py       # Excel 文件解析
│
├── core/
│   ├── exam_engine.py         # 考试引擎（出题、计时、评分）
│   ├── study_engine.py        # 学习模式引擎
│   └── stats_engine.py        # 统计分析（历史、错题、趋势）
│
├── ui/
│   ├── app.py                 # 主窗口（导航栏、页面切换）
│   ├── base_frame.py          # 页面基类（公共组件方法）
│   ├── home_frame.py          # 首页仪表盘
│   ├── import_frame.py        # 题库导入页面
│   ├── exam_setup_frame.py    # 考试配置页面
│   ├── exam_frame.py          # 考试答题页面
│   ├── exam_result_frame.py   # 考试结果页面
│   ├── study_setup_frame.py   # 学习模式配置页面
│   ├── study_frame.py         # 学习模式页面
│   ├── wrong_book_frame.py    # 错题本页面
│   ├── history_frame.py       # 历史记录页面
│   └── widgets/
│       └── question_widget.py # 题目显示组件（通用）
│
└── data/                      # 运行时自动创建
    ├── exam.db                # SQLite 数据库
    └── app.log                # 运行日志
```

---

## 数据库结构

程序使用 SQLite 数据库，文件位于：
- 开发模式：`exam_client/data/exam.db`
- 打包后（Windows）：`%APPDATA%\ExamClient\exam.db`

| 表名 | 说明 |
|------|------|
| `question_banks` | 题库元数据（名称、来源文件、导入时间） |
| `questions` | 所有题目（题干、选项、答案、解析、分类） |
| `exams` | 考试记录（得分、用时、题数） |
| `exam_answers` | 每次考试的逐题作答记录 |
| `wrong_answers` | 错题本（错误次数、最近答错时间） |
| `app_settings` | 应用设置键值对 |

---

## 打包为 .exe

### 在 Windows 上打包（推荐）

**前提条件：**
- 已安装 Python 3.7 ~ 3.12（推荐 3.10 或 3.11）
- 安装时勾选了「Add Python to PATH」
- 能访问互联网（首次运行需下载依赖）

**一键打包（推荐）：**

双击 `build_windows.bat`，脚本会自动完成所有步骤，输出 `dist\ExamClient.exe`。

**手动打包：**

```bat
:: 1. 创建虚拟环境
python -m venv .venv

:: 2. 安装依赖（含 PyInstaller）
.venv\Scripts\pip install -r requirements.txt

:: 3. 执行打包
.venv\Scripts\pyinstaller build.spec --noconfirm

:: 4. 输出文件
:: dist\ExamClient.exe  ← 单文件可执行程序，可直接分发
```

---

### 在 macOS 上打包为 macOS 应用（本地调试用）

```bash
# 使用虚拟环境中的 PyInstaller
.venv313/bin/pyinstaller build.spec --noconfirm

# 输出文件位于 dist/ExamClient（macOS 可执行文件）
```

**注意事项：**
- 生成 Windows .exe 必须在 Windows 系统上执行，macOS 无法交叉编译
- 如需图标，将 `icon.ico`（Windows）或 `icon.icns`（macOS）放入 `assets/` 目录
- 打包后程序体积约 30–50 MB（含 Python 运行时）

---

## 单位批量部署

适用场景：50 台以上 Windows 电脑，用户无编程基础，各自独立使用。

### 部署步骤

**第一步：在一台 Windows 电脑上打包**

1. 安装 Python 3.10 或 3.11（官网下载，安装时勾选 Add to PATH）
2. 将项目文件夹复制到该电脑
3. 双击 `build_windows.bat`，等待打包完成
4. 获得 `dist\ExamClient.exe`（约 30~50 MB）

**第二步：分发给所有用户**

将 `ExamClient.exe` 通过以下任意方式分发：
- 复制到 U 盘，逐台拷贝到桌面
- 放到共享文件夹，让用户自行复制
- 通过内网文件服务器下载

**第三步：用户使用**

用户双击 `ExamClient.exe` 即可，无需任何安装操作。

### 题库统一分发

1. 制作好题库文件（.xlsx 或 .docx）
2. 将题库文件和 `ExamClient.exe` 一起放在同一个文件夹中分发
3. 用户打开程序后，点击「导入」，选择题库文件导入即可

### 数据独立性

每台电脑的考试数据完全独立，互不影响，保存在各自电脑的：
`C:\Users\<用户名>\AppData\Roaming\ExamClient\exam.db`

---

## 常见问题

**Q: Python 3.6 能运行吗？**
A: 不能。本程序使用了 `dataclass`（Python 3.7 新增特性），最低需要 Python 3.7。推荐使用 3.10 或 3.11。

**Q: Windows 上运行 `pip install` 报错**
A: 使用虚拟环境隔离依赖，避免权限和版本冲突。直接双击 `run_dev.bat` 会自动处理。

**Q: macOS 上运行 `pip install -r requirements.txt` 报错**
A: 系统中存在多个 Python 版本时，`pip3` 可能指向旧版本（如 3.9）。请改用虚拟环境：
```bash
python3 -m venv .venv313
.venv313/bin/pip install -r requirements.txt
.venv313/bin/python main.py
```

**Q: 安装依赖时提示 `externally-managed-environment`**
A: Homebrew 安装的 Python 不允许直接向系统环境安装包。使用虚拟环境即可解决（见上）。

**Q: 导入 Word 文件时提示"缺少依赖 python-docx"**
A: 确认依赖已安装到正确的 Python 环境中。使用虚拟环境后运行 `pip install python-docx`。

**Q: 导入后题目数量为 0**
A: 检查文件格式是否符合规范，特别是答案行是否以 `答案：` 开头，题型标记是否正确。

**Q: 程序启动后界面显示乱码**
A: 确保系统安装了微软雅黑字体（Windows 系统默认已安装）。macOS 上字体会自动回退到系统默认字体，显示正常。

**Q: 数据存在哪里？如何备份？**
A: 开发模式下数据库在项目目录 `data/exam.db`；打包后在 `%APPDATA%\ExamClient\exam.db`（Windows）。直接复制该文件即可备份。

**Q: 如何在多台电脑间同步数据？**
A: 将 `exam.db` 文件复制到另一台电脑的相同路径即可。

**Q: 多选题答案顺序有影响吗？**
A: 没有影响。系统判题时会忽略答案字母的顺序，`AB` 和 `BA` 视为相同答案。


## 目录

1. [功能概览](#功能概览)
2. [快速开始](#快速开始)
3. [题库文件格式](#题库文件格式)
4. [功能说明](#功能说明)
5. [项目结构](#项目结构)
6. [打包为 .exe](#打包为-exe)
7. [常见问题](#常见问题)

---

## 功能概览

| 功能 | 说明 |
|------|------|
| 题库导入 | 从 Word (.docx) 或 Excel (.xlsx) 文件导入题目 |
| 考试模式 | 随机组卷、计时、自动评分 |
| 学习模式 | 顺序浏览全部题目，显示答案和解析 |
| 错题本 | 自动记录答错题目，支持标记已掌握、错题专项练习 |
| 历史记录 | 查看历次考试成绩、得分趋势图、答题详情 |
| 题库更新 | 随时导入新题库文件，支持多个题库并存 |

---

## 快速开始

### 方式一：直接运行（开发/调试）

**环境要求：** Python 3.13（通过 Homebrew 安装）

> **注意（macOS）：** 系统中可能同时存在多个 Python 版本。`pip3` 可能指向旧版本（如 3.9），
> 而 `python3` 实际运行的是 3.13。必须使用虚拟环境确保依赖安装到正确的 Python 中。

```bash
# 1. 在项目目录下创建虚拟环境（仅首次需要）
python3 -m venv .venv313

# 2. 安装依赖到虚拟环境
.venv313/bin/pip install -r requirements.txt

# 3. 启动程序
.venv313/bin/python main.py
```

也可以先激活虚拟环境，之后直接使用 `python` / `pip`：

```bash
source .venv313/bin/activate
pip install -r requirements.txt
python main.py
```

### 方式二：使用打包好的 .exe（Windows 用户）

直接双击 `ExamClient.exe` 即可运行，无需安装 Python。

数据文件保存在：`C:\Users\<用户名>\AppData\Roaming\ExamClient\`

---

## 题库文件格式

### Excel 格式（推荐）

文件扩展名：`.xlsx`

**列格式（第一行为表头，从第二行开始填写数据）：**

| 列 | 列名 | 说明 | 是否必填 |
|----|------|------|----------|
| A | 题型 | single / multi / truefalse / scenario | 必填 |
| B | 题干 | 题目内容 | 必填 |
| C | 选项A | 选项文本 | 选择题必填 |
| D | 选项B | 选项文本 | 选择题必填 |
| E | 选项C | 选项文本 | 可选 |
| F | 选项D | 选项文本 | 可选 |
| G | 选项E | 选项文本 | 可选 |
| H | 正确答案 | A / B / AB / True / False | 必填 |
| I | 解析 | 答案解释 | 可选 |
| J | 分类 | 章节/标签 | 可选 |
| K | 难度 | 1（易）/ 2（中）/ 3（难） | 可选 |

**题型填写规则：**

| 题型 | 填写值 | 说明 |
|------|--------|------|
| 单选题 | `single` 或 `单选题` | 答案填单个字母，如 `B` |
| 多选题 | `multi` 或 `多选题` | 答案填多个字母，如 `ABD` |
| 判断题 | `truefalse` 或 `判断题` | 答案填 `True` 或 `False` |
| 场景题 | `scenario` 或 `场景题` | 同单选题 |

**多 Sheet 支持：** 每个 Sheet 代表一个分类，Sheet 名称作为默认分类（若 J 列为空则使用 Sheet 名）。

**示例（Excel 数据行）：**

```
single | Python中定义函数的关键字是？ | class | def | func | function | | B | Python使用def关键字 | 基础语法 | 1
multi  | 以下属于Python内置类型的有？ | list | tuple | dict | array | set | ABCE | array需要import | 数据类型 | 2
truefalse | Python字符串是不可变的。 | | | | | | True | 字符串是不可变类型 | 数据类型 | 1
```

---

### Word 格式

文件扩展名：`.docx`

每道题按固定格式书写，题目之间用**空行**分隔：

```
【单选题】
1. Python中用于定义函数的关键字是？
A. class
B. def
C. func
D. function
答案：B
解析：Python使用def关键字定义函数。
分类：基础语法
难度：1

【多选题】
2. 以下属于Python内置数据类型的有？
A. list
B. tuple
C. dict
D. array
E. set
答案：ABCE
解析：array不是Python内置类型，需要import。
分类：数据类型
难度：2

【判断题】
3. Python中字符串是不可变的。
答案：True
解析：Python字符串是不可变类型，修改字符串会创建新对象。

【场景题】
4. 某系统需要通过姓名快速查找成绩，最适合使用哪种数据结构？
A. list（列表）
B. tuple（元组）
C. dict（字典）
D. set（集合）
答案：C
解析：字典以键值对存储，查找时间复杂度O(1)。
```

**格式说明：**
- 题型标记：`【单选题】` `【多选题】` `【判断题】` `【场景题】` 或 `【情景题】`
- 选项格式：`A.` `A、` `A）` 均可识别
- 答案行：必须以 `答案：` 或 `答案:` 开头
- 解析、分类、难度行均为可选
- 题目之间用空行分隔（或直接跟下一个题型标记）

---

## 功能说明

### 题库导入

1. 点击左侧导航「导入」
2. 点击「浏览文件...」选择 .docx 或 .xlsx 文件
3. 填写题库名称（默认使用文件名）
4. 点击「开始导入」，查看导入日志
5. 导入完成后，题库出现在「已有题库」列表中

**题库更新：** 直接导入新版本文件即可，旧题库不会被覆盖，可在列表中手动删除旧版本。

---

### 考试模式

1. 点击「考试」进入考试设置页面
2. 选择题库、设置题目数量和时间限制
3. 可筛选题型（单选/多选/判断/场景）
4. 点击「开始考试」
5. 答题过程中可标记题目、跳题、查看导航面板
6. 点击「交卷」查看成绩和错题分析

**评分规则：** 每题等分，多选题必须全部选项正确才得分。

---

### 学习模式

1. 点击「学习」进入学习配置页面
2. 选择题库和分类（可选「全部」）
3. 点击「开始学习」
4. 题目显示时自动展示正确答案和解析
5. 使用「上一题」「下一题」或输入题号跳转

---

### 错题本

- 每次考试结束后，答错的题目自动加入错题本
- 同一道题多次答错会累计错误次数
- 点击「标记已掌握」将题目标记为已掌握（可隐藏）
- 点击「开始错题练习」对所有未掌握错题进行专项练习
- 双击题目可查看题目详情和解析

---

### 历史记录

- 显示所有历史考试记录
- 顶部折线图展示得分趋势
- 双击记录可查看该次考试的完整答题详情和解析

---

## 项目结构

```
exam_client/
├── main.py                    # 程序入口
├── config.py                  # 全局配置（路径、颜色、字体等）
├── requirements.txt           # Python 依赖
├── build.spec                 # PyInstaller 打包配置
├── 示例题库.xlsx              # 示例题库文件
│
├── database/
│   ├── db_manager.py          # SQLite 数据库管理（单例）
│   └── models.py              # 数据模型（dataclass）
│
├── importer/
│   ├── base_importer.py       # 导入器基类（校验、写库）
│   ├── docx_importer.py       # Word 文件解析
│   └── xlsx_importer.py       # Excel 文件解析
│
├── core/
│   ├── exam_engine.py         # 考试引擎（出题、计时、评分）
│   ├── study_engine.py        # 学习模式引擎
│   └── stats_engine.py        # 统计分析（历史、错题、趋势）
│
├── ui/
│   ├── app.py                 # 主窗口（导航栏、页面切换）
│   ├── base_frame.py          # 页面基类（公共组件方法）
│   ├── home_frame.py          # 首页仪表盘
│   ├── import_frame.py        # 题库导入页面
│   ├── exam_setup_frame.py    # 考试配置页面
│   ├── exam_frame.py          # 考试答题页面
│   ├── exam_result_frame.py   # 考试结果页面
│   ├── study_setup_frame.py   # 学习模式配置页面
│   ├── study_frame.py         # 学习模式页面
│   ├── wrong_book_frame.py    # 错题本页面
│   ├── history_frame.py       # 历史记录页面
│   └── widgets/
│       └── question_widget.py # 题目显示组件（通用）
│
└── data/                      # 运行时自动创建
    ├── exam.db                # SQLite 数据库
    └── app.log                # 运行日志
```

---

## 数据库结构

程序使用 SQLite 数据库，文件位于：
- 开发模式：`exam_client/data/exam.db`
- 打包后：`%APPDATA%\ExamClient\exam.db`

| 表名 | 说明 |
|------|------|
| `question_banks` | 题库元数据（名称、来源文件、导入时间） |
| `questions` | 所有题目（题干、选项、答案、解析、分类） |
| `exams` | 考试记录（得分、用时、题数） |
| `exam_answers` | 每次考试的逐题作答记录 |
| `wrong_answers` | 错题本（错误次数、最近答错时间） |
| `app_settings` | 应用设置键值对 |

---

## 打包为 .exe

### 在 macOS 上交叉编译（当前环境）

macOS 上的 PyInstaller 只能生成 macOS 可执行文件，无法直接生成 Windows .exe。
要生成 Windows 可执行文件，需要在 Windows 系统上执行打包，或使用 GitHub Actions 等 CI 工具。

**推荐方式：在 Windows 上打包**

```bat
:: 1. 安装依赖（含 PyInstaller）
python -m pip install -r requirements.txt

:: 2. 执行打包
pyinstaller build.spec

:: 3. 输出文件
:: dist\ExamClient.exe  ← 单文件可执行程序，可直接分发
```

### 在 macOS 上打包为 macOS 应用（本地调试用）

```bash
# 使用虚拟环境中的 PyInstaller
.venv313/bin/pyinstaller build.spec

# 输出文件位于 dist/ExamClient（macOS 可执行文件）
```

**注意事项：**
- 生成 Windows .exe 必须在 Windows 系统上执行
- 如需图标，将 `icon.ico`（Windows）或 `icon.icns`（macOS）放入 `assets/` 目录
- 打包后程序体积约 30–50 MB（含 Python 运行时）
- 依赖版本要求 Python 3.13：`python-docx>=1.1.2`、`openpyxl>=3.1.5`、`pyinstaller>=6.10.0`

---

## 常见问题

**Q: macOS 上运行 `pip install -r requirements.txt` 报错**
A: 系统中存在多个 Python 版本时，`pip3` 可能指向旧版本（如 3.9）。请改用虚拟环境：
```bash
python3 -m venv .venv313
.venv313/bin/pip install -r requirements.txt
.venv313/bin/python main.py
```

**Q: 安装依赖时提示 `externally-managed-environment`**
A: Homebrew 安装的 Python 不允许直接向系统环境安装包。使用虚拟环境即可解决（见上）。

**Q: 导入 Word 文件时提示"缺少依赖 python-docx"**
A: 确认依赖已安装到正确的 Python 环境中。使用虚拟环境后运行 `.venv313/bin/pip install python-docx`。

**Q: 导入后题目数量为 0**
A: 检查文件格式是否符合规范，特别是答案行是否以 `答案：` 开头，题型标记是否正确。

**Q: 程序启动后界面显示乱码**
A: 确保系统安装了微软雅黑字体（Windows 系统默认已安装）。macOS 上字体会自动回退到系统默认字体，显示正常。

**Q: 数据存在哪里？如何备份？**
A: 开发模式下数据库在项目目录 `data/exam.db`；打包后在 `%APPDATA%\ExamClient\exam.db`（Windows）。直接复制该文件即可备份。

**Q: 如何在多台电脑间同步数据？**
A: 将 `exam.db` 文件复制到另一台电脑的相同路径即可。

**Q: 多选题答案顺序有影响吗？**
A: 没有影响。系统判题时会忽略答案字母的顺序，`AB` 和 `BA` 视为相同答案。
