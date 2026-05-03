# -*- coding: utf-8 -*-
"""
ui/home_frame.py — 首页/仪表盘
显示题库总览统计和最近考试记录。
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ui.base_frame import BaseFrame
from core.stats_engine import StatsEngine

if TYPE_CHECKING:
    from ui.app import App


class HomeFrame(BaseFrame):
    """首页仪表盘"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._build()

    def _build(self) -> None:
        # 顶部标题区
        header = tk.Frame(self, bg='#2563EB', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(
            header, text='欢迎使用离线题库练习系统',
            font=('Microsoft YaHei', 16, 'bold'),
            fg='#FFFFFF', bg='#2563EB'
        ).pack(expand=True)

        # 主内容区（带内边距）
        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True, padx=24, pady=20)

        # 统计卡片行
        self._stat_frame = tk.Frame(body, bg='#F1F5F9')
        self._stat_frame.pack(fill='x', pady=(0, 20))

        # 最近考试标题
        self.make_label(body, '最近考试记录', size=13, bold=True).pack(anchor='w', pady=(0, 8))

        # 考试历史表格
        cols = ('日期', '题库', '题数', '得分', '用时')
        self._tree = ttk.Treeview(body, columns=cols, show='headings', height=8)
        for col in cols:
            self._tree.heading(col, text=col)
        self._tree.column('日期', width=160)
        self._tree.column('题库', width=200)
        self._tree.column('题数', width=80,  anchor='center')
        self._tree.column('得分', width=80,  anchor='center')
        self._tree.column('用时', width=100, anchor='center')

        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        # 底部按钮行
        btn_frame = tk.Frame(self, bg='#F1F5F9')
        btn_frame.pack(fill='x', padx=24, pady=12)
        self.make_button(btn_frame, '开始考试', lambda: self.app.show_frame('exam_setup'),
                         style='primary').pack(side='left', padx=(0, 12))
        self.make_button(btn_frame, '进入学习模式', lambda: self.app.show_frame('study_setup'),
                         style='secondary').pack(side='left')

    def on_show(self, **kwargs) -> None:
        """每次进入首页时刷新统计数据"""
        self._refresh_stats()
        self._refresh_history()

    def _refresh_stats(self) -> None:
        """刷新顶部统计卡片"""
        for w in self._stat_frame.winfo_children():
            w.destroy()

        engine = StatsEngine()
        data = engine.get_overview()

        cards = [
            ('题库总题数', str(data['total_questions']), '#2563EB'),
            ('累计考试次数', str(data['total_exams']),   '#16A34A'),
            ('平均得分',    f"{data['avg_score']}分",    '#D97706'),
            ('待复习错题',  str(data['wrong_count']),    '#DC2626'),
        ]

        for title, value, color in cards:
            card = self.make_card(self._stat_frame)
            card.pack(side='left', fill='both', expand=True, padx=(0, 12))
            tk.Label(card, text=value,
                     font=('Microsoft YaHei', 22, 'bold'),
                     fg=color, bg='#FFFFFF').pack(pady=(16, 4))
            tk.Label(card, text=title,
                     font=('Microsoft YaHei', 10),
                     fg='#64748B', bg='#FFFFFF').pack(pady=(0, 16))

    def _refresh_history(self) -> None:
        """刷新最近考试记录表格"""
        for row in self._tree.get_children():
            self._tree.delete(row)

        engine = StatsEngine()
        records = engine.get_exam_history(limit=10)
        for rec in records:
            self._tree.insert('', 'end', values=(
                rec.started_at[:16],
                rec.bank_name,
                rec.total_q,
                f'{rec.score:.1f}分',
                self.format_duration(rec.duration_sec),
            ))
