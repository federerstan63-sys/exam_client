# -*- coding: utf-8 -*-
"""
database/db_manager.py — 数据库连接管理与初始化
使用单例模式管理 SQLite 连接，提供统一的增删查改接口。
"""

import sqlite3
import logging
from typing import List, Optional, Tuple, Any

logger = logging.getLogger(__name__)
# logging.getLogger(__name__)：
#   获取以当前模块名（'database.db_manager'）命名的记录器
#   这样日志输出中可以看到是哪个模块产生的日志


class DBManager:
    """
    SQLite 数据库管理器，使用单例模式（Singleton Pattern）。

    单例模式的含义：整个程序运行期间只存在一个 DBManager 实例，
    所有模块都通过 DBManager.get_instance() 获取同一个对象，
    共享同一个数据库连接，避免重复建立连接的开销。

    使用方式：
      1. 程序启动时调用一次：DBManager.initialize(db_path)
      2. 之后任何地方获取实例：db = DBManager.get_instance()
      3. 使用实例方法进行数据库操作：db.fetchall(sql, params)
    """

    _instance: Optional['DBManager'] = None
    # 类变量（不是实例变量），存储唯一的 DBManager 实例
    # Optional['DBManager']：类型注解，值可以是 DBManager 对象或 None
    # 初始为 None，表示尚未初始化

    def __init__(self, db_path: str):
        """
        构造函数（私有，不应直接调用，请使用 initialize() 方法）。
        db_path：SQLite 数据库文件的绝对路径
        """
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        # _conn：数据库连接对象，初始为 None，_connect() 后才有值

    @classmethod
    def get_instance(cls) -> 'DBManager':
        """
        获取单例实例。

        @classmethod 说明：
          - cls 指向类本身（DBManager），而不是某个实例
          - 可以通过 DBManager.get_instance() 直接调用

        如果 initialize() 还没被调用（_instance 为 None），则抛出异常，
        防止在数据库未初始化时就尝试使用。
        """
        if cls._instance is None:
            raise RuntimeError('DBManager 尚未初始化，请先调用 DBManager.initialize()')
        return cls._instance

    @classmethod
    def initialize(cls, db_path: str) -> 'DBManager':
        """
        初始化单例并建表，程序启动时调用一次。

        幂等性：如果已经初始化过（_instance 不为 None），直接返回现有实例，
        不会重复建立连接或重复建表。

        执行顺序：
          1. 创建 DBManager 实例
          2. 建立数据库连接（_connect）
          3. 创建所有数据表（_create_tables）
          4. 写入默认设置（_seed_settings）
        """
        if cls._instance is None:
            cls._instance = cls(db_path)   # 调用 __init__，创建实例
            cls._instance._connect()        # 建立 SQLite 连接
            cls._instance._create_tables()  # 建表（已存在则跳过）
            cls._instance._seed_settings()  # 写入默认配置
        return cls._instance

    # ── 连接管理 ──────────────────────────────────────────────────────────────

    def _connect(self) -> None:
        """
        建立 SQLite 数据库连接，并配置性能和安全选项。

        参数说明：
          check_same_thread=False：
            SQLite 默认只允许创建连接的线程使用该连接。
            设为 False 允许多线程共用同一连接（导入功能在后台线程运行时需要）。
            注意：需要自行保证线程安全（本项目通过 tkinter 的 after() 回调保证）。

          row_factory = sqlite3.Row：
            让查询结果支持按列名访问，如 row['id']，而不只是 row[0]。
            这使代码更易读，也不容易因列顺序变化而出错。

          PRAGMA journal_mode=WAL：
            WAL（Write-Ahead Logging）是 SQLite 的一种日志模式。
            相比默认的 DELETE 模式，WAL 允许读写并发，性能更好。

          PRAGMA foreign_keys=ON：
            SQLite 默认不检查外键约束，需要手动开启。
            开启后，如果插入的外键值在父表中不存在，会报错。
        """
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row   # 让查询结果支持按列名访问
        self._conn.execute('PRAGMA journal_mode=WAL')   # 开启 WAL 模式提升并发性能
        self._conn.execute('PRAGMA foreign_keys=ON')    # 开启外键约束检查

    def close(self) -> None:
        """
        关闭数据库连接，程序退出时调用（在 App._on_close 中调用）。
        关闭后将 _conn 置为 None，防止后续误用已关闭的连接。
        """
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── 建表 ──────────────────────────────────────────────────────────────────

    def _create_tables(self) -> None:
        """
        创建所有数据表。

        CREATE TABLE IF NOT EXISTS：
          如果表已存在则跳过，不会报错也不会清空数据。
          这使得 initialize() 可以安全地多次调用（幂等）。

        数据库表结构说明：
          question_banks — 题库元数据（每个导入的文件对应一行）
          questions      — 题目（每道题对应一行，通过 bank_id 关联题库）
          exams          — 考试记录（每次考试对应一行）
          exam_answers   — 答题明细（每道题的作答情况，通过 exam_id 关联考试）
          wrong_answers  — 错题本（每道错题一行，UNIQUE 约束防止重复）
          app_settings   — 应用设置键值对（主题、字体大小等）

        REFERENCES 关键字定义外键关系，如：
          bank_id INTEGER NOT NULL REFERENCES question_banks(id)
          表示 bank_id 必须是 question_banks 表中存在的 id 值
        """
        ddl_statements = [
            # 题库元数据表
            """
            CREATE TABLE IF NOT EXISTS question_banks (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT    NOT NULL,
                source_file    TEXT    NOT NULL,
                file_type      TEXT    NOT NULL,
                imported_at    TEXT    NOT NULL,
                question_count INTEGER DEFAULT 0,
                is_active      INTEGER DEFAULT 1
            )
            """,
            # 题目表
            """
            CREATE TABLE IF NOT EXISTS questions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id      INTEGER NOT NULL REFERENCES question_banks(id),
                q_type       TEXT    NOT NULL,
                content      TEXT    NOT NULL,
                option_a     TEXT,
                option_b     TEXT,
                option_c     TEXT,
                option_d     TEXT,
                option_e     TEXT,
                correct_ans  TEXT    NOT NULL,
                explanation  TEXT,
                category     TEXT    DEFAULT '',
                difficulty   INTEGER DEFAULT 2,
                created_at   TEXT    NOT NULL
            )
            """,
            # 考试记录表
            """
            CREATE TABLE IF NOT EXISTS exams (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id       INTEGER REFERENCES question_banks(id),
                total_q       INTEGER NOT NULL,
                score         REAL    NOT NULL,
                correct_count INTEGER NOT NULL,
                wrong_count   INTEGER NOT NULL,
                duration_sec  INTEGER NOT NULL,
                time_limit    INTEGER,
                started_at    TEXT    NOT NULL,
                finished_at   TEXT    NOT NULL
            )
            """,
            # 考试答题明细表（每道题一行）
            """
            CREATE TABLE IF NOT EXISTS exam_answers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id     INTEGER NOT NULL REFERENCES exams(id),
                question_id INTEGER NOT NULL REFERENCES questions(id),
                user_answer TEXT    NOT NULL,
                is_correct  INTEGER NOT NULL,
                time_spent  INTEGER DEFAULT 0
            )
            """,
            # 错题本表（每道题只保留一条记录，重复答错则更新计数）
            # UNIQUE 约束：question_id 不能重复，保证每题只有一条错题记录
            """
            CREATE TABLE IF NOT EXISTS wrong_answers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL REFERENCES questions(id) UNIQUE,
                wrong_count INTEGER DEFAULT 1,
                last_wrong  TEXT    NOT NULL,
                last_answer TEXT    NOT NULL,
                is_mastered INTEGER DEFAULT 0
            )
            """,
            # 应用设置键值对表（key 为主键，保证每个设置项唯一）
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
        ]
        for ddl in ddl_statements:
            self._conn.execute(ddl)   # 逐条执行建表语句
        self._conn.commit()           # 提交事务，使建表操作生效

    def _seed_settings(self) -> None:
        """
        写入默认应用设置（已存在则忽略，不覆盖用户修改过的值）。

        INSERT OR IGNORE：
          如果 key 已存在（违反 PRIMARY KEY 约束），则静默忽略该行，
          不报错也不更新。这保证了默认值只在首次运行时写入。

        executemany：
          批量执行同一条 SQL，参数是一个列表，比循环调用 execute 更高效。
        """
        defaults = [
            ('theme',                  'light'),  # 主题：浅色
            ('font_size',              '11'),      # 字体大小
            ('default_time_limit',     '60'),      # 默认时间限制（分钟）
            ('default_question_count', '50'),      # 默认出题数量
        ]
        self._conn.executemany(
            'INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)',
            defaults
        )
        self._conn.commit()

    # ── 通用查询接口 ──────────────────────────────────────────────────────────

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        执行写操作（INSERT / UPDATE / DELETE），自动提交事务。

        参数化查询（? 占位符）：
          SQL 中用 ? 代替实际值，params 元组提供对应的值。
          这是防止 SQL 注入攻击的标准做法，绝对不要用字符串拼接 SQL。
          示例：execute('INSERT INTO t (a) VALUES (?)', ('value',))

        返回值：sqlite3.Cursor 对象
          - 对于 INSERT 操作，可通过 cursor.lastrowid 获取新插入行的 ID
          - 对于 UPDATE/DELETE，可通过 cursor.rowcount 获取影响的行数
        """
        cursor = self._conn.execute(sql, params)
        self._conn.commit()   # 立即提交，确保数据持久化到磁盘
        return cursor

    def executemany(self, sql: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """
        批量执行写操作，自动提交。

        params_list：包含多个参数元组的列表，每个元组对应一次执行。
        比循环调用 execute() 更高效，因为只提交一次事务。

        示例：
          executemany('INSERT INTO t (a, b) VALUES (?, ?)', [(1, 'x'), (2, 'y')])
        """
        cursor = self._conn.executemany(sql, params_list)
        self._conn.commit()
        return cursor

    def fetchall(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        执行 SELECT 查询，返回所有匹配行的列表。

        返回值：List[sqlite3.Row]
          每个 Row 对象支持 row['列名'] 访问（因为设置了 row_factory）。
          如果没有匹配行，返回空列表 []。
        """
        return self._conn.execute(sql, params).fetchall()

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """
        执行 SELECT 查询，只返回第一行。

        适用于：
          - 按主键查询（结果唯一）
          - 只需要一条记录的场景（如 COUNT、AVG 聚合查询）

        返回值：sqlite3.Row 或 None（无匹配行时返回 None）
        """
        return self._conn.execute(sql, params).fetchone()

    def get_setting(self, key: str, default: str = '') -> str:
        """
        读取应用设置值。

        参数：
          key     — 设置项的键名（如 'theme'、'font_size'）
          default — 键不存在时的默认返回值

        返回值：设置值字符串，或 default（键不存在时）
        """
        row = self.fetchone('SELECT value FROM app_settings WHERE key=?', (key,))
        return row['value'] if row else default
        # row['value']：从查询结果中取 value 列的值
        # if row else default：row 为 None（未找到）时返回默认值

    def set_setting(self, key: str, value: str) -> None:
        """
        写入或更新应用设置。

        INSERT OR REPLACE：
          如果 key 已存在，则先删除旧行再插入新行（相当于 UPSERT）。
          与 INSERT OR IGNORE 不同，这里会覆盖已有值。
        """
        self.execute(
            'INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)',
            (key, value)
        )
