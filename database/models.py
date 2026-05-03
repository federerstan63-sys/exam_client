# -*- coding: utf-8 -*-
"""
database/models.py — 数据模型
将数据库行映射为 Python dataclass，方便在业务层和 UI 层传递数据。
"""

from dataclasses import dataclass, field
# dataclass：装饰器，自动为类生成 __init__、__repr__、__eq__ 等方法
# field：用于给 dataclass 字段设置默认值工厂（如 default_factory=list）

from typing import Optional, List
# Optional[X]：表示该值可以是 X 类型，也可以是 None
# List[X]：表示元素类型为 X 的列表

import sqlite3
# sqlite3.Row：查询结果行对象，支持按列名访问，如 row['id']


@dataclass
class QuestionBank:
    """
    题库元数据，对应数据库 question_banks 表的一行记录。
    每导入一个文件就会创建一条 QuestionBank 记录。
    """
    id: int              # 题库唯一 ID（数据库自增主键）
    name: str            # 题库名称（用户自定义，如"2024年真题"）
    source_file: str     # 原始文件名（如 "题库.xlsx"）
    file_type: str       # 文件类型：'docx'（Word）或 'xlsx'（Excel）
    imported_at: str     # 导入时间，ISO8601 格式字符串（如 "2024-01-01 12:00:00"）
    question_count: int  # 该题库包含的题目总数
    is_active: int       # 是否有效：1=正常可用，0=已软删除（不显示但数据保留）

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'QuestionBank':
        """
        类方法：从数据库查询结果行构造 QuestionBank 对象。

        @classmethod 说明：
          - 第一个参数是 cls（类本身），而不是 self（实例）
          - 可以通过 QuestionBank.from_row(row) 调用，不需要先创建实例
          - 这是一种常见的"工厂方法"模式

        sqlite3.Row 支持 row['列名'] 的字典式访问，比下标访问更清晰。
        返回值类型写成字符串 'QuestionBank' 是因为类还未定义完，
        Python 3.10+ 可以直接写 QuestionBank，旧版本需要用字符串。
        """
        return cls(
            id=row['id'],
            name=row['name'],
            source_file=row['source_file'],
            file_type=row['file_type'],
            imported_at=row['imported_at'],
            question_count=row['question_count'],
            is_active=row['is_active'],
        )


@dataclass
class Question:
    """
    题目数据，对应数据库 questions 表的一行记录。
    是整个系统最核心的数据结构，贯穿导入、考试、学习、错题本各模块。
    """
    id: int                    # 题目唯一 ID（数据库自增主键）
    bank_id: int               # 所属题库 ID（外键，关联 question_banks.id）
    q_type: str                # 题型：'single'=单选 | 'multi'=多选 | 'truefalse'=判断 | 'scenario'=场景
    content: str               # 题干文字（题目正文）
    option_a: Optional[str]    # 选项 A 的文字，判断题为 None
    option_b: Optional[str]    # 选项 B 的文字
    option_c: Optional[str]    # 选项 C 的文字（可选，不足时为 None）
    option_d: Optional[str]    # 选项 D 的文字（可选）
    option_e: Optional[str]    # 选项 E 的文字（可选，最多支持 5 个选项）
    correct_ans: str           # 正确答案：单选='A'/'B'/... | 多选='AB'/'ACD'/... | 判断='True'/'False'
    explanation: Optional[str] # 题目解析文字（可为空）
    category: str              # 所属分类（如"第一章"，空字符串表示未分类）
    difficulty: int            # 难度等级：1=易，2=中，3=难
    created_at: str            # 创建时间（导入时写入）

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Question':
        """从数据库行构造 Question 对象（工厂方法，同 QuestionBank.from_row）"""
        return cls(
            id=row['id'],
            bank_id=row['bank_id'],
            q_type=row['q_type'],
            content=row['content'],
            option_a=row['option_a'],
            option_b=row['option_b'],
            option_c=row['option_c'],
            option_d=row['option_d'],
            option_e=row['option_e'],
            correct_ans=row['correct_ans'],
            explanation=row['explanation'],
            category=row['category'] or '',
            # row['category'] 可能为 None（数据库 NULL），用 or '' 转为空字符串
            difficulty=row['difficulty'],
            created_at=row['created_at'],
        )

    def get_options(self) -> List[tuple]:
        """
        返回该题目的选项列表，格式为 [(字母, 文本), ...]。

        处理逻辑：
          - 判断题（truefalse）：固定返回 [('True', '正确'), ('False', '错误')]
          - 其他题型：从 option_a~e 中过滤掉空值，只返回有内容的选项

        示例返回值：
          单选题 → [('A', '选项内容'), ('B', '选项内容'), ('C', '选项内容')]
          判断题 → [('True', '正确'), ('False', '错误')]
        """
        if self.q_type == 'truefalse':
            return [('True', '正确'), ('False', '错误')]

        # 构建所有可能的选项对，然后过滤掉文本为空的
        pairs = [
            ('A', self.option_a),
            ('B', self.option_b),
            ('C', self.option_c),
            ('D', self.option_d),
            ('E', self.option_e),
        ]
        # 列表推导式：只保留 v（选项文本）不为空的项
        return [(k, v) for k, v in pairs if v]

    def check_answer(self, user_answer: str) -> bool:
        """
        判断用户答案是否正确。

        比较规则：
          - 忽略大小写（统一转为大写后比较）
          - 多选题忽略字母顺序（用集合 set 比较，'AB' == 'BA'）
          - 判断题：'True'/'False' 与正确答案比较

        参数：
          user_answer — 用户提交的答案字符串，如 'A'、'AB'、'True'

        返回值：
          True = 答对，False = 答错
        """
        correct = set(self.correct_ans.upper())  # 将正确答案转为字符集合，如 'AB' → {'A','B'}
        given   = set(user_answer.upper())        # 将用户答案转为字符集合
        return correct == given                   # 集合相等则答对（顺序无关）


