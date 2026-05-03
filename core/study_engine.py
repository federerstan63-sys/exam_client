# -*- coding: utf-8 -*-
"""
core/study_engine.py — 学习模式引擎
提供题库浏览、分类筛选等学习功能。
"""

import logging
from typing import List, Optional

from database.db_manager import DBManager
from database.models import Question

logger = logging.getLogger(__name__)


class StudyEngine:
    """学习模式引擎，支持按题库/分类顺序浏览所有题目"""

    def __init__(self, bank_id: int, category: Optional[str] = None):
        self._db      = DBManager.get_instance()
        self.bank_id  = bank_id
        self.category = category
        self._questions: List[Question] = []
        self._index   = 0
        self._load()

    def _load(self) -> None:
        """从数据库加载题目列表"""
        if self.category and self.category != '全部':
            rows = self._db.fetchall(
                'SELECT * FROM questions WHERE bank_id=? AND category=? ORDER BY id',
                (self.bank_id, self.category)
            )
        else:
            rows = self._db.fetchall(
                'SELECT * FROM questions WHERE bank_id=? ORDER BY id',
                (self.bank_id,)
            )
        self._questions = [Question.from_row(r) for r in rows]
        logger.info('学习模式加载 %d 题（题库=%d, 分类=%s）',
                    len(self._questions), self.bank_id, self.category)

    def get_total(self) -> int:
        return len(self._questions)

    def get_current_index(self) -> int:
        """返回当前题目的 0-based 索引"""
        return self._index

    def get_current(self) -> Optional[Question]:
        """返回当前题目，列表为空时返回 None"""
        if not self._questions:
            return None
        return self._questions[self._index]

    def next(self) -> Optional[Question]:
        """移动到下一题，已是最后一题则停留"""
        if self._index < len(self._questions) - 1:
            self._index += 1
        return self.get_current()

    def prev(self) -> Optional[Question]:
        """移动到上一题，已是第一题则停留"""
        if self._index > 0:
            self._index -= 1
        return self.get_current()

    def jump_to(self, index: int) -> Optional[Question]:
        """跳转到指定索引"""
        if 0 <= index < len(self._questions):
            self._index = index
        return self.get_current()

    def get_categories(self) -> List[str]:
        """返回当前题库的所有分类列表"""
        rows = self._db.fetchall(
            '''SELECT DISTINCT category FROM questions
               WHERE bank_id=? AND category != ''
               ORDER BY category''',
            (self.bank_id,)
        )
        return [r['category'] for r in rows]

    def reload(self, category: Optional[str] = None) -> None:
        """切换分类后重新加载"""
        self.category = category
        self._index   = 0
        self._load()
