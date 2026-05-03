# -*- coding: utf-8 -*-
"""
ui/exam_setup_frame.py — 考试配置页面
用户在此选择题库、题目数量、时间限制、题型筛选等参数后开始考试。
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, List

from ui.base_frame import BaseFrame
from database.db_manager import DBManager

if TYPE_CHECKING:
    from ui.app import App


class ExamSetupFrame(BaseFrame):
    """考试配置页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._bank_list = []   # [(id, name, count), ...]
        self._build()

    def _build(self) -> None:
        # 页面标题
        header = tk.Frame(self, bg='#F1F5F9')
        header.pack(fill='x', padx=24, pady=(20, 0))
        self.make_label(header, '考试设置', size=16, bold=True).pack(anchor='w')
        tk.Frame(self, height=1, bg='#CBD5E1').pack(fill='x', padx=24, pady=12)

        # 居中卡片容器
        outer = tk.Frame(self, bg='#F1F5F9')
        outer.pack(fill='both', expand=True)
        card = self.make_card(outer)
        card.place(relx=0.5, rely=0.5, anchor='center', width=520)

        inner = tk.Frame(card, bg='#FFFFFF')
        inner.pack(fill='both', padx=32, pady=28)

        # ── 选择题库 ──────────────────────────────────────────────────────────
        self.make_label(inner, '选择题库', size=11, bold=True, bg='#FFFFFF').grid(
            row=0, column=0, sticky='w', pady=(0, 6))
        self._bank_var = tk.StringVar()
        self._bank_combo = ttk.Combobox(
            inner, textvariable=self._bank_var,
            state='readonly', width=36,
            font=('Microsoft YaHei', 11)
        )
        self._bank_combo.grid(row=0, column=1, sticky='w', pady=(0, 6), padx=(12, 0))
        self._bank_combo.bind('<<ComboboxSelected>>', self._on_bank_change)

        # 题库信息提示
        self._bank_info = tk.Label(
            inner, text='', font=('Microsoft YaHei', 9),
            fg='#64748B', bg='#FFFFFF'
        )
        self._bank_info.grid(row=1, column=1, sticky='w', padx=(12, 0), pady=(0, 12))

        # ── 题目数量 ──────────────────────────────────────────────────────────
        self.make_label(inner, '题目数量', size=11, bold=True, bg='#FFFFFF').grid(
            row=2, column=0, sticky='w', pady=(0, 12))
        count_frame = tk.Frame(inner, bg='#FFFFFF')
        count_frame.grid(row=2, column=1, sticky='w', padx=(12, 0), pady=(0, 12))
        self._count_var = tk.StringVar(value='50')
        tk.Entry(
            count_frame, textvariable=self._count_var,
            font=('Microsoft YaHei', 11), width=8,
            relief='solid', bd=1
        ).pack(side='left')
        self._max_label = tk.Label(
            count_frame, text='（最多: --）',
            font=('Microsoft YaHei', 9), fg='#64748B', bg='#FFFFFF'
        )
        self._max_label.pack(side='left', padx=(8, 0))

        # ── 时间限制 ──────────────────────────────────────────────────────────
        self.make_label(inner, '时间限制', size=11, bold=True, bg='#FFFFFF').grid(
            row=3, column=0, sticky='w', pady=(0, 12))
        time_frame = tk.Frame(inner, bg='#FFFFFF')
        time_frame.grid(row=3, column=1, sticky='w', padx=(12, 0), pady=(0, 12))
        self._time_mode = tk.StringVar(value='limit')
        tk.Radiobutton(
            time_frame, text='无限制', variable=self._time_mode, value='none',
            font=('Microsoft YaHei', 11), bg='#FFFFFF',
            command=self._on_time_mode_change
        ).pack(side='left')
        tk.Radiobutton(
            time_frame, text='自定义', variable=self._time_mode, value='limit',
            font=('Microsoft YaHei', 11), bg='#FFFFFF',
            command=self._on_time_mode_change
        ).pack(side='left', padx=(12, 0))
        self._time_var = tk.StringVar(value='60')
        self._time_entry = tk.Entry(
            time_frame, textvariable=self._time_var,
            font=('Microsoft YaHei', 11), width=6,
            relief='solid', bd=1
        )
        self._time_entry.pack(side='left', padx=(8, 0))
        tk.Label(time_frame, text='分钟', font=('Microsoft YaHei', 11),
                 bg='#FFFFFF').pack(side='left', padx=(4, 0))

        # ── 题型筛选 ──────────────────────────────────────────────────────────
        self.make_label(inner, '题型筛选', size=11, bold=True, bg='#FFFFFF').grid(
            row=4, column=0, sticky='nw', pady=(0, 12))
        type_frame = tk.Frame(inner, bg='#FFFFFF')
        type_frame.grid(row=4, column=1, sticky='w', padx=(12, 0), pady=(0, 12))
        self._type_vars = {
            'single':    tk.BooleanVar(value=True),
            'multi':     tk.BooleanVar(value=True),
            'truefalse': tk.BooleanVar(value=True),
            'scenario':  tk.BooleanVar(value=True),
        }
        type_labels = {'single': '单选题', 'multi': '多选题',
                       'truefalse': '判断题', 'scenario': '场景题'}
        for i, (key, var) in enumerate(self._type_vars.items()):
            tk.Checkbutton(
                type_frame, text=type_labels[key], variable=var,
                font=('Microsoft YaHei', 11), bg='#FFFFFF'
            ).grid(row=i // 2, column=i % 2, sticky='w', padx=(0, 16))

        # ── 操作按钮 ──────────────────────────────────────────────────────────
        btn_frame = tk.Frame(inner, bg='#FFFFFF')
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(16, 0))
        self.make_button(btn_frame, '取消', lambda: self.app.show_frame('home'),
                         style='secondary').pack(side='left', padx=(0, 12))
        self.make_button(btn_frame, '开始考试', self._start_exam,
                         style='primary').pack(side='left')

    def on_show(self, **kwargs) -> None:
        self._load_banks()

    def _load_banks(self) -> None:
        """加载题库下拉列表"""
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
        """题库切换时更新题目数量上限提示"""
        idx = self._bank_combo.current()
        if 0 <= idx < len(self._bank_list):
            _, _, count = self._bank_list[idx]
            self._max_label.config(text=f'（最多: {count}）')
            self._bank_info.config(text=f'共 {count} 道题目')
            # 自动调整默认题数不超过上限
            try:
                cur = int(self._count_var.get())
                if cur > count:
                    self._count_var.set(str(count))
            except ValueError:
                pass

    def _on_time_mode_change(self) -> None:
        """切换时间限制模式"""
        if self._time_mode.get() == 'none':
            self._time_entry.config(state='disabled')
        else:
            self._time_entry.config(state='normal')

    def _start_exam(self) -> None:
        """校验参数后跳转到考试页面"""
        idx = self._bank_combo.current()
        if idx < 0 or not self._bank_list:
            messagebox.showwarning('提示', '请先选择题库')
            return

        bank_id, bank_name, max_count = self._bank_list[idx]

        try:
            count = int(self._count_var.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning('提示', '题目数量必须是正整数')
            return

        if count > max_count:
            messagebox.showwarning('提示', f'题目数量不能超过题库总题数 {max_count}')
            return

        time_limit = None
        if self._time_mode.get() == 'limit':
            try:
                minutes = int(self._time_var.get())
                if minutes <= 0:
                    raise ValueError
                time_limit = minutes * 60
            except ValueError:
                messagebox.showwarning('提示', '时间限制必须是正整数（分钟）')
                return

        # 获取选中的题型
        q_types = [k for k, v in self._type_vars.items() if v.get()]
        if not q_types:
            messagebox.showwarning('提示', '请至少选择一种题型')
            return

        self.app.show_frame('exam', bank_id=bank_id, question_count=count,
                            time_limit=time_limit, q_types=q_types)
