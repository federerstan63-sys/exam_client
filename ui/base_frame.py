# -*- coding: utf-8 -*-
"""
ui/base_frame.py — 所有页面的基类
提供统一的页面生命周期钩子和公共工具方法。
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.app import App


class BaseFrame(tk.Frame):
    """所有页面 Frame 的基类"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, bg='#F1F5F9')
        self.app = app

    def on_show(self, **kwargs) -> None:
        """每次切换到此页面时调用，子类覆盖以刷新数据"""
        pass

    def on_hide(self) -> None:
        """离开此页面时调用，子类覆盖以清理状态"""
        pass

    # ── 公共工具方法 ──────────────────────────────────────────────────────────

    def make_label(self, parent, text: str, size: int = 11,
                   bold: bool = False, color: str = '#1E293B', **kw) -> tk.Label:
        """创建统一样式的标签"""
        weight = 'bold' if bold else 'normal'
        return tk.Label(
            parent, text=text,
            font=('Microsoft YaHei', size, weight),
            fg=color, bg=kw.pop('bg', parent.cget('bg')),
            **kw
        )

    def make_button(self, parent, text: str, command=None,
                    style: str = 'primary', **kw) -> tk.Button:
        """
        创建统一样式的按钮。
        style: 'primary' | 'danger' | 'secondary'
        """
        colors = {
            'primary':   ('#2563EB', '#FFFFFF'),
            'danger':    ('#DC2626', '#FFFFFF'),
            'secondary': ('#64748B', '#FFFFFF'),
            'success':   ('#16A34A', '#FFFFFF'),
        }
        bg, fg = colors.get(style, colors['primary'])
        btn = tk.Button(
            parent, text=text, command=command,
            font=('Microsoft YaHei', 11),
            bg=bg, fg=fg,
            activebackground=bg, activeforeground=fg,
            relief='flat', cursor='hand2',
            padx=16, pady=6,
            **kw
        )
        # 悬停效果
        def on_enter(e): btn.config(bg=self._darken(bg))
        def on_leave(e): btn.config(bg=bg)
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        return btn

    def make_card(self, parent, **kw) -> tk.Frame:
        """创建白色卡片容器"""
        return tk.Frame(parent, bg='#FFFFFF',
                        relief='flat', bd=1,
                        highlightbackground='#CBD5E1',
                        highlightthickness=1,
                        **kw)

    @staticmethod
    def _darken(hex_color: str) -> str:
        """将十六进制颜色加深约 15%"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, int(r * 0.85))
        g = max(0, int(g * 0.85))
        b = max(0, int(b * 0.85))
        return f'#{r:02x}{g:02x}{b:02x}'

    @staticmethod
    def format_duration(seconds: int) -> str:
        """将秒数格式化为 mm:ss 或 hh:mm:ss"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'
