# -*- coding: utf-8 -*-
"""
importer/base_importer.py — 导入器基类
定义所有导入器的公共接口和数据库写入逻辑。
"""

import logging
from abc import ABC, abstractmethod
# abc 模块：Abstract Base Class（抽象基类）
# ABC：继承它的类变成抽象类，不能直接实例化
# abstractmethod：装饰器，标记必须由子类实现的抽象方法

from datetime import datetime   # 用于获取当前时间并格式化为字符串
from typing import Any, Dict, List, Optional, Tuple

from database.db_manager import DBManager

logger = logging.getLogger(__name__)

# 合法的题型标识符集合（用于校验导入数据）
VALID_TYPES = {'single', 'multi', 'truefalse', 'scenario'}
# 使用集合（set）而非列表（list），因为 in 操作在集合中是 O(1)，列表是 O(n)


class BaseImporter(ABC):
    """
    题库导入器基类（抽象类）。

    设计模式：模板方法模式（Template Method Pattern）
      - 基类定义了导入流程的骨架：parse() → validate() → save_to_db()
      - 子类只需实现 parse() 方法，处理不同文件格式的解析逻辑
      - 数据校验和数据库写入逻辑在基类中统一实现，子类无需重复

    子类：
      - XlsxImporter：解析 Excel (.xlsx) 文件
      - DocxImporter：解析 Word (.docx) 文件
    """

    def __init__(self, filepath: str, bank_name: str):
        """
        初始化导入器。

        参数：
          filepath  — 要导入的文件绝对路径
          bank_name — 用户输入的题库名称（空时使用默认名）
        """
        self.filepath  = filepath
        self.bank_name = bank_name.strip() or '未命名题库'
        # str.strip()：去除首尾空白字符
        # or '未命名题库'：如果 strip() 后为空字符串（空字符串是 falsy），则使用默认名
        self._db       = DBManager.get_instance()

    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        """
        解析文件，返回题目字典列表（抽象方法，子类必须实现）。

        @abstractmethod 说明：
          - 标记为抽象方法后，BaseImporter 不能直接实例化
          - 子类如果不实现此方法，也不能实例化（Python 会报 TypeError）
          - 这强制所有子类都提供自己的解析实现

        返回值格式：每个字典的键对应 questions 表字段：
          {
            'q_type':      str,           # 题型
            'content':     str,           # 题干
            'option_a':    str,           # 选项 A（可为空字符串）
            'option_b':    str,           # 选项 B
            'option_c':    str,           # 选项 C（可选）
            'option_d':    str,           # 选项 D（可选）
            'option_e':    str,           # 选项 E（可选）
            'correct_ans': str,           # 正确答案
            'explanation': str,           # 解析（可为空）
            'category':    str,           # 分类（可为空）
            'difficulty':  int,           # 难度 1/2/3
          }
        """
        ...
        # ... 是 Python 中的 Ellipsis 字面量，在抽象方法体中作为占位符使用
        # 等价于 pass，但语义上更明确表示"此处由子类实现"

    def validate_question(self, q: Dict[str, Any]) -> Tuple[bool, str]:
        """
        校验单题数据的完整性和合法性。

        返回值：(是否合法, 错误描述)
          - (True, '')        — 数据合法
          - (False, '原因')   — 数据不合法，附带原因说明

        校验规则：
          1. 题干不能为空
          2. 题型必须是 VALID_TYPES 中的一种
          3. 答案不能为空
          4. 选择题（单选/多选/场景）至少需要 A、B 两个选项
          5. 多选题答案至少包含两个字母
          6. 判断题答案只能是规定的几种写法
        """
        # 规则 1：题干不能为空
        if not q.get('content', '').strip():
            return False, '题干为空'
        # q.get('content', '')：安全获取字典值，键不存在时返回 ''
        # .strip()：去除首尾空白后判断是否为空

        # 规则 2：题型必须合法
        q_type = q.get('q_type', '')
        if q_type not in VALID_TYPES:
            return False, f'未知题型: {q_type}'
        # f-string：Python 3.6+ 的格式化字符串，{变量} 会被替换为实际值

        # 规则 3：答案不能为空
        if not q.get('correct_ans', '').strip():
            return False, '答案为空'

        # 规则 4：选择题至少需要 A、B 两个选项
        if q_type in ('single', 'multi', 'scenario'):
            if not q.get('option_a') or not q.get('option_b'):
                return False, '选择题至少需要 A、B 两个选项'

        # 规则 5：多选题答案至少两个字母（如 'AB'、'ACD'）
        if q_type == 'multi':
            ans = q.get('correct_ans', '')
            if len(ans) < 2:
                return False, f'多选题答案 "{ans}" 少于两个选项'

        # 规则 6：判断题答案格式校验
        if q_type == 'truefalse':
            ans = q.get('correct_ans', '').strip().lower()
            # .lower()：转为小写，方便统一比较
            if ans not in ('true', 'false', '正确', '错误', '对', '错', '√', '×'):
                return False, f'判断题答案 "{ans}" 不合法'

        return True, ''   # 所有校验通过

    def _normalize_truefalse_answer(self, ans: str) -> str:
        """
        将各种判断题答案写法统一为标准格式 'True' 或 'False'。

        支持的输入格式：
          True  方向：'true', '正确', '对', '√', '是'
          False 方向：'false', '错误', '错', '×', '否'

        mapping.get(key, default)：
          在字典中查找 key，找不到时返回 default（这里返回原始值 ans）。
          这样即使遇到未知格式也不会崩溃，只是保持原样。
        """
        mapping = {
            'true':  'True',  '正确': 'True',  '对': 'True',  '√': 'True',  '是': 'True',
            'false': 'False', '错误': 'False', '错': 'False', '×': 'False', '否': 'False',
        }
        return mapping.get(ans.strip().lower(), ans)
        # ans.strip().lower()：先去空白再转小写，作为字典查找的 key

    def save_to_db(self, questions: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """
        将解析出的题目列表写入数据库。

        执行流程：
          1. 先插入题库记录（question_banks 表），获取 bank_id
          2. 逐题校验 → 格式化 → 插入 questions 表
          3. 更新题库的实际题目数量
          4. 如果一题都没导入成功，删除空题库记录（回滚）

        返回值：(成功数, 失败数, 错误信息列表)
          - 成功数：成功写入数据库的题目数量
          - 失败数：校验不通过或写入失败的题目数量
          - 错误信息列表：每条失败的原因说明
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # datetime.now()：获取当前本地时间
        # .strftime(格式)：将时间格式化为字符串
        #   %Y=四位年, %m=两位月, %d=两位日, %H=小时, %M=分钟, %S=秒

        file_type = self.filepath.rsplit('.', 1)[-1].lower()
        # rsplit('.', 1)：从右边按 '.' 分割，最多分割 1 次
        #   'path/to/file.xlsx'.rsplit('.', 1) → ['path/to/file', 'xlsx']
        # [-1]：取最后一个元素（扩展名）
        # .lower()：转小写，统一为 'xlsx' 或 'docx'

        # 先插入题库记录，获取 bank_id（后续题目需要引用此 ID）
        cursor = self._db.execute(
            '''INSERT INTO question_banks
               (name, source_file, file_type, imported_at, question_count)
               VALUES (?, ?, ?, ?, 0)''',
            (self.bank_name,
             self.filepath.split('/')[-1].split('\\')[-1],
             # 兼容 Linux/Mac（/）和 Windows（\）路径分隔符，取文件名部分
             file_type,
             now)
        )
        bank_id = cursor.lastrowid
        # cursor.lastrowid：INSERT 操作后，获取新插入行的自增 ID

        success, fail = 0, 0   # 成功/失败计数器
        errors: List[str] = [] # 错误信息收集列表

        for idx, q in enumerate(questions, start=1):
            # enumerate(iterable, start=1)：
            #   同时获取索引和元素，start=1 使索引从 1 开始（更符合"第几题"的表述）

            ok, msg = self.validate_question(q)
            if not ok:
                fail += 1
                errors.append(f'第 {idx} 题跳过：{msg}')
                logger.warning('题目 %d 校验失败：%s', idx, msg)
                continue   # 跳过当前题目，继续处理下一题

            # 统一判断题答案格式（'正确' → 'True'，'错误' → 'False'）
            if q.get('q_type') == 'truefalse':
                q['correct_ans'] = self._normalize_truefalse_answer(q['correct_ans'])

            # 选择题答案字母统一大写并去除空格（'a b' → 'AB'）
            if q.get('q_type') != 'truefalse':
                q['correct_ans'] = q['correct_ans'].upper().replace(' ', '')

            try:
                self._db.execute(
                    '''INSERT INTO questions
                       (bank_id, q_type, content, option_a, option_b, option_c,
                        option_d, option_e, correct_ans, explanation, category,
                        difficulty, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        bank_id,
                        q.get('q_type', 'single'),
                        q['content'].strip(),
                        q.get('option_a', ''),   # 键不存在时用空字符串
                        q.get('option_b', ''),
                        q.get('option_c', ''),
                        q.get('option_d', ''),
                        q.get('option_e', ''),
                        q['correct_ans'],
                        q.get('explanation', ''),
                        q.get('category', ''),
                        int(q.get('difficulty', 2)),  # 转为整数，默认难度 2（中等）
                        now,
                    )
                )
                success += 1
            except Exception as e:
                # 捕获所有异常（数据库约束违反、类型错误等）
                fail += 1
                errors.append(f'第 {idx} 题写入失败：{e}')
                logger.error('题目 %d 写入数据库失败：%s', idx, e)

        # 更新题库记录中的实际题目数量（之前插入时写的是 0）
        self._db.execute(
            'UPDATE question_banks SET question_count=? WHERE id=?',
            (success, bank_id)
        )

        # 如果一题都没导入成功，删除空题库记录（避免留下无用的空题库）
        if success == 0:
            self._db.execute('DELETE FROM question_banks WHERE id=?', (bank_id,))

        return success, fail, errors
