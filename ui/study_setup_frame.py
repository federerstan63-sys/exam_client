# -*- coding: utf-8 -*-
"""
ui/study_setup_frame.py — 学习模式配置页面
选择题库和分类后进入学习模式。
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from ui.base_frame import BaseFrame
from database.db_manager import DBManager

if TYPE_CHECKING:
    from ui.app import App


class StudySetupFrame(BaseFrame):
    """学习模式配置页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._bank_list = []
        self._build()

    def _build(self) -> None:
        header = tk.Frame(self, bg='#F1F5F9')
        header.pack(fill='x', padx=24, pady=(20, 0))
        self.make_label(header, '学习模式', size=16, bold=True).pack(anchor='w')
        tk.Frame(self, height=1, bg='#CBD5E1').pack(fill='x', padx=24, pady=12)

        outer = tk.Frame(self, bg='#F1F5F9')
        outer.pack(fill='both', expand=True)
        card = self.make_card(outer)
        card.place(relx=0.5, rely=0.5, anchor='center', width=460)

        inner = tk.Frame(card, bg='#FFFFFF')
        inner.pack(fill='both', padx=32, pady=28)

        # 选择题库
        self.make_label(inner, '选择题库', size=11, bold=True, bg='#FFFFFF').grid(
            row=0, column=0, sticky='w', pady=(0, 12))
        self._bank_var = tk.StringVar()
        self._bank_combo = ttk.Combobox(
            inner, textvariable=self._bank_var,
            state='readonly', width=30,
            font=('Microsoft YaHei', 11)
        )
        self._bank_combo.grid(row=0, column=1, sticky='w', padx=(12, 0), pady=(0, 12))
        self._bank_combo.bind('<<ComboboxSelected>>', self._on_bank_change)

        # 选择分类
        self.make_label(inner, '选择分类', size=11, bold=True, bg='#FFFFFF').grid(
            row=1, column=0, sticky='w', pady=(0, 12))
        self._cat_var = tk.StringVar(value='全部')
        self._cat_combo = ttk.Combobox(
            inner, textvariable=self._cat_var,
            state='readonly', width=30,
            font=('Microsoft YaHei', 11)
        )
        self._cat_combo.grid(row=1, column=1, sticky='w', padx=(12, 0), pady=(0, 12))

        # 题库信息
        self._info_label = tk.Label(
            inner, text='', font=('Microsoft YaHei', 9),
            fg='#64748B', bg='#FFFFFF'
        )
        self._info_label.grid(row=2, column=0, columnspan=2, sticky='w', pady=(0, 16))

        # 按钮
        btn_frame = tk.Frame(inner, bg='#FFFFFF')
        btn_frame.grid(row=3, column=0, columnspan=2)
        self.make_button(btn_frame, '取消', lambda: self.app.show_frame('home'),
                         style='secondary').pack(side='left', padx=(0, 12))
        self.make_button(btn_frame, '开始学习', self._start_study,
                         style='primary').pack(side='left')

    def on_show(self, **kwargs) -> None:
        self._load_banks()

    def _load_banks(self) -> None:
        db = DBManager.get_instance()
        rows = db.fetchall(
            'SELECT id, name, question_count FROM question_banks WHERE is_active=1 ORDER BY imported_at DESC'
        )
        self._bank_list = [(r['id'], r['name'], r['question_count']) for r in rows]
        names = [r['name'] for r in rows]
        self._bank_combo['values'] = names
        if names:
            self._bank_combo.current(0)
            self._on_bank_change()

    def _on_bank_change(self, event=None) -> None:
        idx = self._bank_combo.current()
        if idx < 0 or not self._bank_list:
            return
        bank_id, _, count = self._bank_list[idx]
        self._info_label.config(text=f'共 {count} 道题目')

        # 加载该题库的分类列表
        db = DBManager.get_instance()
        rows = db.fetchall(
            "SELECT DISTINCT category FROM questions WHERE bank_id=? AND category != '' ORDER BY category",
            (bank_id,)
        )
        cats = ['全部'] + [r['category'] for r in rows]
        self._cat_combo['values'] = cats
        self._cat_combo.current(0)

    def _start_study(self) -> None:
        idx = self._bank_combo.current()
        if idx < 0 or not self._bank_list:
            messagebox.showwarning('提示', '请先选择题库')
            return
        bank_id, bank_name, _ = self._bank_list[idx]
        category = self._cat_var.get()
        self.app.show_frame('study', bank_id=bank_id, category=category)
