# -*- coding: utf-8 -*-
"""
config.py — 全局配置常量
包含路径、UI 样式、字体等所有可调参数，集中管理方便后期修改。
"""

import os   # os 模块：提供操作系统相关功能，如路径拼接、目录创建
import sys  # sys 模块：提供 Python 解释器相关信息，如是否被 PyInstaller 打包


def get_app_data_dir() -> str:
    """
    获取用户数据目录（存放数据库和日志文件的位置）。

    判断逻辑：
      - 如果程序被 PyInstaller 打包成 .exe，则使用系统的 %APPDATA% 目录
        （Windows 上通常是 C:/Users/用户名/AppData/Roaming/ExamClient）
      - 如果是开发环境直接运行 .py，则使用项目根目录下的 data/ 子目录

    返回值：str — 数据目录的绝对路径（目录不存在时会自动创建）
    """
    if getattr(sys, 'frozen', False):
        # getattr(sys, 'frozen', False)：
        #   PyInstaller 打包后会在 sys 对象上设置 frozen=True 属性
        #   开发环境中该属性不存在，getattr 返回默认值 False
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        # os.environ.get('APPDATA', ...)：读取环境变量 APPDATA
        #   如果不存在（非 Windows），则回退到用户主目录 ~
        # os.path.expanduser('~')：将 ~ 展开为当前用户的主目录路径
        path = os.path.join(base, 'ExamClient')
        # os.path.join：跨平台拼接路径，自动处理 / 和 \ 的差异
    else:
        # 开发环境：数据存在项目根目录的 data/ 下
        # os.path.abspath(__file__)：获取当前文件（config.py）的绝对路径
        # os.path.dirname(...)：取路径的目录部分（即项目根目录）
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    os.makedirs(path, exist_ok=True)
    # os.makedirs：递归创建目录（包括所有中间层目录）
    # exist_ok=True：如果目录已存在则不报错，直接跳过
    return path


# ── 路径 ──────────────────────────────────────────────────────────────────────
APP_DATA_DIR = get_app_data_dir()                        # 数据根目录（绝对路径）
DB_PATH      = os.path.join(APP_DATA_DIR, 'exam.db')    # SQLite 数据库文件路径
LOG_PATH     = os.path.join(APP_DATA_DIR, 'app.log')    # 日志文件路径

# ── 窗口 ──────────────────────────────────────────────────────────────────────
APP_TITLE    = '离线题库练习系统'   # 窗口标题栏文字
WINDOW_SIZE  = '1100x720'          # 初始窗口尺寸，格式为 "宽x高"（像素）
MIN_WIDTH    = 900                 # 窗口最小宽度（像素），防止界面被压缩变形
MIN_HEIGHT   = 600                 # 窗口最小高度（像素）
NAV_WIDTH    = 150                 # 左侧导航栏固定宽度（像素）

# ── 字体 ──────────────────────────────────────────────────────────────────────
# 优先使用微软雅黑（Windows 内置中文字体），macOS/Linux 会回退到系统默认字体
FONT_FAMILY       = 'Microsoft YaHei'  # 字体族名称
FONT_SIZE_SMALL   = 10                 # 小号字体（提示文字、版本号等）
FONT_SIZE_NORMAL  = 11                 # 正常字体（正文、按钮等）
FONT_SIZE_LARGE   = 13                 # 大号字体（副标题等）
FONT_SIZE_TITLE   = 16                 # 标题字体（页面大标题）

# ── 颜色（十六进制 RGB 色值）──────────────────────────────────────────────────
COLOR_PRIMARY      = '#2563EB'  # 主色调：蓝色，用于主要按钮、高亮等
COLOR_PRIMARY_DARK = '#1D4ED8'  # 主色深色版：鼠标悬停时的按钮颜色
COLOR_SUCCESS      = '#16A34A'  # 成功色：绿色，用于正确答案、成功提示
COLOR_DANGER       = '#DC2626'  # 危险色：红色，用于错误答案、删除按钮
COLOR_WARNING      = '#D97706'  # 警告色：橙色，用于标记题目、警告提示
COLOR_BG           = '#F1F5F9'  # 页面背景色：浅灰蓝，整体背景
COLOR_CARD         = '#FFFFFF'  # 卡片背景色：纯白，内容卡片
COLOR_BORDER       = '#CBD5E1'  # 边框颜色：浅灰，分隔线和卡片边框
COLOR_TEXT         = '#1E293B'  # 主文字颜色：深蓝灰，正文
COLOR_TEXT_MUTED   = '#64748B'  # 次要文字颜色：中灰，提示文字
COLOR_NAV_BG       = '#1E293B'  # 导航栏背景色：深蓝灰
COLOR_NAV_TEXT     = '#CBD5E1'  # 导航栏文字颜色：浅灰
COLOR_NAV_ACTIVE   = '#2563EB'  # 导航栏当前选中项背景色：蓝色
COLOR_NAV_HOVER    = '#334155'  # 导航栏鼠标悬停背景色：稍浅的深蓝灰

# ── 考试默认参数 ───────────────────────────────────────────────────────────────
DEFAULT_QUESTION_COUNT = 50   # 默认出题数量（用户可在考试设置页修改）
DEFAULT_TIME_LIMIT_MIN = 60   # 默认时间限制（分钟），0 表示无限制

# ── 版本 ──────────────────────────────────────────────────────────────────────
APP_VERSION = '1.0.0'  # 应用版本号，显示在导航栏底部
