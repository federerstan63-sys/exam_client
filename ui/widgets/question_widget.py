# -*- coding: utf-8 -*-
"""
ui/widgets/question_widget.py — 题目显示组件
通用组件，支持单选/多选/判断/场景题的显示与交互。
"""

import tkinter as tk
from typing import Callable, List, Optional, Tuple

from database.models import Question


class QuestionWidget(tk.Frame):
    """
    题目显示组件。
    show_answer=True 时自动高亮正确答案（学习模式/结果查看用）。
    on_answer_change 回调在用户改变选项时触发。
    """

    def __init__(
        self,
        parent: tk.Widget,
        question: Question,
        show_answer: bool = False,
        on_answer_change: Optional[Callable[[str], None]] = None,
        bg: str = '#FFFFFF',
    ):
        super().__init__(parent, bg=bg)
        self.question         = question
        self.show_answer      = show_answer
        self.on_answer_change = on_answer_change
        self._bg              = bg

        # 单选用 StringVar，多选用多个 BooleanVar
        self._single_var: tk.StringVar = tk.StringVar(value='')
        self._multi_vars: List[Tuple[str, tk.BooleanVar]] = []

        self._build()

    # ── 构建 UI ───────────────────────────────────────────────────────────────

    def _build(self) -> None:
        q = self.question

        # 题型标签
        type_labels = {
            'single':    '【单选题】',
            'multi':     '【多选题】',
            'truefalse': '【判断题】',
            'scenario':  '【场景题】',
        }
        type_text = type_labels.get(q.q_type, '【题目】')

        tk.Label(
            self, text=type_text,
            font=('Microsoft YaHei', 10),
            fg='#2563EB', bg=self._bg
        ).pack(anchor='w', pady=(0, 4))

        # 题干（支持长文本自动换行）
        tk.Label(
            self, text=q.content,
            font=('Microsoft YaHei', 12),
            fg='#1E293B', bg=self._bg,
            wraplength=680, justify='left', anchor='w'
        ).pack(anchor='w', pady=(0, 12))

        # 选项区域
        options = q.get_options()
        self._option_labels: List[tk.Label] = []

        if q.q_type == 'multi':
            self._build_multi_options(options)
        else:
            self._build_single_options(options)

        # 解析区域（show_answer 模式下显示）
        if self.show_answer and q.explanation:
            sep = tk.Frame(self, height=1, bg='#E2E8F0')
            sep.pack(fill='x', pady=(12, 8))
            tk.Label(
                self, text='解析：',
                font=('Microsoft YaHei', 10, 'bold'),
                fg='#64748B', bg=self._bg
            ).pack(anchor='w')
            tk.Label(
                self, text=q.explanation,
                font=('Microsoft YaHei', 10),
                fg='#475569', bg=self._bg,
                wraplength=680, justify='left'
            ).pack(anchor='w', pady=(2, 0))

        # show_answer 模式下立即高亮正确答案
        if self.show_answer:
            self.highlight_correct()

    def _build_single_options(self, options: List[Tuple[str, str]]) -> None:
        """构建单选/判断题选项（Radiobutton）"""
        for letter, text in options:
            lbl = tk.Label(
                self,
                text=f'  {letter}.  {text}',
                font=('Microsoft YaHei', 11),
                fg='#1E293B', bg=self._bg,
                anchor='w', cursor='hand2',
                wraplength=660, justify='left',
                padx=8, pady=4,
            )
            lbl.pack(fill='x', pady=2)
            self._option_labels.append(lbl)

            # 绑定点击事件（整行可点击）
            lbl.bind('<Button-1>', lambda e, l=letter: self._on_single_click(l))
            lbl.bind('<Enter>', lambda e, w=lbl: w.config(bg='#EFF6FF'))
            lbl.bind('<Leave>', lambda e, w=lbl: w.config(bg=self._bg))

    def _build_multi_options(self, options: List[Tuple[str, str]]) -> None:
        """构建多选题选项（Checkbutton）"""
        for letter, text in options:
            var = tk.BooleanVar(value=False)
            self._multi_vars.append((letter, var))

            frame = tk.Frame(self, bg=self._bg)
            frame.pack(fill='x', pady=2)

            cb = tk.Checkbutton(
                frame, variable=var,
                font=('Microsoft YaHei', 11),
                fg='#1E293B', bg=self._bg,
                activebackground=self._bg,
                text=f'  {letter}.  {text}',
                anchor='w', cursor='hand2',
                command=self._on_multi_change,
                wraplength=640, justify='left',
            )
            cb.pack(fill='x', padx=8)
            self._option_labels.append(cb)

    # ── 事件处理 ──────────────────────────────────────────────────────────────

    def _on_single_click(self, letter: str) -> None:
        """单选/判断题点击选项"""
        if self.show_answer:
            return
        self._single_var.set(letter)
        # 更新所有选项的背景色
        options = self.question.get_options()
        for i, (lbl_letter, _) in enumerate(options):
            if i < len(self._option_labels):
                color = '#DBEAFE' if lbl_letter == letter else self._bg
                self._option_labels[i].config(bg=color)
        if self.on_answer_change:
            self.on_answer_change(letter)

    def _on_multi_change(self) -> None:
        """多选题勾选变化"""
        if self.on_answer_change:
            self.on_answer_change(self.get_selected_answer())

    # ── 公共接口 ──────────────────────────────────────────────────────────────

    def get_selected_answer(self) -> str:
        """返回当前选中答案字符串，如 'A' 或 'AC'"""
        if self.question.q_type == 'multi':
            selected = [l for l, v in self._multi_vars if v.get()]
            return ''.join(sorted(selected))
        return self._single_var.get()

    def set_answer(self, answer: str) -> None:
        """程序化设置答案（用于恢复已答状态）"""
        if self.question.q_type == 'multi':
            for letter, var in self._multi_vars:
                var.set(letter in answer.upper())
        else:
            self._single_var.set(answer)
            # 更新背景色
            options = self.question.get_options()
            for i, (lbl_letter, _) in enumerate(options):
                if i < len(self._option_labels):
                    color = '#DBEAFE' if lbl_letter == answer else self._bg
                    self._option_labels[i].config(bg=color)

    def highlight_correct(self) -> None:
        """高亮正确答案（绿色），错误答案（红色）"""
        correct = set(self.question.correct_ans.upper())
        options = self.question.get_options()

        if self.question.q_type == 'multi':
            for i, (letter, var) in enumerate(self._multi_vars):
                if i < len(self._option_labels):
                    is_correct_option = letter in correct
                    is_selected = var.get()
                    if is_correct_option:
                        self._option_labels[i].config(fg='#16A34A')
                    elif is_selected and not is_correct_option:
                        self._option_labels[i].config(fg='#DC2626')
        else:
            user_ans = self._single_var.get().upper()
            for i, (letter, _) in enumerate(options):
                if i < len(self._option_labels):
                    if letter in correct:
                        self._option_labels[i].config(bg='#DCFCE7', fg='#15803D')
                    elif letter == user_ans and letter not in correct:
                        self._option_labels[i].config(bg='#FEE2E2', fg='#DC2626')

    def reset(self) -> None:
        """重置选项状态"""
        self._single_var.set('')
        for _, var in self._multi_vars:
            var.set(False)
        for lbl in self._option_labels:
            lbl.config(bg=self._bg, fg='#1E293B')
