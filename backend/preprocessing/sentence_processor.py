#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
句子处理模块
提供句子分割功能
"""

import re
from typing import List, Optional

CHINESE_PUNCTUATION_PATTERN = r'(……|…|[。！？!?])'

# 德语缩写白名单（这些缩写后的句号不应该切句）
GERMAN_ABBREV_WHITELIST = [
    "z.B.", "u.a.", "etc.", "usw.", "ca.", "bzw.", "vgl.", "u.ä.", 
    "Dr.", "Prof.", "Dipl.-Ing.", 
    "Jan.", "Feb.", "Mär.", "Apr.", "Aug.", "Sep.", "Okt.", "Nov.", "Dez.",
    "Mai", "Jun", "Juni", "Jul", "Juli",  # 月份（有些没有句号）
    "d.h.", "i.e.", "e.g.", "z. B.", "u. a.", "u. ä.",  # 带空格的变体
    "bzw", "ca", "usw", "etc",  # 不带句号的变体（保险起见）
]

# 德语日期模式
GERMAN_DATE_PATTERNS = [
    r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",  # 数字日期：dd.mm.yyyy 或 dd.mm.yy
    r"\b\d{1,2}\.\s?(Jan\.|Feb\.|Mär\.|Apr\.|Mai|Jun[iy]?|Jul[iy]?|Aug\.|Sep\.|Okt\.|Nov\.|Dez\.)\b",  # 月份日期
]

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

def _split_whitespace_sentences(text: str) -> List[str]:
    """
    分割空格语言的句子（英文/德文等）
    规则：括号内禁止切句，括号内的句号、冒号、分号不视为句子结束
    
    实现方式：
    - 扫描字符串，遇到 ( → 括号层级 +1
    - 在括号层级 > 0 期间的所有句号、冒号、分号都禁止切句
    - 遇到 ) → 括号层级 -1
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    sentences: List[str] = []
    current_sentence = ""
    paren_level = 0  # 括号层级计数：遇到 ( 时 +1，遇到 ) 时 -1
    
    i = 0
    while i < len(text):
        char = text[i]
        
        # 处理左括号：启动括号层级计数
        if char == '(':
            paren_level += 1
            current_sentence += char
        # 处理右括号：括号层级 -1
        elif char == ')':
            if paren_level > 0:  # 防止括号不匹配导致负数
                paren_level -= 1
            current_sentence += char
        # 处理句子结束标记（句号、问号、感叹号）
        elif char in '.!?':
            current_sentence += char
            # 只有在括号层级为 0 时，才允许切句
            if paren_level == 0:
                # 检查后面是否有空格（用于判断是否是句子结束）
                # 跳过当前字符后的空白字符
                j = i + 1
                while j < len(text) and text[j].isspace():
                    j += 1
                
                # 如果后面有内容或者是文本结束，则切句
                if j >= len(text) or text[j].isalnum() or text[j] in '"\'':
                    sentence = current_sentence.strip()
                    if sentence:
                        sentences.append(sentence)
                    current_sentence = ""
                    i = j - 1  # 跳过已处理的空白字符
            # 如果 paren_level > 0，则继续添加到当前句子（不切句）
        # 处理冒号和分号（在括号内时禁止切句，括号外也不切句）
        elif char in ':;':
            current_sentence += char
            # 冒号和分号本身就不切句，但需要确保在括号内时也不切句
            # 这里只是添加到当前句子，不进行切句操作
        else:
            current_sentence += char
        
        i += 1
    
    # 处理最后一段文本
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    return sentences

