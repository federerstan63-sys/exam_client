# -*- coding: utf-8 -*-
"""
ui/wrong_book_frame.py — 错题本页面
显示所有错题，支持复习、标记已掌握、开始错题练习。
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, List, Optional

from ui.base_frame import BaseFrame
from core.stats_engine import StatsEngine
from database.models import WrongAnswerEntry

if TYPE_CHECKING:
    from ui.app import App


class WrongBookFrame(BaseFrame):
    """错题本页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._entries: List[WrongAnswerEntry] = []
        self._build()

    def _build(self) -> None:
        # 页面标题栏
        header = tk.Frame(self, bg='#F1F5F9')
        header.pack(fill='x', padx=24, pady=(20, 0))

        self.make_label(header, '错题本', size=16, bold=True).pack(side='left')

        # 右侧工具栏
        toolbar = tk.Frame(header, bg='#F1F5F9')
        toolbar.pack(side='right')

        self._hide_mastered_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            toolbar, text='隐藏已掌握',
            variable=self._hide_mastered_var,
            font=('Microsoft YaHei', 10), bg='#F1F5F9',
            command=self.on_show
        ).pack(side='left', padx=(0, 12))

        self.make_button(toolbar, '开始错题练习', self._start_wrong_exam,
                         style='primary').pack(side='left')

        tk.Frame(self, height=1, bg='#CBD5E1').pack(fill='x', padx=24, pady=12)

        # 统计信息行
        self._stat_label = self.make_label(self, '', size=10, color='#64748B')
        self._stat_label.pack(anchor='w', padx=24, pady=(0, 8))

        # 错题列表（主体）
        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        cols = ('题干', '题型', '错误次数', '最近答错', '状态')
        self._tree = ttk.Treeview(body, columns=cols, show='headings')
        self._tree.heading('题干',   text='题干（前50字）')
        self._tree.heading('题型',   text='题型')
        self._tree.heading('错误次数', text='错误次数')
        self._tree.heading('最近答错', text='最近答错')
        self._tree.heading('状态',   text='状态')

        self._tree.column('题干',    width=380)
        self._tree.column('题型',    width=80,  anchor='center')
        self._tree.column('错误次数', width=80,  anchor='center')
        self._tree.column('最近答错', width=140, anchor='center')
        self._tree.column('状态',    width=80,  anchor='center')

        scrollbar = ttk.Scrollbar(body, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='left', fill='y')

        # 双击查看题目
        self._tree.bind('<Double-1>', self._on_double_click)

        # 底部操作按钮
        btn_bar = tk.Frame(self, bg='#F1F5F9')
        btn_bar.pack(fill='x', padx=24, pady=(0, 16))
        self.make_button(btn_bar, '查看题目', self._view_selected,
                         style='secondary').pack(side='left', padx=(0, 8))
        self.make_button(btn_bar, '标记已掌握', self._mark_mastered,
                         style='success').pack(side='left', padx=(0, 8))
        self.make_button(btn_bar, '取消掌握', self._unmark_mastered,
                         style='secondary').pack(side='left', padx=(0, 8))
        self.make_button(btn_bar, '从错题本删除', self._delete_entry,
                         style='danger').pack(side='left')

    def on_show(self, **kwargs) -> None:
        self._refresh()

    def _refresh(self) -> None:
        """刷新错题列表"""
        for row in self._tree.get_children():
            self._tree.delete(row)

        engine = StatsEngine()
        hide = self._hide_mastered_var.get()
        self._entries = engine.get_wrong_questions(hide_mastered=hide)

        type_labels = {'single': '单选', 'multi': '多选',
                       'truefalse': '判断', 'scenario': '场景'}

        for entry in self._entries:
            q = entry.question
            if not q:
                continue
            stem = (q.content[:50] + '...') if len(q.content) > 50 else q.content
            status = '✓ 已掌握' if entry.is_mastered else '待复习'
            self._tree.insert('', 'end', iid=str(entry.question_id), values=(
                stem,
                type_labels.get(q.q_type, q.q_type),
                entry.wrong_count,
                entry.last_wrong[:16],
                status,
            ))

        total_all = StatsEngine().get_overview()['wrong_count']
        self._stat_label.config(
            text=f'共 {len(self._entries)} 题（全部错题：{total_all} 题）'
        )

    def _get_selected_entry(self) -> Optional[WrongAnswerEntry]:
        """获取当前选中的错题条目"""
        selected = self._tree.selection()
        if not selected:
            return None
        q_id = int(selected[0])
        for e in self._entries:
            if e.question_id == q_id:
                return e
        return None

    def _on_double_click(self, event) -> None:
        self._view_selected()

    def _view_selected(self) -> None:
        """弹窗查看选中题目"""
        entry = self._get_selected_entry()
        if not entry or not entry.question:
            messagebox.showinfo('提示', '请先选择一道题目')
            return

        win = tk.Toplevel(self)
        win.title('题目详情')
        win.geometry('620x420')
        win.grab_set()

        from ui.widgets.question_widget import QuestionWidget
        wgt = QuestionWidget(win, entry.question, show_answer=True, bg='#FFFFFF')
        wgt.pack(fill='both', expand=True, padx=20, pady=20)

        # 显示上次错误答案
        if entry.last_answer:
            wgt.set_answer(entry.last_answer)
        wgt.highlight_correct()

        info = tk.Label(
            win,
            text=f'上次错误答案：{entry.last_answer or "（未作答）"}    累计答错：{entry.wrong_count} 次',
            font=('Microsoft YaHei', 9), fg='#DC2626', bg='#FFFFFF'
        )
        info.pack(pady=(0, 12))

    def _mark_mastered(self) -> None:
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showinfo('提示', '请先选择一道题目')
            return
        StatsEngine().mark_mastered(entry.question_id)
        self._refresh()

    def _unmark_mastered(self) -> None:
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showinfo('提示', '请先选择一道题目')
            return
        StatsEngine().unmark_mastered(entry.question_id)
        self._refresh()

    def _delete_entry(self) -> None:
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showinfo('提示', '请先选择一道题目')
            return
        if not messagebox.askyesno('确认', '确定从错题本中删除这道题吗？'):
            return
        StatsEngine().delete_wrong_entry(entry.question_id)
        self._refresh()

    def _start_wrong_exam(self) -> None:
        """用错题本中的题目开始一次练习"""
        if not self._entries:
            messagebox.showinfo('提示', '错题本为空，无法开始练习')
            return

        # 收集错题 ID，传给考试页面（特殊模式）
        q_ids = [e.question_id for e in self._entries if not e.is_mastered]
        if not q_ids:
            messagebox.showinfo('提示', '没有待复习的错题')
            return

        self.app.show_frame('exam', bank_id=None, question_count=len(q_ids),
                            time_limit=None, q_types=None, wrong_q_ids=q_ids)
