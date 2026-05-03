# -*- coding: utf-8 -*-
"""
ui/exam_result_frame.py — 考试结果页面
显示得分、题型分析、错题列表，支持查看解析和加入错题本。
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Optional

from ui.base_frame import BaseFrame
from database.models import ExamAnswer, ExamResult, Question

if TYPE_CHECKING:
    from ui.app import App


class ExamResultFrame(BaseFrame):
    """考试结果页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._result: Optional[ExamResult] = None
        self._paper: List[Question] = []
        self._build()

    def _build(self) -> None:
        # 顶部得分区
        self._score_frame = tk.Frame(self, bg='#1E293B', height=120)
        self._score_frame.pack(fill='x')
        self._score_frame.pack_propagate(False)

        self._score_label = tk.Label(
            self._score_frame, text='--',
            font=('Microsoft YaHei', 36, 'bold'),
            fg='#FACC15', bg='#1E293B'
        )
        self._score_label.pack(side='left', padx=40, pady=20)

        stats_frame = tk.Frame(self._score_frame, bg='#1E293B')
        stats_frame.pack(side='left', pady=20)
        self._stats_label = tk.Label(
            stats_frame, text='',
            font=('Microsoft YaHei', 12),
            fg='#CBD5E1', bg='#1E293B', justify='left'
        )
        self._stats_label.pack(anchor='w')

        # 主体区域
        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True, padx=24, pady=16)

        # 左侧：题型分析 + 错题列表
        left = tk.Frame(body, bg='#F1F5F9')
        left.pack(side='left', fill='both', expand=True, padx=(0, 16))

        # 题型分析卡片
        type_card = self.make_card(left)
        type_card.pack(fill='x', pady=(0, 12))
        type_inner = tk.Frame(type_card, bg='#FFFFFF')
        type_inner.pack(fill='x', padx=16, pady=12)
        self.make_label(type_inner, '题型分析', size=12, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 8))
        self._type_analysis_frame = tk.Frame(type_inner, bg='#FFFFFF')
        self._type_analysis_frame.pack(fill='x')

        # 错题列表
        wrong_card = self.make_card(left)
        wrong_card.pack(fill='both', expand=True)
        wrong_inner = tk.Frame(wrong_card, bg='#FFFFFF')
        wrong_inner.pack(fill='both', expand=True, padx=16, pady=12)
        self.make_label(wrong_inner, '错题列表', size=12, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 8))

        cols = ('#', '题干', '你的答案', '正确答案')
        self._wrong_tree = ttk.Treeview(wrong_inner, columns=cols, show='headings', height=10)
        self._wrong_tree.heading('#', text='#')
        self._wrong_tree.heading('题干', text='题干（前40字）')
        self._wrong_tree.heading('你的答案', text='你的答案')
        self._wrong_tree.heading('正确答案', text='正确答案')
        self._wrong_tree.column('#', width=40, anchor='center')
        self._wrong_tree.column('题干', width=320)
        self._wrong_tree.column('你的答案', width=80, anchor='center')
        self._wrong_tree.column('正确答案', width=80, anchor='center')

        wrong_scroll = ttk.Scrollbar(wrong_inner, orient='vertical', command=self._wrong_tree.yview)
        self._wrong_tree.configure(yscrollcommand=wrong_scroll.set)
        self._wrong_tree.pack(side='left', fill='both', expand=True)
        wrong_scroll.pack(side='left', fill='y')

        # 双击查看解析
        self._wrong_tree.bind('<Double-1>', self._on_wrong_double_click)

        # 右侧：操作按钮
        right = tk.Frame(body, bg='#F1F5F9', width=180)
        right.pack(side='left', fill='y')
        right.pack_propagate(False)

        self.make_label(right, '操作', size=12, bold=True).pack(anchor='w', pady=(0, 12))
        self.make_button(right, '再来一次', self._retry_exam, style='primary').pack(fill='x', pady=(0, 8))
        self.make_button(right, '查看解析', self._view_analysis, style='secondary').pack(fill='x', pady=(0, 8))
        self.make_button(right, '返回首页', lambda: self.app.show_frame('home'), style='secondary').pack(fill='x')

        # 解析弹窗（懒创建）
        self._analysis_window = None

    def on_show(self, result: ExamResult = None, paper: List[Question] = None, **kwargs) -> None:
        if result is None:
            return
        self._result = result
        self._paper  = paper or []
        self._refresh()

    def _refresh(self) -> None:
        r = self._result
        if not r:
            return

        # 得分区
        color = '#22C55E' if r.score >= 60 else '#EF4444'
        self._score_label.config(text=f'{r.score:.1f}分', fg=color)
        self._stats_label.config(
            text=f'正确：{r.correct} / {r.total} 题\n'
                 f'错误：{r.wrong} 题\n'
                 f'用时：{self.format_duration(r.duration_sec)}'
        )

        # 题型分析
        for w in self._type_analysis_frame.winfo_children():
            w.destroy()

        type_labels = {'single': '单选题', 'multi': '多选题',
                       'truefalse': '判断题', 'scenario': '场景题'}
        # 按题型统计
        type_stats: dict = {}
        q_map = {q.id: q for q in self._paper}
        for ans in r.answers:
            q = q_map.get(ans.question_id)
            if not q:
                continue
            t = q.q_type
            if t not in type_stats:
                type_stats[t] = [0, 0]   # [correct, total]
            type_stats[t][1] += 1
            if ans.is_correct:
                type_stats[t][0] += 1

        for q_type, (correct, total) in type_stats.items():
            pct = correct / total * 100 if total else 0
            row = tk.Frame(self._type_analysis_frame, bg='#FFFFFF')
            row.pack(fill='x', pady=2)
            tk.Label(row, text=f'{type_labels.get(q_type, q_type)}：',
                     font=('Microsoft YaHei', 10), fg='#64748B', bg='#FFFFFF',
                     width=8, anchor='w').pack(side='left')
            tk.Label(row, text=f'{correct}/{total}  ({pct:.1f}%)',
                     font=('Microsoft YaHei', 10), fg='#1E293B', bg='#FFFFFF').pack(side='left')

        # 错题列表
        for row in self._wrong_tree.get_children():
            self._wrong_tree.delete(row)

        wrong_num = 0
        for ans in r.answers:
            if ans.is_correct:
                continue
            wrong_num += 1
            q = q_map.get(ans.question_id)
            stem = (q.content[:40] + '...') if q and len(q.content) > 40 else (q.content if q else '')
            correct_ans = q.correct_ans if q else ''
            self._wrong_tree.insert('', 'end', iid=str(ans.question_id), values=(
                wrong_num, stem,
                ans.user_answer or '（未作答）',
                correct_ans,
            ))

    def _on_wrong_double_click(self, event) -> None:
        """双击错题列表行，弹出题目解析"""
        selected = self._wrong_tree.selection()
        if not selected:
            return
        q_id = int(selected[0])
        q_map = {q.id: q for q in self._paper}
        q = q_map.get(q_id)
        if q:
            self._show_question_popup(q)

    def _view_analysis(self) -> None:
        """查看全部题目解析（弹出窗口）"""
        if not self._paper:
            return
        win = tk.Toplevel(self)
        win.title('题目解析')
        win.geometry('700x600')
        win.grab_set()

        canvas = tk.Canvas(win, bg='#F1F5F9', highlightthickness=0)
        scroll = ttk.Scrollbar(win, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        scroll.pack(side='left', fill='y')

        inner = tk.Frame(canvas, bg='#F1F5F9')
        canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        q_map = {q.id: q for q in self._paper}
        ans_map = {a.question_id: a for a in self._result.answers}

        for i, q in enumerate(self._paper):
            ans = ans_map.get(q.id)
            is_correct = ans.is_correct if ans else False
            bg = '#F0FDF4' if is_correct else '#FEF2F2'
            border = '#86EFAC' if is_correct else '#FCA5A5'

            card = tk.Frame(inner, bg=bg, relief='solid', bd=1,
                            highlightbackground=border, highlightthickness=1)
            card.pack(fill='x', padx=12, pady=6)

            from ui.widgets.question_widget import QuestionWidget
            wgt = QuestionWidget(card, q, show_answer=True, bg=bg)
            wgt.pack(fill='x', padx=12, pady=12)
            if ans:
                wgt.set_answer(ans.user_answer)
            wgt.highlight_correct()

    def _show_question_popup(self, q: Question) -> None:
        """弹出单题解析窗口"""
        win = tk.Toplevel(self)
        win.title('题目解析')
        win.geometry('600x400')
        win.grab_set()

        from ui.widgets.question_widget import QuestionWidget
        wgt = QuestionWidget(win, q, show_answer=True, bg='#FFFFFF')
        wgt.pack(fill='both', expand=True, padx=20, pady=20)

        ans_map = {a.question_id: a for a in self._result.answers}
        ans = ans_map.get(q.id)
        if ans:
            wgt.set_answer(ans.user_answer)
        wgt.highlight_correct()

    def _retry_exam(self) -> None:
        """用相同参数再考一次"""
        self.app.show_frame('exam_setup')
