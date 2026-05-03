# -*- coding: utf-8 -*-
"""
ui/app.py — 主窗口框架
负责窗口初始化、左侧导航栏构建、页面切换管理。
"""

import tkinter as tk
from tkinter import messagebox
from typing import Dict

import config
from database.db_manager import DBManager


class App(tk.Tk):
    """主应用窗口"""

    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        self.minsize(config.MIN_WIDTH, config.MIN_HEIGHT)
        self._center_window()
        self.protocol('WM_DELETE_WINDOW', self._on_close)

        # 存储所有页面 Frame 实例
        self._frames: Dict[str, object] = {}
        self._current_frame_name: str = ''

        # 导航按钮引用，用于切换高亮
        self._nav_buttons: Dict[str, tk.Label] = {}

        self._build_layout()
        self._register_frames()
        self.show_frame('home')

    # ── 布局构建 ──────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """构建左侧导航 + 右侧内容区的两栏布局"""
        # 左侧导航栏
        self._nav_frame = tk.Frame(
            self, bg=config.COLOR_NAV_BG,
            width=config.NAV_WIDTH
        )
        self._nav_frame.pack(side='left', fill='y')
        self._nav_frame.pack_propagate(False)   # 固定宽度

        # 右侧内容区
        self._content_frame = tk.Frame(self, bg=config.COLOR_BG)
        self._content_frame.pack(side='left', fill='both', expand=True)

        self._build_nav()

    def _build_nav(self) -> None:
        """构建导航栏内容"""
        nav = self._nav_frame

        # 应用标题
        tk.Label(
            nav, text='题库练习\n系统',
            font=('Microsoft YaHei', 13, 'bold'),
            fg='#FFFFFF', bg=config.COLOR_NAV_BG,
            pady=20
        ).pack(fill='x')

        # 分隔线
        tk.Frame(nav, height=1, bg='#334155').pack(fill='x', padx=12)

        # 导航菜单项：(显示名, frame名, 图标字符)
        nav_items = [
            ('首  页', 'home',         '⌂'),
            ('导  入', 'import',       '↑'),
            ('考  试', 'exam_setup',   '✎'),
            ('学  习', 'study_setup',  '☰'),
            ('错题本', 'wrong_book',   '✗'),
            ('历  史', 'history',      '◷'),
        ]

        for label, name, icon in nav_items:
            btn = tk.Label(
                nav,
                text=f'  {icon}  {label}',
                font=('Microsoft YaHei', 11),
                fg=config.COLOR_NAV_TEXT,
                bg=config.COLOR_NAV_BG,
                anchor='w', cursor='hand2',
                pady=12, padx=8,
            )
            btn.pack(fill='x')
            self._nav_buttons[name] = btn

            btn.bind('<Button-1>', lambda e, n=name: self.show_frame(n))
            btn.bind('<Enter>',    lambda e, w=btn, n=name: self._nav_hover(w, n, True))
            btn.bind('<Leave>',    lambda e, w=btn, n=name: self._nav_hover(w, n, False))

        # 底部版本号
        tk.Label(
            nav, text=f'v{config.APP_VERSION}',
            font=('Microsoft YaHei', 9),
            fg='#475569', bg=config.COLOR_NAV_BG,
        ).pack(side='bottom', pady=10)

    def _nav_hover(self, widget: tk.Label, name: str, entering: bool) -> None:
        """导航按钮悬停效果（当前选中项不变色）"""
        if name == self._current_frame_name:
            return
        widget.config(bg=config.COLOR_NAV_HOVER if entering else config.COLOR_NAV_BG)

    def _set_nav_active(self, name: str) -> None:
        """高亮当前选中的导航项"""
        for n, btn in self._nav_buttons.items():
            if n == name:
                btn.config(bg=config.COLOR_NAV_ACTIVE, fg='#FFFFFF')
            else:
                btn.config(bg=config.COLOR_NAV_BG, fg=config.COLOR_NAV_TEXT)

    # ── 页面注册与切换 ────────────────────────────────────────────────────────

    def _register_frames(self) -> None:
        """延迟导入并实例化所有页面，避免循环导入"""
        from ui.home_frame        import HomeFrame
        from ui.import_frame      import ImportFrame
        from ui.exam_setup_frame  import ExamSetupFrame
        from ui.study_setup_frame import StudySetupFrame
        from ui.exam_frame        import ExamFrame
        from ui.exam_result_frame import ExamResultFrame
        from ui.study_frame       import StudyFrame
        from ui.wrong_book_frame  import WrongBookFrame
        from ui.history_frame     import HistoryFrame

        frame_classes = {
            'home':         HomeFrame,
            'import':       ImportFrame,
            'exam_setup':   ExamSetupFrame,
            'study_setup':  StudySetupFrame,
            'exam':         ExamFrame,
            'exam_result':  ExamResultFrame,
            'study':        StudyFrame,
            'wrong_book':   WrongBookFrame,
            'history':      HistoryFrame,
        }

        for name, cls in frame_classes.items():
            frame = cls(self._content_frame, self)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._frames[name] = frame

    def show_frame(self, name: str, **kwargs) -> None:
        """
        切换显示指定页面。
        kwargs 会传递给目标页面的 on_show() 方法。
        """
        if self._current_frame_name:
            old = self._frames.get(self._current_frame_name)
            if old:
                old.on_hide()

        frame = self._frames.get(name)
        if frame is None:
            return

        frame.tkraise()
        frame.on_show(**kwargs)
        self._current_frame_name = name
        self._set_nav_active(name)

    # ── 窗口工具 ──────────────────────────────────────────────────────────────

    def _center_window(self) -> None:
        """将窗口居中显示"""
        self.update_idletasks()
        w = int(config.WINDOW_SIZE.split('x')[0])
        h = int(config.WINDOW_SIZE.split('x')[1])
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f'{w}x{h}+{x}+{y}')

    def _on_close(self) -> None:
        """关闭窗口前清理资源"""
        try:
            DBManager.get_instance().close()
        except Exception:
            pass
        self.destroy()