def _split_german_sentences(text: str) -> List[str]:
    """
    分割德语句子，应用德语特殊规则
    
    规则：
    1. 不要在已知德语缩写后切句
    2. 不要在日期后切句（数字日期和月份日期）
    3. 如果下一个句子以小写字母开头，不要切句
    4. 括号内禁止切句
    5. 合并过程：合并以缩写结尾的短句、合并括号跨段的句子
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    # 第一步：初始分割（考虑括号、缩写、日期、小写字母）
    sentences: List[str] = []
    current_sentence = ""
    paren_level = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        
        # 处理括号
        if char == '(':
            paren_level += 1
            current_sentence += char
        elif char == ')':
            if paren_level > 0:
                paren_level -= 1
            current_sentence += char
        # 处理句子结束标记
        elif char in '.!?':
            current_sentence += char
            
            # 只有在括号层级为 0 时，才考虑切句
            if paren_level == 0:
                # 检查是否是德语缩写
                is_abbrev = False
                sentence_so_far = current_sentence.rstrip()
                for abbrev in GERMAN_ABBREV_WHITELIST:
                    # 检查当前句子末尾是否以该缩写结尾（考虑大小写）
                    if sentence_so_far.endswith(abbrev) or sentence_so_far.endswith(abbrev.lower()):
                        is_abbrev = True
                        break
                
                # 检查是否是日期（只在句号时检查）
                is_date = False
                if char == '.':
                    sentence_end = sentence_so_far
                    for pattern in GERMAN_DATE_PATTERNS:
                        if re.search(pattern + r'$', sentence_end, re.IGNORECASE):
                            is_date = True
                            break
                
                # 如果既不是缩写也不是日期，检查是否可以切句
                if not is_abbrev and not is_date:
                    # 检查后面是否有空格，以及下一个字符
                    j = i + 1
                    while j < len(text) and text[j].isspace():
                        j += 1
                    
                    # 如果文本结束，则切句
                    if j >= len(text):
                        sentence = current_sentence.strip()
                        if sentence:
                            sentences.append(sentence)
                        current_sentence = ""
                    # 如果下一个字符是小写字母，不切句（规则3）
                    elif text[j].islower():
                        # 不切句，继续添加到当前句子
                        pass
                    # 如果下一个字符是大写字母/数字/引号，则切句
                    elif text[j].isupper() or text[j].isdigit() or text[j] in '"\'':
                        sentence = current_sentence.strip()
                        if sentence:
                            sentences.append(sentence)
                        current_sentence = ""
                        i = j - 1  # 跳过已处理的空白字符
            # 如果 paren_level > 0，则继续添加到当前句子（不切句）
        elif char in ':;':
            current_sentence += char
        else:
            current_sentence += char
        
        i += 1
    
    # 处理最后一段文本
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # 第二步：合并过程
    merged_sentences: List[str] = []
    i = 0
    while i < len(sentences):
        current = sentences[i]
        
        # 检查是否需要与下一句合并
        if i < len(sentences) - 1:
            next_sentence = sentences[i + 1]
            should_merge = False
            
            # 规则1：如果当前句子以缩写结尾，合并
            current_stripped = current.rstrip()
            for abbrev in GERMAN_ABBREV_WHITELIST:
                if current_stripped.endswith(abbrev) or current_stripped.endswith(abbrev.lower()):
                    should_merge = True
                    break
            
            # 规则2：如果当前句子少于10个字符，合并
            if len(current.strip()) < 10:
                should_merge = True
            
            # 规则3：如果括号在前一句打开，在下一句关闭，合并
            open_count = current.count('(') - current.count(')')
            if open_count > 0 and ')' in next_sentence:
                should_merge = True
            
            if should_merge:
                # 合并当前句子和下一句
                merged = current + " " + next_sentence
                merged_sentences.append(merged)
                i += 2  # 跳过下一句，因为已经合并
                continue
        
        # 不需要合并，直接添加
        merged_sentences.append(current)
        i += 1
    
    return merged_sentences

def split_sentences(text: str, language_code: Optional[str] = None) -> List[str]:
    """
    将文本按句子分隔
    使用正则表达式匹配句号、问号、感叹号作为句子结束标记
    
    Args:
        text: 输入的文本字符串
        language_code: 语言代码（如 "zh", "en", "de"）
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    if language_code == "zh":
        return _split_chinese_sentences(text)
    
    if language_code == "de":
        return _split_german_sentences(text)
    
    # 使用增强的分句逻辑（支持括号内禁止切句）
    return _split_whitespace_sentences(text)

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