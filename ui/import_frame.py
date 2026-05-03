# -*- coding: utf-8 -*-
"""
ui/import_frame.py — 题库导入页面
支持选择 Word/Excel 文件，显示导入进度和日志。
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from ui.base_frame import BaseFrame
from database.db_manager import DBManager

if TYPE_CHECKING:
    from ui.app import App


class ImportFrame(BaseFrame):
    """题库导入页面"""

    def __init__(self, parent: tk.Widget, app: 'App'):
        super().__init__(parent, app)
        self._selected_file = ''
        self._build()

    def _build(self) -> None:
        # 页面标题
        header = tk.Frame(self, bg='#F1F5F9')
        header.pack(fill='x', padx=24, pady=(20, 0))
        self.make_label(header, '题库导入', size=16, bold=True).pack(anchor='w')
        self.make_label(header, '支持 Word (.docx) 和 Excel (.xlsx) 格式',
                        size=10, color='#64748B').pack(anchor='w', pady=(4, 0))

        tk.Frame(self, height=1, bg='#CBD5E1').pack(fill='x', padx=24, pady=12)

        body = tk.Frame(self, bg='#F1F5F9')
        body.pack(fill='both', expand=True, padx=24)

        # 左侧：导入操作区
        left = tk.Frame(body, bg='#F1F5F9')
        left.pack(side='left', fill='both', expand=True, padx=(0, 16))

        # 文件选择
        file_card = self.make_card(left)
        file_card.pack(fill='x', pady=(0, 12))
        inner = tk.Frame(file_card, bg='#FFFFFF')
        inner.pack(fill='x', padx=16, pady=16)

        self.make_label(inner, '选择题库文件', size=12, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 8))

        file_row = tk.Frame(inner, bg='#FFFFFF')
        file_row.pack(fill='x')
        self.make_button(file_row, '浏览文件...', self._choose_file).pack(side='left')
        self._file_label = tk.Label(
            file_row, text='未选择文件',
            font=('Microsoft YaHei', 10), fg='#64748B', bg='#FFFFFF'
        )
        self._file_label.pack(side='left', padx=12)

        # 题库名称
        name_row = tk.Frame(inner, bg='#FFFFFF')
        name_row.pack(fill='x', pady=(12, 0))
        self.make_label(name_row, '题库名称：', size=11, bg='#FFFFFF').pack(side='left')
        self._name_var = tk.StringVar()
        tk.Entry(
            name_row, textvariable=self._name_var,
            font=('Microsoft YaHei', 11), width=30,
            relief='solid', bd=1
        ).pack(side='left', padx=(8, 0))

        # 导入按钮
        self._import_btn = self.make_button(inner, '开始导入', self._start_import, style='primary')
        self._import_btn.pack(anchor='w', pady=(16, 0))

        # 进度条
        progress_card = self.make_card(left)
        progress_card.pack(fill='x', pady=(0, 12))
        prog_inner = tk.Frame(progress_card, bg='#FFFFFF')
        prog_inner.pack(fill='x', padx=16, pady=12)

        self.make_label(prog_inner, '导入进度', size=11, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 6))
        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(
            prog_inner, variable=self._progress_var,
            maximum=100, length=400
        )
        self._progress_bar.pack(fill='x')
        self._progress_label = tk.Label(
            prog_inner, text='等待导入...',
            font=('Microsoft YaHei', 10), fg='#64748B', bg='#FFFFFF'
        )
        self._progress_label.pack(anchor='w', pady=(4, 0))

        # 导入日志
        log_card = self.make_card(left)
        log_card.pack(fill='both', expand=True)
        log_inner = tk.Frame(log_card, bg='#FFFFFF')
        log_inner.pack(fill='both', expand=True, padx=16, pady=12)

        self.make_label(log_inner, '导入日志', size=11, bold=True, bg='#FFFFFF').pack(anchor='w', pady=(0, 6))
        self._log_text = tk.Text(
            log_inner, height=8,
            font=('Microsoft YaHei', 10),
            state='disabled', relief='solid', bd=1,
            bg='#F8FAFC', fg='#1E293B'
        )
        log_scroll = ttk.Scrollbar(log_inner, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scroll.set)
        self._log_text.pack(side='left', fill='both', expand=True)
        log_scroll.pack(side='left', fill='y')

        # 右侧：已有题库列表
        right = tk.Frame(body, bg='#F1F5F9', width=320)
        right.pack(side='left', fill='both')
        right.pack_propagate(False)

        self.make_label(right, '已有题库', size=12, bold=True).pack(anchor='w', pady=(0, 8))

        bank_card = self.make_card(right)
        bank_card.pack(fill='both', expand=True)

        cols = ('名称', '题数', '导入时间')
        self._bank_tree = ttk.Treeview(bank_card, columns=cols, show='headings', height=15)
        for col in cols:
            self._bank_tree.heading(col, text=col)
        self._bank_tree.column('名称', width=120)
        self._bank_tree.column('题数', width=60, anchor='center')
        self._bank_tree.column('导入时间', width=110)

        bank_scroll = ttk.Scrollbar(bank_card, orient='vertical', command=self._bank_tree.yview)
        self._bank_tree.configure(yscrollcommand=bank_scroll.set)
        self._bank_tree.pack(side='left', fill='both', expand=True, padx=8, pady=8)
        bank_scroll.pack(side='left', fill='y', pady=8)

        # 删除题库按钮
        self.make_button(right, '删除选中题库', self._delete_bank, style='danger').pack(
            anchor='w', pady=(8, 0)
        )

    def on_show(self, **kwargs) -> None:
        self._refresh_bank_list()

    # ── 事件处理 ──────────────────────────────────────────────────────────────

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title='选择题库文件',
            filetypes=[
                ('题库文件', '*.docx *.xlsx'),
                ('Word 文件', '*.docx'),
                ('Excel 文件', '*.xlsx'),
            ]
        )
        if path:
            self._selected_file = path
            filename = os.path.basename(path)
            self._file_label.config(text=filename, fg='#1E293B')
            # 自动填充题库名称（去掉扩展名）
            if not self._name_var.get():
                self._name_var.set(os.path.splitext(filename)[0])

    def _start_import(self) -> None:
        if not self._selected_file:
            messagebox.showwarning('提示', '请先选择题库文件')
            return
        if not os.path.exists(self._selected_file):
            messagebox.showerror('错误', '文件不存在，请重新选择')
            return

        bank_name = self._name_var.get().strip()
        if not bank_name:
            messagebox.showwarning('提示', '请输入题库名称')
            return

        # 禁用按钮防止重复点击
        self._import_btn.config(state='disabled')
        self._clear_log()
        self._progress_var.set(0)
        self._progress_label.config(text='正在解析文件...')

        # 在后台线程执行导入，避免阻塞 UI
        threading.Thread(
            target=self._do_import,
            args=(self._selected_file, bank_name),
            daemon=True
        ).start()

    def _do_import(self, filepath: str, bank_name: str) -> None:
        """后台线程执行导入逻辑"""
        try:
            ext = filepath.rsplit('.', 1)[-1].lower()
            if ext == 'docx':
                from importer.docx_importer import DocxImporter
                importer = DocxImporter(filepath, bank_name)
            elif ext == 'xlsx':
                from importer.xlsx_importer import XlsxImporter
                importer = XlsxImporter(filepath, bank_name)
            else:
                self._ui_log('✗ 不支持的文件格式')
                return

            self._ui_update_progress(20, '正在解析题目...')
            questions = importer.parse()
            self._ui_log(f'✓ 解析完成，共发现 {len(questions)} 题')

            self._ui_update_progress(60, '正在写入数据库...')
            success, fail, errors = importer.save_to_db(questions)

            for err in errors:
                self._ui_log(f'  ✗ {err}')

            self._ui_update_progress(100, f'导入完成：成功 {success} 题，跳过 {fail} 题')
            self._ui_log(f'✓ 成功导入 {success} 题')
            if fail:
                self._ui_log(f'  跳过 {fail} 题（格式不符）')

            # 刷新题库列表（回到主线程）
            self.after(0, self._refresh_bank_list)
            self.after(0, lambda: self._import_btn.config(state='normal'))

        except Exception as e:
            self._ui_log(f'✗ 导入失败：{e}')
            self._ui_update_progress(0, '导入失败')
            self.after(0, lambda: self._import_btn.config(state='normal'))

    def _delete_bank(self) -> None:
        selected = self._bank_tree.selection()
        if not selected:
            messagebox.showwarning('提示', '请先选择要删除的题库')
            return
        item = self._bank_tree.item(selected[0])
        bank_name = item['values'][0]
        if not messagebox.askyesno('确认删除',
                                   f'确定要删除题库「{bank_name}」及其所有题目吗？\n此操作不可恢复。'):
            return

        db = DBManager.get_instance()
        # 查找 bank_id
        row = db.fetchone('SELECT id FROM question_banks WHERE name=?', (bank_name,))
        if row:
            bank_id = row['id']
            # 级联删除：先删题目，再删题库记录
            db.execute('DELETE FROM questions WHERE bank_id=?', (bank_id,))
            db.execute('DELETE FROM question_banks WHERE id=?', (bank_id,))
            self._refresh_bank_list()
            messagebox.showinfo('完成', f'题库「{bank_name}」已删除')

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    def _refresh_bank_list(self) -> None:
        for row in self._bank_tree.get_children():
            self._bank_tree.delete(row)
        db = DBManager.get_instance()
        rows = db.fetchall(
            'SELECT name, question_count, imported_at FROM question_banks WHERE is_active=1 ORDER BY imported_at DESC'
        )
        for r in rows:
            self._bank_tree.insert('', 'end', values=(
                r['name'], r['question_count'], r['imported_at'][:16]
            ))

    def _ui_log(self, msg: str) -> None:
        """线程安全地向日志框追加文本"""
        def _append():
            self._log_text.config(state='normal')
            self._log_text.insert('end', msg + '\n')
            self._log_text.see('end')
            self._log_text.config(state='disabled')
        self.after(0, _append)

    def _ui_update_progress(self, value: float, text: str) -> None:
        """线程安全地更新进度条"""
        def _update():
            self._progress_var.set(value)
            self._progress_label.config(text=text)
        self.after(0, _update)

    def _clear_log(self) -> None:
        self._log_text.config(state='normal')
        self._log_text.delete('1.0', 'end')
        self._log_text.config(state='disabled')
