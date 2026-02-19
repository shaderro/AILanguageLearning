#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
句子处理模块
提供句子分割功能
"""

import re
from typing import List, Optional

CHINESE_PUNCTUATION_PATTERN = r'(……|…|[。！？!?])'

# 缩写白名单（这些缩写后的句号不应该切句）
# 注意：_is_known_abbreviation 函数会将单词转为小写后比较，所以这里只需要小写形式
ABBREVIATION_WHITELIST = [
    # 德语常见缩写
    "z.b.", "u.a.", "etc.", "usw.", "ca.", "bzw.", "vgl.", "u.ä.",
    "d.h.", "i.e.", "e.g.", "z. b.", "u. a.", "u. ä.",
    # 职称和称谓（英文）- 包括 Dr., Mr., Mrs., Ms. 等
    "dr.", "mr.", "mrs.", "ms.", "miss.", "prof.", "rev.", "gen.", "capt.", 
    "lt.", "sgt.", "col.", "maj.", "adm.", "gov.", "sen.", "rep.", "pres.",
    "jr.", "sr.", "esq.", "ph.d.", "m.d.", "d.d.s.", "d.v.m.",
    # 地名和地址缩写（注意：dr. 在地址中表示 drive，与职称 dr. 相同但含义不同）
    "st.", "ave.", "blvd.", "rd.", "ln.", "ct.", "pl.", "pkwy.",
    "n.", "s.", "e.", "w.", "ne.", "nw.", "se.", "sw.",
    # 公司和组织
    "inc.", "ltd.", "llc.", "corp.", "co.", "assoc.", "dept.", "univ.",
    # 时间相关
    "a.m.", "p.m.", "b.c.", "a.d.", "b.c.e.", "c.e.",
    # 月份（英文）
    "jan.", "feb.", "mar.", "apr.", "may.", "jun.", "jul.", "aug.", 
    "sep.", "sept.", "oct.", "nov.", "dec.",
    # 月份（德语）
    "mär.", "okt.", "dez.",
    # 其他常见缩写
    "vs.", "et al.", "cf.", "viz.", "approx.",
    "no.", "vol.", "pp.", "p.", "ch.", "sec.", "fig.", "ex.", "ed.",
    "min.", "max.", "temp.",
]

# 日期模式
DATE_PATTERNS = [
    r"\d{1,2}\.\d{1,2}\.\d{2,4}",  # 数字日期：dd.mm.yyyy 或 dd.mm.yy
    r"\d{1,2}\.\s?(Jan\.|Feb\.|Mär\.|Apr\.|Mai|Jun[iy]?|Jul[iy]?|Aug\.|Sep\.|Okt\.|Nov\.|Dez\.)",  # 月份日期
]

# ==================== 判断函数（按优先级顺序） ====================

def _is_ellipsis(text: str, index: int) -> bool:
    """省略号保护：检查是否是 ..."""
    if index + 2 < len(text):
        return text[index:index+3] == "..."
    return False


def _is_numeric_dot(text: str, index: int) -> bool:
    """数字小数点（最高优先级）：检查前后是否都是数字"""
    if index > 0 and index + 1 < len(text):
        return text[index-1].isdigit() and text[index+1].isdigit()
    return False


def _is_ordinal_dot_de(text: str, index: int) -> bool:
    """
    德语序数点：检查是否是序数词后的句号（如 21. Jahrhundert）
    规则：前一个字符是数字，后一个字符是空格，再下一个字符是大写字母
    """
    if index == 0 or index + 1 >= len(text):
        return False
    
    if not text[index-1].isdigit():
        return False
    
    if text[index+1] != ' ':
        return False
    
    next_char = _next_non_space_char(text, index + 1)
    if next_char and next_char.isupper():
        return True
    
    return False


def _is_multi_letter_abbreviation(text: str, index: int) -> bool:
    """多字母缩写（B.C. / A.D. / U.S.A.）：匹配 ([A-Z]\\.){2,} 模式"""
    if index == 0:
        return False
    
    # 向前查找，匹配模式 ([A-Z]\.){2,}$
    pattern = r'([A-Z]\.){2,}$'
    text_before = text[:index+1]
    return bool(re.search(pattern, text_before))


def _is_single_letter_abbreviation(text: str, index: int) -> bool:
    """单字母缩写（J. K. Rowling）：前一个字符是大写字母，下一个非空格字符也是大写字母"""
    if index == 0 or index + 1 >= len(text):
        return False
    
    if not text[index-1].isupper():
        return False
    
    next_char = _next_non_space_char(text, index + 1)
    if next_char and next_char.isupper():
        return True
    
    return False


def _is_known_abbreviation(text: str, index: int) -> bool:
    """白名单缩写：检查句号前的单词是否在白名单中"""
    word = _get_word_ending_at(text, index).lower()
    # 检查带句号和不带句号的版本（因为 _get_word_ending_at 可能不包含句号）
    word_with_dot = word + "."
    is_match = word in ABBREVIATION_WHITELIST or word_with_dot in ABBREVIATION_WHITELIST
    # 调试日志（仅在需要时启用）
    # if is_match:
    #     print(f"[DEBUG] 匹配缩写: '{word}' 或 '{word_with_dot}' 在白名单中")
    return is_match


def _is_abbreviation_dot(text: str, index: int) -> bool:
    """缩写保护（统一入口）"""
    return (
        _is_multi_letter_abbreviation(text, index) or
        _is_single_letter_abbreviation(text, index) or
        _is_known_abbreviation(text, index)
    )


def _is_date_dot(text: str, index: int) -> bool:
    """日期格式保护：检查句号是否在日期模式中"""
    # 检查前后15个字符范围内是否匹配日期模式
    start = max(0, index - 15)
    end = min(len(text), index + 15)
    context = text[start:end]
    
    for pattern in DATE_PATTERNS:
        # 检查模式是否包含当前索引位置的句号
        matches = list(re.finditer(pattern, context))
        for match in matches:
            # 将相对位置转换为绝对位置
            match_start = start + match.start()
            match_end = start + match.end()
            if match_start <= index < match_end:
                return True
    
    return False


def _is_url_or_email_dot(text: str, index: int) -> bool:
    """URL / Email 保护：检查上下文是否包含 URL 或 Email 特征"""
    start = max(0, index - 15)
    end = min(len(text), index + 15)
    context = text[start:end].lower()
    
    return (
        "http" in context or
        "www." in context or
        ".com" in context or
        ".de" in context or
        ".org" in context or
        ".net" in context or
        "@" in context
    )


def _is_file_or_version_dot(text: str, index: int) -> bool:
    """文件名 / 版本号保护：检查是否是文件扩展名或版本号"""
    start = max(0, index - 20)
    end = min(len(text), index + 20)
    context = text[start:end]
    
    # 版本号模式：v1.2.3 或 1.2.3
    version_pattern = r'(v\d+(\.\d+)+)|(\d+(\.\d+){2,})'
    # 文件扩展名模式：filename.ext
    file_pattern = r'[a-zA-Z0-9_-]+\.[a-z]{2,4}'
    
    # 检查当前索引是否在匹配的模式内
    for pattern in [version_pattern, file_pattern]:
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        for match in matches:
            match_start = start + match.start()
            match_end = start + match.end()
            if match_start <= index < match_end:
                return True
    
    return False


def _next_char_does_not_start_sentence(text: str, index: int) -> bool:
    """
    语言级判断（最后一道门）：检查下一个字符是否不适合开始新句子
    返回 True 表示不应该切句，False 表示可以切句
    """
    next_char = _next_non_space_char(text, index + 1)
    
    if next_char is None:
        # 文本结束，应该切句（返回False表示"可以切句"）
        return False
    
    if next_char.islower():
        # 小写字母，不应该切句
        return True
    
    # 大写字母/数字/引号等，可以切句
    return False


def _should_split_here(text: str, index: int, paren_depth: int, is_german: bool = False) -> bool:
    """
    是否切句的统一入口（非常关键）
    按固定优先级检查，任何一条返回 true → 不切句
    只有全部通过 → 切句
    
    顺序：括号 → 省略号 → 数字 → 序数（仅德语）→ 缩写 → 日期 → URL/Email → 文件/版本 → 语言判断
    """
    # 1. 括号内禁止切句
    if paren_depth > 0:
        return False
    
    # 2. 省略号保护
    if _is_ellipsis(text, index):
        return False
    
    # 3. 数字小数点（最高优先级）
    if _is_numeric_dot(text, index):
        return False
    
    # 4. 德语序数点（仅德语）
    if is_german and _is_ordinal_dot_de(text, index):
        return False
    
    # 5. 缩写保护
    if _is_abbreviation_dot(text, index):
        return False
    
    # 6. 日期格式保护
    if _is_date_dot(text, index):
        return False
    
    # 7. URL / Email 保护
    if _is_url_or_email_dot(text, index):
        return False
    
    # 8. 文件名 / 版本号保护
    if _is_file_or_version_dot(text, index):
        return False
    
    # 9. 语言级判断（最后一道门）
    if _next_char_does_not_start_sentence(text, index):
        return False
    
    # 全部通过，可以切句
    return True


# ==================== 辅助函数 ====================

def _next_non_space_char(text: str, start: int) -> Optional[str]:
    """获取从 start 位置开始的第一个非空格字符"""
    for i in range(start, len(text)):
        if not text[i].isspace():
            return text[i]
    return None


def _get_word_ending_at(text: str, index: int) -> str:
    """获取在 index 位置（句号）前结束的单词"""
    if index == 0:
        return ""
    
    # 向前查找单词边界
    end = index
    start = end
    
    # 向前找到单词开始（字母、数字、连字符等）
    while start > 0 and (text[start-1].isalnum() or text[start-1] in '-.'):
        start -= 1
    
    return text[start:end].strip()


def _post_merge(sentences: List[str]) -> List[str]:
    """后处理：合并短缩写句"""
    if not sentences:
        return []
    
    merged = []
    for i, sentence in enumerate(sentences):
        if i > 0 and len(sentences[i-1].strip()) < 10:
            # 检查前一句是否以缩写结尾
            prev_stripped = sentences[i-1].rstrip()
            ends_with_abbrev = False
            for abbrev in ABBREVIATION_WHITELIST:
                if prev_stripped.lower().endswith(abbrev):
                    ends_with_abbrev = True
                    break
            
            if ends_with_abbrev:
                merged[-1] += " " + sentence
                continue
        
        merged.append(sentence)
    
    return merged


# ==================== 主流程 ====================

def _split_chinese_sentences(text: str) -> List[str]:
    """
    按照中文标点符号（。！？，问号、感叹号、以及“……”省略号等）进行分句
    """
    if not text:
        return []
    
    parts = re.split(CHINESE_PUNCTUATION_PATTERN, text)
    sentences: List[str] = []
    buffer = ""
    
    for part in parts:
        if part is None or part == "":
            continue
        buffer += part
        if re.fullmatch(CHINESE_PUNCTUATION_PATTERN, part):
            sentence = buffer.strip()
            if sentence:
                sentences.append(sentence)
            buffer = ""
    
    # 处理最后一段没有标点的文本
    tail = buffer.strip()
    if tail:
        sentences.append(tail)
    
    return sentences

def _split_whitespace_sentences(text: str, is_german: bool = False) -> List[str]:
    """
    分割空格语言的句子（英文/德文等）
    按照规范实现：逐字符扫描，只在遇到 . ? ! 时尝试切句
    
    Args:
        text: 输入的文本字符串
        is_german: 是否为德语（启用德语特殊规则）
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    sentences: List[str] = []
    current_sentence = ""
    paren_depth = 0
    
    for i in range(len(text)):
        char = text[i]
        current_sentence += char
        
        if char == '(':
            paren_depth += 1
            continue
        
        if char == ')':
            paren_depth = max(0, paren_depth - 1)
            continue
        
        if char in ['.', '?', '!']:
            if _should_split_here(text, i, paren_depth, is_german=is_german):
                sentence = current_sentence.strip()
                if sentence:
                    sentences.append(sentence)
                current_sentence = ""
    
    # 处理最后一段文本
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # 德语后处理：合并短缩写句
    if is_german:
        sentences = _post_merge(sentences)
    
    return sentences


def split_sentences(text: str, language_code: Optional[str] = None) -> List[str]:
    """
    将文本按句子分隔
    按照规范实现：逐字符扫描，只在遇到 . ? ! 时尝试切句
    
    Args:
        text: 输入的文本字符串
        language_code: 语言代码（如 "zh", "en", "de"）
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    # 🔧 如果 language_code 为 None，尝试自动检测（默认为英文）
    if language_code is None:
        # 检查是否包含中文字符
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            language_code = "zh"
        else:
            # 默认为英文，使用空格语言分句逻辑（包含缩写保护）
            language_code = "en"
    
    if language_code == "zh":
        return _split_chinese_sentences(text)
    
    # 空格语言（英文/德语等）使用统一实现
    # 注意：即使 language_code 为 None，也会使用英文分句逻辑（包含缩写保护）
    is_german = (language_code == "de")
    return _split_whitespace_sentences(text, is_german=is_german)

def read_and_split_sentences(file_path: str, language_code: Optional[str] = None) -> List[str]:
    """
    读取txt文件并返回分割后的句子列表
    
    Args:
        file_path: 文件路径
        
    Returns:
        List[str]: 分割后的句子列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return split_sentences(text, language_code=language_code)
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return [] 