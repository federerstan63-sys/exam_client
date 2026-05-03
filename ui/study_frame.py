# -*- coding: utf-8 -*-
"""
ui/study_frame.py — 学习模式页面
顺序浏览题目，显示答案和解析，支持分类筛选和跳题。
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional

from ui.base_frame import BaseFrame
from ui.widgets.question_widget import QuestionWidget
from core.study_engine import StudyEngine

if TYPE_CHECKING:
    from ui.app import App


class StudyFrame(BaseFrame):
    """学习模式页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._engine: Optional[StudyEngine] = None
        self._q_widget: Optional[QuestionWidget] = None
        self._build()

    def _build(self) -> None:
        # ── 顶部工具栏 ────────────────────────────────────────────────────────
        top = tk.Frame(self, bg='#1E293B', height=52)
        top.pack(fill='x')
        top.pack_propagate(False)

        tk.Label(top, text='学习模式',
                 font=('Microsoft YaHei', 12, 'bold'),
                 fg='#FFFFFF', bg='#1E293B').pack(side='left', padx=16)

        # 分类下拉
        tk.Label(top, text='分类：',
                 font=('Microsoft YaHei', 10),
                 fg='#94A3B8', bg='#1E293B').pack(side='left')
        self._cat_var = tk.StringVar(value='全部')
        self._cat_combo = ttk.Combobox(
            top, textvariable=self._cat_var,
            state='readonly', width=16,
            font=('Microsoft YaHei', 10)
        )
        self._cat_combo.pack(side='left', padx=(0, 16))
        self._cat_combo.bind('<<ComboboxSelected>>', self._on_cat_change)

        # 题目进度
        self._progress_label = tk.Label(
            top, text='第 1 / 1 题',
            font=('Microsoft YaHei', 11),
            fg='#FFFFFF', bg='#1E293B'
        )
        self._progress_label.pack(side='right', padx=16)

        # 返回按钮
        back_btn = tk.Label(
            top, text='← 返回',
            font=('Microsoft YaHei', 10),
            fg='#94A3B8', bg='#1E293B',
            cursor='hand2', padx=8
        )
        back_btn.pack(side='right')
        back_btn.bind('<Button-1>', lambda e: self.app.show_frame('study_setup'))

        # ── 题目显示区（可滚动）────────────────────────────────────────────────
        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True, padx=24, pady=16)

        # Canvas + Scrollbar 实现题目区域滚动
        self._canvas = tk.Canvas(body, bg='#FFFFFF', highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self._q_inner = tk.Frame(self._canvas, bg='#FFFFFF')
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._q_inner, anchor='nw'
        )
        self._q_inner.bind('<Configure>',
                           lambda e: self._canvas.configure(scrollregion=self._canvas.bbox('all')))
        self._canvas.bind('<Configure>',
                          lambda e: self._canvas.itemconfig(self._canvas_win, width=e.width))

        # ── 底部导航按钮 ──────────────────────────────────────────────────────
        nav = tk.Frame(self, bg='#F1F5F9')
        nav.pack(fill='x', padx=24, pady=(0, 16))

        self.make_button(nav, '◀ 上一题', self._prev, style='secondary').pack(side='left')

        # 跳转输入框
        jump_frame = tk.Frame(nav, bg='#F1F5F9')
        jump_frame.pack(side='left', padx=16)
        tk.Label(jump_frame, text='跳转到第',
                 font=('Microsoft YaHei', 10), bg='#F1F5F9').pack(side='left')
        self._jump_var = tk.StringVar()
        tk.Entry(jump_frame, textvariable=self._jump_var,
                 font=('Microsoft YaHei', 10), width=5,
                 relief='solid', bd=1).pack(side='left', padx=4)
        tk.Label(jump_frame, text='题',
                 font=('Microsoft YaHei', 10), bg='#F1F5F9').pack(side='left')
        self.make_button(jump_frame, '跳转', self._jump, style='secondary').pack(side='left', padx=(4, 0))

        self.make_button(nav, '下一题 ▶', self._next, style='primary').pack(side='right')

    # ── 页面生命周期 ──────────────────────────────────────────────────────────

    def on_show(self, bank_id: int = 0, category: str = '全部', **kwargs) -> None:
        self._engine = StudyEngine(bank_id, category if category != '全部' else None)

        if self._engine.get_total() == 0:
            # 没有题目时返回配置页
            from tkinter import messagebox
            messagebox.showwarning('提示', '该题库/分类下没有题目')
            self.app.show_frame('study_setup')
            return

        # 加载分类列表
        cats = ['全部'] + self._engine.get_categories()
        self._cat_combo['values'] = cats
        self._cat_var.set(category)

        self._show_current()

    # ── 显示题目 ──────────────────────────────────────────────────────────────

    def _show_current(self) -> None:
        """渲染当前题目"""
        if not self._engine:
            return
        q = self._engine.get_current()
        if not q:
            return

        # 清空旧组件
        for w in self._q_inner.winfo_children():
            w.destroy()

        # 创建题目组件（学习模式始终显示答案）
        self._q_widget = QuestionWidget(
            self._q_inner, q,
            show_answer=True,
            bg='#FFFFFF'
        )
        self._q_widget.pack(fill='both', expand=True, padx=24, pady=20)

        # 更新进度
        idx   = self._engine.get_current_index()
        total = self._engine.get_total()
        self._progress_label.config(text=f'第 {idx + 1} / {total} 题')
        self._jump_var.set(str(idx + 1))

        # 重置滚动
        self._canvas.yview_moveto(0)

    # ── 导航操作 ──────────────────────────────────────────────────────────────

    def _prev(self) -> None:
        if self._engine:
            self._engine.prev()
            self._show_current()

    def _next(self) -> None:
        if self._engine:
            self._engine.next()
            self._show_current()

    def _jump(self) -> None:
        if not self._engine:
            return
        try:
            num = int(self._jump_var.get())
            self._engine.jump_to(num - 1)   # 转为 0-based
            self._show_current()
        except ValueError:
            pass

    def _on_cat_change(self, event=None) -> None:
        """切换分类"""
        if not self._engine:
            return
        cat = self._cat_var.get()
        self._engine.reload(cat if cat != '全部' else None)
        self._show_current()
