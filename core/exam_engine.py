# -*- coding: utf-8 -*-
"""
core/exam_engine.py — 考试引擎
负责随机出题、计时、判分、持久化考试结果。
"""

import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from database.db_manager import DBManager
from database.models import ExamAnswer, ExamResult, Question

logger = logging.getLogger(__name__)


class ExamEngine:
    """
    考试引擎。
    使用流程：
      1. engine = ExamEngine(bank_id, question_count, time_limit)
      2. paper  = engine.generate_paper()
      3. engine.start()
      4. engine.submit_answer(question_id, answer)  # 每题调用一次
      5. result = engine.finish()
    """

    def __init__(
        self,
        bank_id: Optional[int],
        question_count: int,
        time_limit: Optional[int] = None,    # 秒，None 表示无限制
        q_types: Optional[List[str]] = None,  # 限定题型，None 表示全部
        categories: Optional[List[str]] = None,  # 限定分类，None 表示全部
        wrong_q_ids: Optional[List[int]] = None,  # 错题练习模式：指定题目 ID 列表
    ):
        self._db             = DBManager.get_instance()
        self.bank_id         = bank_id
        self.question_count  = question_count
        self.time_limit      = time_limit
        self.q_types         = q_types
        self.categories      = categories
        self.wrong_q_ids     = wrong_q_ids   # 非 None 时进入错题练习模式

        self._paper: List[Question] = []
        self._answers: Dict[int, str] = {}      # question_id → user_answer
        self._start_time: Optional[float] = None
        self._q_start_time: Optional[float] = None  # 当前题开始时间
        self._time_per_q: Dict[int, int] = {}   # question_id → 用时秒数
        self._finished = False

    # ── 出题 ──────────────────────────────────────────────────────────────────

    def generate_paper(self) -> List[Question]:
        """从题库随机抽题，返回题目列表。错题练习模式下按指定 ID 列表出题。"""
        # 错题练习模式：直接按 ID 列表查询
        if self.wrong_q_ids:
            placeholders = ','.join('?' * len(self.wrong_q_ids))
            rows = self._db.fetchall(
                f'SELECT * FROM questions WHERE id IN ({placeholders})',
                tuple(self.wrong_q_ids)
            )
            all_questions = [Question.from_row(r) for r in rows]
            random.shuffle(all_questions)
            self._paper = all_questions
            logger.info('错题练习模式：%d 题', len(self._paper))
            return self._paper

        # 普通模式：按题库/题型/分类筛选
        sql_parts = ['SELECT * FROM questions WHERE bank_id=?']
        params: List = [self.bank_id]

        if self.q_types:
            placeholders = ','.join('?' * len(self.q_types))
            sql_parts.append(f'AND q_type IN ({placeholders})')
            params.extend(self.q_types)

        if self.categories:
            placeholders = ','.join('?' * len(self.categories))
            sql_parts.append(f'AND category IN ({placeholders})')
            params.extend(self.categories)

        rows = self._db.fetchall(' '.join(sql_parts), tuple(params))
        all_questions = [Question.from_row(r) for r in rows]

        if not all_questions:
            logger.warning('题库 %d 中没有符合条件的题目', self.bank_id)
            return []

        # 随机抽取，不超过可用题目总数
        count = min(self.question_count, len(all_questions))
        self._paper = random.sample(all_questions, count)
        logger.info('生成试卷：%d 题（题库共 %d 题）', count, len(all_questions))
        return self._paper

    # ── 考试控制 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """记录考试开始时间"""
        self._start_time   = time.time()
        self._q_start_time = time.time()

    def mark_question_start(self, question_id: int) -> None:
        """切换到某题时记录开始时间，用于统计每题用时"""
        self._q_start_time = time.time()

    def submit_answer(self, question_id: int, answer: str) -> bool:
        """
        提交单题答案。
        返回是否正确。
        """
        # 记录该题用时
        if self._q_start_time is not None:
            elapsed = int(time.time() - self._q_start_time)
            self._time_per_q[question_id] = elapsed

        self._answers[question_id] = answer.strip()

        # 查找题目并判断正误
        for q in self._paper:
            if q.id == question_id:
                return q.check_answer(answer)
        return False

    def get_progress(self) -> Tuple[int, int]:
        """返回 (已答题数, 总题数)"""
        answered = sum(1 for q in self._paper if q.id in self._answers)
        return answered, len(self._paper)

    def get_remaining_time(self) -> Optional[int]:
        """返回剩余秒数；无时限返回 None；已超时返回 0"""
        if self.time_limit is None or self._start_time is None:
            return None
        elapsed = int(time.time() - self._start_time)
        remaining = self.time_limit - elapsed
        return max(0, remaining)

    def is_time_up(self) -> bool:
        """是否已超时"""
        remaining = self.get_remaining_time()
        return remaining is not None and remaining <= 0

    # ── 结束考试 ──────────────────────────────────────────────────────────────

    def finish(self) -> ExamResult:
        """
        结束考试，计算得分，将结果写入数据库。
        返回 ExamResult 汇总对象。
        """
        if self._finished:
            raise RuntimeError('考试已结束，不能重复调用 finish()')
        self._finished = True

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duration = int(time.time() - self._start_time) if self._start_time else 0

        # 逐题判分
        correct_ids: List[int] = []
        wrong_ids:   List[int] = []
        answer_records: List[ExamAnswer] = []

        for q in self._paper:
            user_ans = self._answers.get(q.id, '')   # 未作答视为空
            is_correct = q.check_answer(user_ans) if user_ans else False

            if is_correct:
                correct_ids.append(q.id)
            else:
                wrong_ids.append(q.id)

            answer_records.append(ExamAnswer(
                id=0,
                exam_id=0,
                question_id=q.id,
                user_answer=user_ans,
                is_correct=1 if is_correct else 0,
                time_spent=self._time_per_q.get(q.id, 0),
            ))

        total   = len(self._paper)
        correct = len(correct_ids)
        score   = round(correct / total * 100, 1) if total > 0 else 0.0

        # 写入 exams 表
        started_at = (
            datetime.fromtimestamp(self._start_time).strftime('%Y-%m-%d %H:%M:%S')
            if self._start_time else now
        )
        cursor = self._db.execute(
            '''INSERT INTO exams
               (bank_id, total_q, score, correct_count, wrong_count,
                duration_sec, time_limit, started_at, finished_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (self.bank_id, total, score, correct, total - correct,
             duration, self.time_limit, started_at, now)
        )
        exam_id = cursor.lastrowid

        # 批量写入 exam_answers 表
        self._db.executemany(
            '''INSERT INTO exam_answers
               (exam_id, question_id, user_answer, is_correct, time_spent)
               VALUES (?, ?, ?, ?, ?)''',
            [(exam_id, a.question_id, a.user_answer, a.is_correct, a.time_spent)
             for a in answer_records]
        )

        # 更新错题本
        self._update_wrong_book(wrong_ids, now)

        logger.info('考试结束：exam_id=%d, 得分=%.1f, 正确=%d/%d', exam_id, score, correct, total)

        return ExamResult(
            exam_id=exam_id,
            total=total,
            correct=correct,
            wrong=total - correct,
            score=score,
            duration_sec=duration,
            wrong_question_ids=wrong_ids,
            answers=answer_records,
        )

    def _update_wrong_book(self, wrong_ids: List[int], now: str) -> None:
        """将本次答错的题目更新到错题本"""
        for q_id in wrong_ids:
            user_ans = self._answers.get(q_id, '')
            existing = self._db.fetchone(
                'SELECT id, wrong_count FROM wrong_answers WHERE question_id=?',
                (q_id,)
            )
            if existing:
                # 已在错题本：累加错误次数，更新最近答案
                self._db.execute(
                    '''UPDATE wrong_answers
                       SET wrong_count=?, last_wrong=?, last_answer=?, is_mastered=0
                       WHERE question_id=?''',
                    (existing['wrong_count'] + 1, now, user_ans, q_id)
                )
            else:
                # 首次答错：插入新记录
                self._db.execute(
                    '''INSERT INTO wrong_answers
                       (question_id, wrong_count, last_wrong, last_answer)
                       VALUES (?, 1, ?, ?)''',
                    (q_id, now, user_ans)
                )
