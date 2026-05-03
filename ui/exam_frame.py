# -*- coding: utf-8 -*-
"""
ui/exam_frame.py — 考试答题页面
显示题目、选项、计时器、题目导航，支持标记题目和跳题。
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Dict, List, Optional

from ui.base_frame import BaseFrame
from ui.widgets.question_widget import QuestionWidget
from core.exam_engine import ExamEngine
from database.models import Question

if TYPE_CHECKING:
    from ui.app import App


class ExamFrame(BaseFrame):
    """考试答题页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._engine: Optional[ExamEngine] = None
        self._paper: List[Question] = []
        self._current_idx: int = 0
        self._answers: Dict[int, str] = {}     # question_id → answer
        self._marked: set = set()              # 已标记的 question_id
        self._nav_btns: List[tk.Label] = []
        self._q_widget: Optional[QuestionWidget] = None
        self._timer_id = None
        self._build()

    def _build(self) -> None:
        # ── 顶部信息栏 ────────────────────────────────────────────────────────
        top = tk.Frame(self, bg='#1E293B', height=56)
        top.pack(fill='x')
        top.pack_propagate(False)

        self._progress_label = tk.Label(
            top, text='第 1 / 1 题',
            font=('Microsoft YaHei', 12, 'bold'),
            fg='#FFFFFF', bg='#1E293B'
        )
        self._progress_label.pack(side='left', padx=20)

        self._type_label = tk.Label(
            top, text='',
            font=('Microsoft YaHei', 10),
            fg='#94A3B8', bg='#1E293B'
        )
        self._type_label.pack(side='left')

        self._timer_label = tk.Label(
            top, text='',
            font=('Microsoft YaHei', 12, 'bold'),
            fg='#FACC15', bg='#1E293B'
        )
        self._timer_label.pack(side='right', padx=20)

        # 进度条
        self._prog_var = tk.DoubleVar(value=0)
        prog_bar = ttk.Progressbar(self, variable=self._prog_var, maximum=100)
        prog_bar.pack(fill='x')

        # ── 主体区域 ──────────────────────────────────────────────────────────
        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True)

        # 左侧：题目显示区（带滚动）
        left = tk.Frame(body, bg='#F1F5F9')
        left.pack(side='left', fill='both', expand=True, padx=(16, 8), pady=16)

        # 题目卡片（可滚动）
        self._q_canvas = tk.Canvas(left, bg='#FFFFFF', highlightthickness=0)
        q_scroll = ttk.Scrollbar(left, orient='vertical', command=self._q_canvas.yview)
        self._q_canvas.configure(yscrollcommand=q_scroll.set)
        self._q_canvas.pack(side='left', fill='both', expand=True)
        q_scroll.pack(side='left', fill='y')

        self._q_inner = tk.Frame(self._q_canvas, bg='#FFFFFF')
        self._q_canvas_window = self._q_canvas.create_window(
            (0, 0), window=self._q_inner, anchor='nw'
        )
        self._q_inner.bind('<Configure>', self._on_q_inner_resize)
        self._q_canvas.bind('<Configure>', self._on_canvas_resize)

        # 底部操作按钮
        btn_bar = tk.Frame(left, bg='#F1F5F9')
        btn_bar.pack(fill='x', pady=(8, 0))
        self.make_button(btn_bar, '◀ 上一题', self._prev_q, style='secondary').pack(side='left')
        self._mark_btn = self.make_button(btn_bar, '☆ 标记本题', self._toggle_mark, style='secondary')
        self._mark_btn.pack(side='left', padx=8)
        self.make_button(btn_bar, '下一题 ▶', self._next_q, style='primary').pack(side='left')
        self.make_button(btn_bar, '交卷', self._submit_exam, style='danger').pack(side='right')

        # 右侧：题目导航面板
        right = tk.Frame(body, bg='#F1F5F9', width=200)
        right.pack(side='left', fill='y', padx=(0, 16), pady=16)
        right.pack_propagate(False)

        nav_card = self.make_card(right)
        nav_card.pack(fill='both', expand=True)
        nav_inner = tk.Frame(nav_card, bg='#FFFFFF')
        nav_inner.pack(fill='both', expand=True, padx=8, pady=8)

        self.make_label(nav_inner, '题目导航', size=11, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 6))

        # 图例
        legend = tk.Frame(nav_inner, bg='#FFFFFF')
        legend.pack(anchor='w', pady=(0, 8))
        for color, text in [('#E2E8F0', '未答'), ('#DBEAFE', '已答'), ('#FEF3C7', '已标记')]:
            dot = tk.Frame(legend, bg=color, width=12, height=12, relief='solid', bd=1)
            dot.pack(side='left')
            tk.Label(legend, text=text, font=('Microsoft YaHei', 9),
                     fg='#64748B', bg='#FFFFFF').pack(side='left', padx=(2, 8))

        # 导航按钮网格（可滚动）
        nav_canvas = tk.Canvas(nav_inner, bg='#FFFFFF', highlightthickness=0)
        nav_scroll = ttk.Scrollbar(nav_inner, orient='vertical', command=nav_canvas.yview)
        nav_canvas.configure(yscrollcommand=nav_scroll.set)
        nav_canvas.pack(side='left', fill='both', expand=True)
        nav_scroll.pack(side='left', fill='y')

        self._nav_grid = tk.Frame(nav_canvas, bg='#FFFFFF')
        nav_canvas.create_window((0, 0), window=self._nav_grid, anchor='nw')
        self._nav_grid.bind('<Configure>',
                            lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox('all')))

    # ── 页面生命周期 ──────────────────────────────────────────────────────────

    def on_show(self, bank_id: int = 0, question_count: int = 50,
                time_limit: Optional[int] = None,
                q_types: Optional[List[str]] = None,
                wrong_q_ids: Optional[List[int]] = None, **kwargs) -> None:
        """初始化考试引擎并开始考试"""
        self._engine = ExamEngine(
            bank_id=bank_id,
            question_count=question_count,
            time_limit=time_limit,
            q_types=q_types,
            wrong_q_ids=wrong_q_ids,
        )
        self._paper = self._engine.generate_paper()

        if not self._paper:
            messagebox.showwarning('提示', '该题库没有符合条件的题目，请重新设置')
            self.app.show_frame('exam_setup')
            return

        self._answers = {}
        self._marked  = set()
        self._current_idx = 0
        self._engine.start()

        self._build_nav_buttons()
        self._show_question(0)
        self._update_timer()

    def on_hide(self) -> None:
        """离开页面时停止计时器"""
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    # ── 题目显示 ──────────────────────────────────────────────────────────────

    def _show_question(self, idx: int) -> None:
        """显示指定索引的题目"""
        if not self._paper or idx < 0 or idx >= len(self._paper):
            return

        self._current_idx = idx
        q = self._paper[idx]

        # 通知引擎切换题目（记录用时）
        self._engine.mark_question_start(q.id)

        # 清空旧题目组件
        for w in self._q_inner.winfo_children():
            w.destroy()

        # 创建新题目组件
        self._q_widget = QuestionWidget(
            self._q_inner, q,
            show_answer=False,
            on_answer_change=lambda ans: self._on_answer_change(q.id, ans),
            bg='#FFFFFF',
        )
        self._q_widget.pack(fill='both', expand=True, padx=20, pady=20)

        # 恢复已有答案
        if q.id in self._answers:
            self._q_widget.set_answer(self._answers[q.id])

        # 更新顶部信息
        type_map = {'single': '单选题', 'multi': '多选题',
                    'truefalse': '判断题', 'scenario': '场景题'}
        self._progress_label.config(text=f'第 {idx + 1} / {len(self._paper)} 题')
        self._type_label.config(text=f'  [{type_map.get(q.q_type, "")}]')

        # 更新进度条
        answered = len(self._answers)
        self._prog_var.set(answered / len(self._paper) * 100)

        # 更新标记按钮状态
        if q.id in self._marked:
            self._mark_btn.config(text='★ 取消标记', bg='#D97706')
        else:
            self._mark_btn.config(text='☆ 标记本题', bg='#64748B')

        # 更新导航按钮高亮
        self._update_nav_highlight()

        # 重置滚动位置
        self._q_canvas.yview_moveto(0)

    def _on_answer_change(self, question_id: int, answer: str) -> None:
        """用户改变答案时更新缓存"""
        if answer:
            self._answers[question_id] = answer
        elif question_id in self._answers:
            del self._answers[question_id]
        # 更新进度条
        self._prog_var.set(len(self._answers) / len(self._paper) * 100)
        self._update_nav_highlight()

    # ── 导航按钮 ──────────────────────────────────────────────────────────────

    def _build_nav_buttons(self) -> None:
        """构建题目导航按钮网格"""
        for w in self._nav_grid.winfo_children():
            w.destroy()
        self._nav_btns = []

        cols = 5
        for i, q in enumerate(self._paper):
            btn = tk.Label(
                self._nav_grid,
                text=str(i + 1),
                font=('Microsoft YaHei', 9),
                width=3, height=1,
                relief='solid', bd=1,
                cursor='hand2',
                bg='#E2E8F0', fg='#1E293B',
            )
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            btn.bind('<Button-1>', lambda e, idx=i: self._show_question(idx))
            self._nav_btns.append(btn)

    def _update_nav_highlight(self) -> None:
        """根据答题状态更新导航按钮颜色"""
        for i, q in enumerate(self._paper):
            if i >= len(self._nav_btns):
                break
            btn = self._nav_btns[i]
            if i == self._current_idx:
                btn.config(bg='#2563EB', fg='#FFFFFF')
            elif q.id in self._marked:
                btn.config(bg='#FEF3C7', fg='#92400E')
            elif q.id in self._answers:
                btn.config(bg='#DBEAFE', fg='#1D4ED8')
            else:
                btn.config(bg='#E2E8F0', fg='#1E293B')

    # ── 操作按钮 ──────────────────────────────────────────────────────────────

    def _prev_q(self) -> None:
        if self._current_idx > 0:
            self._show_question(self._current_idx - 1)

    def _next_q(self) -> None:
        if self._current_idx < len(self._paper) - 1:
            self._show_question(self._current_idx + 1)

    def _toggle_mark(self) -> None:
        if not self._paper:
            return
        q_id = self._paper[self._current_idx].id
        if q_id in self._marked:
            self._marked.discard(q_id)
            self._mark_btn.config(text='☆ 标记本题', bg='#64748B')
        else:
            self._marked.add(q_id)
            self._mark_btn.config(text='★ 取消标记', bg='#D97706')
        self._update_nav_highlight()

    def _submit_exam(self) -> None:
        """交卷前确认，然后提交"""
        answered, total = self._engine.get_progress()
        unanswered = total - answered
        msg = f'共 {total} 题，已答 {answered} 题。'
        if unanswered > 0:
            msg += f'\n还有 {unanswered} 题未作答，确定交卷吗？'
        else:
            msg += '\n确定交卷吗？'

        if not messagebox.askyesno('确认交卷', msg):
            return

        # 将当前页面的答案提交给引擎
        for q in self._paper:
            ans = self._answers.get(q.id, '')
            self._engine.submit_answer(q.id, ans)

        result = self._engine.finish()
        self.on_hide()
        self.app.show_frame('exam_result', result=result, paper=self._paper)

    # ── 计时器 ────────────────────────────────────────────────────────────────

    def _update_timer(self) -> None:
        """每秒更新计时器显示"""
        if not self._engine:
            return

        remaining = self._engine.get_remaining_time()
        if remaining is None:
            # 无时限：显示已用时
            pass
        elif remaining <= 0:
            self._timer_label.config(text='时间到！', fg='#EF4444')
            self._auto_submit()
            return
        else:
            color = '#EF4444' if remaining < 300 else '#FACC15'
            self._timer_label.config(
                text=f'剩余 {self.format_duration(remaining)}',
                fg=color
            )

        self._timer_id = self.after(1000, self._update_timer)

    def _auto_submit(self) -> None:
        """时间到自动交卷"""
        messagebox.showinfo('时间到', '考试时间已到，系统自动交卷。')
        for q in self._paper:
            ans = self._answers.get(q.id, '')
            self._engine.submit_answer(q.id, ans)
        result = self._engine.finish()
        self.app.show_frame('exam_result', result=result, paper=self._paper)

    # ── Canvas 自适应 ─────────────────────────────────────────────────────────

    def _on_q_inner_resize(self, event) -> None:
        self._q_canvas.configure(scrollregion=self._q_canvas.bbox('all'))

    def _on_canvas_resize(self, event) -> None:
        self._q_canvas.itemconfig(self._q_canvas_window, width=event.width)
