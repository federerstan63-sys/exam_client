# -*- coding: utf-8 -*-
"""
ui/history_frame.py — 考试历史页面
显示历史考试记录列表和得分趋势折线图，支持查看单次考试详情。
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Optional

from ui.base_frame import BaseFrame
from core.stats_engine import StatsEngine
from database.models import ExamRecord

if TYPE_CHECKING:
    from ui.app import App


class HistoryFrame(BaseFrame):
    """考试历史页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._records: List[ExamRecord] = []
        self._build()

    def _build(self) -> None:
        # 页面标题
        header = tk.Frame(self, bg='#F1F5F9')
        header.pack(fill='x', padx=24, pady=(20, 0))
        self.make_label(header, '考试历史', size=16, bold=True).pack(anchor='w')
        tk.Frame(self, height=1, bg='#CBD5E1').pack(fill='x', padx=24, pady=12)

        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        # 上半部分：得分趋势图
        chart_card = self.make_card(body)
        chart_card.pack(fill='x', pady=(0, 12))
        chart_inner = tk.Frame(chart_card, bg='#FFFFFF')
        chart_inner.pack(fill='x', padx=16, pady=12)
        self.make_label(chart_inner, '得分趋势', size=12, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 8))

        self._chart_canvas = tk.Canvas(
            chart_inner, height=140, bg='#FFFFFF',
            highlightthickness=0
        )
        self._chart_canvas.pack(fill='x')

        # 下半部分：历史记录表格
        self.make_label(body, '历史记录', size=12, bold=True).pack(anchor='w', pady=(0, 8))

        table_frame = tk.Frame(body, bg='#F1F5F9')
        table_frame.pack(fill='both', expand=True)

        cols = ('日期', '题库', '题数', '得分', '正确', '用时')
        self._tree = ttk.Treeview(table_frame, columns=cols, show='headings')
        self._tree.heading('日期',  text='考试日期')
        self._tree.heading('题库',  text='题库')
        self._tree.heading('题数',  text='题数')
        self._tree.heading('得分',  text='得分')
        self._tree.heading('正确',  text='正确率')
        self._tree.heading('用时',  text='用时')

        self._tree.column('日期',  width=160)
        self._tree.column('题库',  width=200)
        self._tree.column('题数',  width=70,  anchor='center')
        self._tree.column('得分',  width=80,  anchor='center')
        self._tree.column('正确',  width=80,  anchor='center')
        self._tree.column('用时',  width=100, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        self._tree.bind('<Double-1>', self._on_double_click)

        # 底部按钮
        btn_bar = tk.Frame(self, bg='#F1F5F9')
        btn_bar.pack(fill='x', padx=24, pady=(0, 16))
        self.make_button(btn_bar, '查看详情', self._view_detail,
                         style='secondary').pack(side='left')

    def on_show(self, **kwargs) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """刷新历史记录和趋势图"""
        engine = StatsEngine()
        self._records = engine.get_exam_history(limit=50)

        # 刷新表格
        for row in self._tree.get_children():
            self._tree.delete(row)

        for rec in self._records:
            pct = f'{rec.correct_count}/{rec.total_q}'
            self._tree.insert('', 'end', iid=str(rec.id), values=(
                rec.started_at[:16],
                rec.bank_name,
                rec.total_q,
                f'{rec.score:.1f}分',
                pct,
                self.format_duration(rec.duration_sec),
            ))

        # 刷新趋势图
        trend = engine.get_score_trend(limit=20)
        self._draw_chart(trend)

    def _draw_chart(self, trend: list) -> None:
        """在 Canvas 上绘制得分折线图"""
        c = self._chart_canvas
        c.delete('all')

        # 等待 Canvas 渲染完成后获取实际宽度
        c.update_idletasks()
        W = c.winfo_width() or 600
        H = 140
        pad_l, pad_r, pad_t, pad_b = 50, 20, 15, 30

        if not trend:
            c.create_text(W // 2, H // 2, text='暂无考试记录',
                          font=('Microsoft YaHei', 11), fill='#94A3B8')
            return

        scores = [s for _, s in trend]
        min_s  = max(0, min(scores) - 10)
        max_s  = min(100, max(scores) + 10)
        if max_s == min_s:
            max_s = min_s + 10

        chart_w = W - pad_l - pad_r
        chart_h = H - pad_t - pad_b

        # Y 轴刻度线和标签
        for val in range(0, 101, 20):
            if val < min_s or val > max_s:
                continue
            y = pad_t + chart_h - (val - min_s) / (max_s - min_s) * chart_h
            c.create_line(pad_l, y, W - pad_r, y, fill='#E2E8F0', dash=(4, 4))
            c.create_text(pad_l - 6, y, text=str(val), anchor='e',
                          font=('Microsoft YaHei', 8), fill='#94A3B8')

        # X 轴
        c.create_line(pad_l, H - pad_b, W - pad_r, H - pad_b, fill='#CBD5E1')
        # Y 轴
        c.create_line(pad_l, pad_t, pad_l, H - pad_b, fill='#CBD5E1')

        # 数据点和折线
        n = len(trend)
        points = []
        for i, (date, score) in enumerate(trend):
            x = pad_l + i / max(n - 1, 1) * chart_w
            y = pad_t + chart_h - (score - min_s) / (max_s - min_s) * chart_h
            points.append((x, y))

            # X 轴日期标签（只显示部分，避免拥挤）
            if n <= 10 or i % max(1, n // 5) == 0:
                c.create_text(x, H - pad_b + 10, text=date[5:],
                              font=('Microsoft YaHei', 7), fill='#94A3B8')

        # 绘制折线
        if len(points) >= 2:
            flat = [coord for pt in points for coord in pt]
            c.create_line(*flat, fill='#2563EB', width=2, smooth=True)

        # 绘制数据点
        for x, y in points:
            c.create_oval(x - 4, y - 4, x + 4, y + 4,
                          fill='#2563EB', outline='#FFFFFF', width=2)

    def _on_double_click(self, event) -> None:
        self._view_detail()

    def _view_detail(self) -> None:
        """弹窗查看单次考试详情"""
        selected = self._tree.selection()
        if not selected:
            tk.messagebox.showinfo('提示', '请先选择一条记录')
            return
        exam_id = int(selected[0])
        self._show_detail_window(exam_id)

    def _show_detail_window(self, exam_id: int) -> None:
        """弹出考试详情窗口"""
        engine = StatsEngine()
        exam, answers, questions = engine.get_exam_detail(exam_id)
        if not exam:
            return

        win = tk.Toplevel(self)
        win.title(f'考试详情 — {exam.started_at[:16]}')
        win.geometry('760x580')
        win.grab_set()

        # 顶部得分摘要
        top = tk.Frame(win, bg='#1E293B', height=70)
        top.pack(fill='x')
        top.pack_propagate(False)

        color = '#22C55E' if exam.score >= 60 else '#EF4444'
        tk.Label(top, text=f'{exam.score:.1f}分',
                 font=('Microsoft YaHei', 22, 'bold'),
                 fg=color, bg='#1E293B').pack(side='left', padx=24)
        tk.Label(
            top,
            text=f'题库：{exam.bank_name}  |  题数：{exam.total_q}  |  '
                 f'正确：{exam.correct_count}  |  用时：{self.format_duration(exam.duration_sec)}',
            font=('Microsoft YaHei', 10),
            fg='#CBD5E1', bg='#1E293B'
        ).pack(side='left')

        # 答题明细（可滚动）
        canvas = tk.Canvas(win, bg='#F1F5F9', highlightthickness=0)
        scroll = ttk.Scrollbar(win, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        scroll.pack(side='left', fill='y')

        inner = tk.Frame(canvas, bg='#F1F5F9')
        canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))

        q_map = {q.id: q for q in questions}
        ans_map = {a.question_id: a for a in answers}

        for i, q in enumerate(questions):
            ans = ans_map.get(q.id)
            is_correct = ans.is_correct if ans else False
            bg = '#F0FDF4' if is_correct else '#FEF2F2'

            card = tk.Frame(inner, bg=bg, relief='solid', bd=1,
                            highlightbackground='#E2E8F0', highlightthickness=1)
            card.pack(fill='x', padx=12, pady=4)

            from ui.widgets.question_widget import QuestionWidget
            wgt = QuestionWidget(card, q, show_answer=True, bg=bg)
            wgt.pack(fill='x', padx=12, pady=10)
            if ans and ans.user_answer:
                wgt.set_answer(ans.user_answer)
            wgt.highlight_correct()
