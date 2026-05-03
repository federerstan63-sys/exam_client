# -*- coding: utf-8 -*-
"""
core/stats_engine.py — 统计分析引擎
提供考试历史查询、错题本管理、得分趋势等统计功能。
"""

import logging
from typing import List, Optional, Tuple

from database.db_manager import DBManager
from database.models import ExamAnswer, ExamRecord, Question, WrongAnswerEntry

logger = logging.getLogger(__name__)


class StatsEngine:
    """统计分析引擎"""

    def __init__(self):
        self._db = DBManager.get_instance()

    # ── 考试历史 ──────────────────────────────────────────────────────────────

    def get_exam_history(self, limit: int = 50) -> List[ExamRecord]:
        """返回最近 limit 条考试记录（含题库名称）"""
        rows = self._db.fetchall(
            '''SELECT e.*, COALESCE(b.name, '已删除题库') AS bank_name
               FROM exams e
               LEFT JOIN question_banks b ON e.bank_id = b.id
               ORDER BY e.started_at DESC
               LIMIT ?''',
            (limit,)
        )
        records = []
        for r in rows:
            rec = ExamRecord.from_row(r)
            rec.bank_name = r['bank_name']
            records.append(rec)
        return records

    def get_exam_detail(self, exam_id: int) -> Tuple[Optional[ExamRecord], List[ExamAnswer], List[Question]]:
        """
        返回单次考试的详细信息。
        返回 (考试记录, 答题明细列表, 对应题目列表)
        """
        row = self._db.fetchone(
            '''SELECT e.*, COALESCE(b.name, '已删除题库') AS bank_name
               FROM exams e
               LEFT JOIN question_banks b ON e.bank_id = b.id
               WHERE e.id=?''',
            (exam_id,)
        )
        if not row:
            return None, [], []

        exam = ExamRecord.from_row(row)
        exam.bank_name = row['bank_name']

        answer_rows = self._db.fetchall(
            'SELECT * FROM exam_answers WHERE exam_id=? ORDER BY id',
            (exam_id,)
        )
        answers = [ExamAnswer.from_row(r) for r in answer_rows]

        # 批量查询对应题目
        if answers:
            q_ids = [a.question_id for a in answers]
            placeholders = ','.join('?' * len(q_ids))
            q_rows = self._db.fetchall(
                f'SELECT * FROM questions WHERE id IN ({placeholders})',
                tuple(q_ids)
            )
            # 按 id 建索引，保持与 answers 顺序一致
            q_map = {r['id']: Question.from_row(r) for r in q_rows}
            questions = [q_map.get(a.question_id) for a in answers if q_map.get(a.question_id)]
        else:
            questions = []

        return exam, answers, questions

    def get_score_trend(self, limit: int = 20) -> List[Tuple[str, float]]:
        """
        返回最近 limit 次考试的得分趋势。
        返回 [(日期字符串, 分数), ...] 按时间升序。
        """
        rows = self._db.fetchall(
            '''SELECT substr(started_at, 1, 10) AS exam_date, score
               FROM exams
               ORDER BY started_at DESC
               LIMIT ?''',
            (limit,)
        )
        # 反转为升序
        return [(r['exam_date'], r['score']) for r in reversed(rows)]

    # ── 错题本 ────────────────────────────────────────────────────────────────

    def get_wrong_questions(self, hide_mastered: bool = True) -> List[WrongAnswerEntry]:
        """
        返回错题本列表（含关联题目信息）。
        hide_mastered=True 时过滤掉已标记为掌握的题目。
        """
        if hide_mastered:
            rows = self._db.fetchall(
                '''SELECT wa.*, q.content, q.q_type, q.correct_ans,
                          q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
                          q.explanation, q.category, q.difficulty, q.bank_id, q.created_at
                   FROM wrong_answers wa
                   JOIN questions q ON wa.question_id = q.id
                   WHERE wa.is_mastered = 0
                   ORDER BY wa.wrong_count DESC, wa.last_wrong DESC'''
            )
        else:
            rows = self._db.fetchall(
                '''SELECT wa.*, q.content, q.q_type, q.correct_ans,
                          q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
                          q.explanation, q.category, q.difficulty, q.bank_id, q.created_at
                   FROM wrong_answers wa
                   JOIN questions q ON wa.question_id = q.id
                   ORDER BY wa.wrong_count DESC, wa.last_wrong DESC'''
            )

        entries = []
        for r in rows:
            entry = WrongAnswerEntry.from_row(r)
            # 手动构建关联的 Question 对象
            entry.question = Question(
                id=r['question_id'],
                bank_id=r['bank_id'],
                q_type=r['q_type'],
                content=r['content'],
                option_a=r['option_a'],
                option_b=r['option_b'],
                option_c=r['option_c'],
                option_d=r['option_d'],
                option_e=r['option_e'],
                correct_ans=r['correct_ans'],
                explanation=r['explanation'],
                category=r['category'] or '',
                difficulty=r['difficulty'],
                created_at=r['created_at'],
            )
            entries.append(entry)
        return entries

    def mark_mastered(self, question_id: int) -> None:
        """将错题标记为已掌握"""
        self._db.execute(
            'UPDATE wrong_answers SET is_mastered=1 WHERE question_id=?',
            (question_id,)
        )

    def unmark_mastered(self, question_id: int) -> None:
        """取消已掌握标记"""
        self._db.execute(
            'UPDATE wrong_answers SET is_mastered=0 WHERE question_id=?',
            (question_id,)
        )

    def delete_wrong_entry(self, question_id: int) -> None:
        """从错题本中删除某题"""
        self._db.execute(
            'DELETE FROM wrong_answers WHERE question_id=?',
            (question_id,)
        )

    # ── 总览统计 ──────────────────────────────────────────────────────────────

    def get_overview(self) -> dict:
        """
        返回首页仪表盘所需的汇总数据。
        包含：题库总题数、考试总次数、平均分、错题数。
        """
        total_q = self._db.fetchone('SELECT COUNT(*) AS cnt FROM questions')
        total_exams = self._db.fetchone('SELECT COUNT(*) AS cnt FROM exams')
        avg_score = self._db.fetchone('SELECT AVG(score) AS avg FROM exams')
        wrong_cnt = self._db.fetchone(
            'SELECT COUNT(*) AS cnt FROM wrong_answers WHERE is_mastered=0'
        )
        return {
            'total_questions': total_q['cnt'] if total_q else 0,
            'total_exams':     total_exams['cnt'] if total_exams else 0,
            'avg_score':       round(avg_score['avg'] or 0, 1),
            'wrong_count':     wrong_cnt['cnt'] if wrong_cnt else 0,
        }

    def get_bank_stats(self, bank_id: int) -> dict:
        """返回指定题库的题型分布统计"""
        rows = self._db.fetchall(
            '''SELECT q_type, COUNT(*) AS cnt
               FROM questions WHERE bank_id=?
               GROUP BY q_type''',
            (bank_id,)
        )
        return {r['q_type']: r['cnt'] for r in rows}