@dataclass
class ExamRecord:
    """
    考试记录，对应数据库 exams 表的一行。
    每次完成考试（调用 ExamEngine.finish()）都会写入一条记录。
    """
    id: int                  # 考试记录唯一 ID
    bank_id: Optional[int]   # 使用的题库 ID（错题练习模式下为 None）
    total_q: int             # 本次考试总题数
    score: float             # 得分（百分制，如 85.5）
    correct_count: int       # 答对题数
    wrong_count: int         # 答错题数
    duration_sec: int        # 考试用时（秒）
    time_limit: Optional[int]# 设定的时间限制（秒），None 表示无限制
    started_at: str          # 考试开始时间
    finished_at: str         # 考试结束时间
    bank_name: str = ''      # 题库名称（不在数据库中，通过 JOIN 查询后手动填充）

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'ExamRecord':
        """从数据库行构造 ExamRecord 对象"""
        return cls(
            id=row['id'],
            bank_id=row['bank_id'],
            total_q=row['total_q'],
            score=row['score'],
            correct_count=row['correct_count'],
            wrong_count=row['wrong_count'],
            duration_sec=row['duration_sec'],
            time_limit=row['time_limit'],
            started_at=row['started_at'],
            finished_at=row['finished_at'],
        )


@dataclass
class ExamAnswer:
    """
    单题作答记录，对应数据库 exam_answers 表的一行。
    每次考试结束后，每道题都会写入一条 ExamAnswer 记录。
    """
    id: int           # 记录唯一 ID
    exam_id: int      # 所属考试 ID（外键，关联 exams.id）
    question_id: int  # 对应题目 ID（外键，关联 questions.id）
    user_answer: str  # 用户提交的答案（空字符串表示未作答）
    is_correct: int   # 是否答对：1=正确，0=错误（用整数而非布尔，方便 SQL 统计）
    time_spent: int   # 该题用时（秒）

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'ExamAnswer':
        """从数据库行构造 ExamAnswer 对象"""
        return cls(
            id=row['id'],
            exam_id=row['exam_id'],
            question_id=row['question_id'],
            user_answer=row['user_answer'],
            is_correct=row['is_correct'],
            time_spent=row['time_spent'],
        )


@dataclass
class WrongAnswerEntry:
    """
    错题本条目，对应数据库 wrong_answers 表的一行。
    每道题在错题本中只保留一条记录，重复答错时更新计数而不新增行。
    """
    id: int              # 记录唯一 ID
    question_id: int     # 对应题目 ID（UNIQUE 约束，每题只有一条错题记录）
    wrong_count: int     # 累计答错次数
    last_wrong: str      # 最近一次答错的时间
    last_answer: str     # 最近一次提交的错误答案
    is_mastered: int     # 是否已掌握：0=待复习，1=已标记为掌握
    question: Optional['Question'] = None
    # 关联的题目对象，不在数据库中存储
    # 通过 JOIN 查询后手动构建并赋值（见 StatsEngine.get_wrong_questions）
    # 默认值 None，dataclass 中带默认值的字段必须放在无默认值字段之后

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'WrongAnswerEntry':
        """从数据库行构造 WrongAnswerEntry 对象（不含关联的 question）"""
        return cls(
            id=row['id'],
            question_id=row['question_id'],
            wrong_count=row['wrong_count'],
            last_wrong=row['last_wrong'],
            last_answer=row['last_answer'],
            is_mastered=row['is_mastered'],
        )


@dataclass
class ExamResult:
    """
    考试结束后的汇总结果，仅在内存中传递，不直接对应数据库表。
    由 ExamEngine.finish() 创建，传递给 ExamResultFrame 显示。
    """
    exam_id: int                   # 本次考试在数据库中的 ID（finish() 写入后获得）
    total: int                     # 总题数
    correct: int                   # 答对题数
    wrong: int                     # 答错题数
    score: float                   # 得分（百分制）
    duration_sec: int              # 考试用时（秒）
    wrong_question_ids: List[int] = field(default_factory=list)
    # 答错的题目 ID 列表，用于错题本更新
    # field(default_factory=list)：每次创建实例时都生成一个新的空列表
    # 不能写 wrong_question_ids: List[int] = []，因为列表是可变对象，
    # 所有实例会共享同一个列表（Python 的常见陷阱）
    answers: List[ExamAnswer] = field(default_factory=list)
    # 所有题目的作答明细列表，用于结果页面展示
