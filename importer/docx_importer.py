# -*- coding: utf-8 -*-
"""
importer/docx_importer.py — Word 文件题库解析器

支持的 Word 题库格式（每题之间用空行分隔）：

    【单选题】
    1. 题干文本
    A. 选项A
    B. 选项B
    C. 选项C
    D. 选项D
    答案：B
    解析：可选解析文本
    分类：可选分类
    难度：1/2/3

    【多选题】 / 【判断题】 / 【场景题】 格式相同
"""

import logging
import re
from typing import Any, Dict, List, Optional

from importer.base_importer import BaseImporter

logger = logging.getLogger(__name__)

# 题型标记 → 内部标识符映射
TYPE_MAP = {
    '单选题': 'single',
    '多选题': 'multi',
    '判断题': 'truefalse',
    '场景题': 'scenario',
    '情景题': 'scenario',
}

# 选项行正则：匹配 "A." "A、" "A）" 等常见格式
OPTION_RE = re.compile(r'^([A-Ea-e])[.、）\)]\s*(.*)')

# 答案行正则
ANSWER_RE = re.compile(r'^答案[：:]\s*(.+)')

# 解析行正则
EXPLAIN_RE = re.compile(r'^解析[：:]\s*(.*)')

# 分类行正则
CATEGORY_RE = re.compile(r'^分类[：:]\s*(.*)')

# 难度行正则
DIFFICULTY_RE = re.compile(r'^难度[：:]\s*([123])')

# 题型标记行正则：匹配 【单选题】 等
TYPE_TAG_RE = re.compile(r'[【\[](.+?)[】\]]')

# 题干编号前缀正则：匹配 "1." "12." "（1）" 等，用于去除编号
STEM_NUM_RE = re.compile(r'^[\d（(]+[.、）)]\s*')


class DocxImporter(BaseImporter):
    """Word (.docx) 题库导入器"""

    def parse(self) -> List[Dict[str, Any]]:
        """解析 Word 文件，返回题目字典列表"""
        try:
            import docx  # python-docx
        except ImportError:
            raise ImportError('缺少依赖 python-docx，请运行: pip install python-docx')

        doc = docx.Document(self.filepath)

        # 提取所有非空段落文本
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        return self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """逐行解析，按题型标记分割题目块"""
        questions: List[Dict[str, Any]] = []
        current_type: str = 'single'    # 当前题型，默认单选
        current_block: List[str] = []   # 当前题目的行缓冲

        for line in lines:
            # 检测题型标记行（如 【单选题】）
            type_match = TYPE_TAG_RE.search(line)
            if type_match:
                tag = type_match.group(1)
                if tag in TYPE_MAP:
                    # 保存上一题
                    if current_block:
                        q = self._parse_block(current_block, current_type)
                        if q:
                            questions.append(q)
                        current_block = []
                    current_type = TYPE_MAP[tag]
                    continue

            # 空行作为题目分隔符
            if not line:
                if current_block:
                    q = self._parse_block(current_block, current_type)
                    if q:
                        questions.append(q)
                    current_block = []
                continue

            current_block.append(line)

        # 处理最后一题
        if current_block:
            q = self._parse_block(current_block, current_type)
            if q:
                questions.append(q)

        logger.info('Word 解析完成，共发现 %d 题', len(questions))
        return questions

    def _parse_block(self, block: List[str], q_type: str) -> Optional[Dict[str, Any]]:
        """
        解析单个题目块（一组连续行）。
        返回题目字典，解析失败返回 None。
        """
        q: Dict[str, Any] = {
            'q_type': q_type,
            'content': '',
            'option_a': '', 'option_b': '', 'option_c': '',
            'option_d': '', 'option_e': '',
            'correct_ans': '',
            'explanation': '',
            'category': '',
            'difficulty': 2,
        }

        stem_lines: List[str] = []   # 题干可能跨多行
        in_stem = True               # 是否还在读题干

        for line in block:
            # 答案行
            m = ANSWER_RE.match(line)
            if m:
                q['correct_ans'] = m.group(1).strip()
                in_stem = False
                continue

            # 解析行
            m = EXPLAIN_RE.match(line)
            if m:
                q['explanation'] = m.group(1).strip()
                in_stem = False
                continue

            # 分类行
            m = CATEGORY_RE.match(line)
            if m:
                q['category'] = m.group(1).strip()
                in_stem = False
                continue

            # 难度行
            m = DIFFICULTY_RE.match(line)
            if m:
                q['difficulty'] = int(m.group(1))
                in_stem = False
                continue

            # 选项行
            m = OPTION_RE.match(line)
            if m:
                letter = m.group(1).upper()
                text   = m.group(2).strip()
                key    = f'option_{letter.lower()}'
                if key in q:
                    q[key] = text
                in_stem = False
                continue

            # 其余行归入题干
            if in_stem:
                # 去除题干开头的序号（如 "1." "（1）"）
                clean = STEM_NUM_RE.sub('', line).strip()
                if clean:
                    stem_lines.append(clean)

        q['content'] = '\n'.join(stem_lines).strip()

        if not q['content'] or not q['correct_ans']:
            return None

        return q
