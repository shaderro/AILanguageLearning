#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
非空格语言分词模块
提供中文、日文等非空格语言的分词功能

当前实现：
- 中文分词：使用 jieba 库
- 日文分词：待实现（可使用 mecab 或 janome）
- 其他非空格语言：待实现
"""

import re
from typing import Any, Dict, List, Tuple, Optional

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("⚠️  警告: jieba 库未安装，中文分词功能将不可用")
    print("   安装方法: pip install jieba")


def Chinese_sentence_segmentation(sentence: str) -> List[Tuple[str, int, int]]:
    """
    中文句子分词
    
    使用 jieba 对中文句子进行分词，返回分词结果及其在原文中的位置信息
    
    Args:
        sentence: 输入的中文句子（字符串）
        
    Returns:
        List[Tuple[str, int, int]]: 分词结果列表
            - 每个元素为 (word, start_pos, end_pos)
            - word: 分词后的词（如 "喜欢"）
            - start_pos: 词在句子中的起始位置（字符索引）
            - end_pos: 词在句子中的结束位置（字符索引，不包含）
            
    Example:
        >>> sentence = "我喜欢学习编程"
        >>> result = Chinese_sentence_segmentation(sentence)
        >>> print(result)
        [('我', 0, 1), ('喜欢', 1, 3), ('学习', 3, 5), ('编程', 5, 7)]
    """
    if not JIEBA_AVAILABLE:
        raise ImportError("jieba 库未安装，无法进行中文分词。请运行: pip install jieba")
    
    if not sentence or not isinstance(sentence, str):
        return []
    
    # 使用 jieba 进行分词
    # jieba.cut 返回一个生成器，包含分词结果
    words = list(jieba.cut(sentence, cut_all=False))
    
    # 计算每个词在原文中的位置
    result = []
    current_pos = 0
    
    for word in words:
        if not word.strip():  # 跳过空白字符
            # 计算空白字符的长度
            whitespace_len = len(word)
            current_pos += whitespace_len
            continue
        
        # 在句子中查找该词的位置
        # 从 current_pos 开始查找，避免重复匹配
        word_start = sentence.find(word, current_pos)
        
        if word_start == -1:
            # 如果找不到（可能因为jieba分词结果与原文不完全匹配），使用当前位置
            word_start = current_pos
            word_end = current_pos + len(word)
        else:
            word_end = word_start + len(word)
        
        result.append((word, word_start, word_end))
        current_pos = word_end
    
    return result


def Chinese_sentence_segmentation_simple(sentence: str) -> List[str]:
    """
    中文句子分词（简化版，只返回词列表）
    
    Args:
        sentence: 输入的中文句子
        
    Returns:
        List[str]: 分词结果列表，每个元素是一个词
        
    Example:
        >>> sentence = "我喜欢学习编程"
        >>> result = Chinese_sentence_segmentation_simple(sentence)
        >>> print(result)
        ['我', '喜欢', '学习', '编程']
    """
    if not JIEBA_AVAILABLE:
        raise ImportError("jieba 库未安装，无法进行中文分词。请运行: pip install jieba")
    
    if not sentence or not isinstance(sentence, str):
        return []
    
    # 使用 jieba 进行分词，返回词列表
    words = list(jieba.cut(sentence, cut_all=False))
    
    # 过滤掉空白字符
    return [word for word in words if word.strip()]


def segment_chinese_text(text: str) -> List[Tuple[str, int, int]]:
    """
    对中文文本进行分词（支持多句子）
    
    先按句子分割，然后对每个句子进行分词
    
    Args:
        text: 输入的中文文本（可能包含多个句子）
        
    Returns:
        List[Tuple[str, int, int]]: 所有句子的分词结果
            - 每个元素为 (word, start_pos, end_pos)
            - start_pos 和 end_pos 是相对于整个文本的位置
    """
    if not JIEBA_AVAILABLE:
        raise ImportError("jieba 库未安装，无法进行中文分词。请运行: pip install jieba")
    
    if not text or not isinstance(text, str):
        return []
    
    # 简单的句子分割（按句号、问号、感叹号等分割）
    # 注意：这里使用简单的正则表达式，更复杂的句子分割可以使用 sentence_processor
    sentence_pattern = r'[。！？；\n]+'
    sentences = re.split(sentence_pattern, text)
    
    result = []
    text_offset = 0
    
    for sentence in sentences:
        if not sentence.strip():
            # 计算跳过的标点符号和空白字符的长度
            # 找到下一个句子的起始位置
            match = re.search(sentence_pattern, text[text_offset:])
            if match:
                text_offset += match.end()
            continue
        
        # 在当前文本中找到该句子的位置
        sentence_start = text.find(sentence, text_offset)
        if sentence_start == -1:
            sentence_start = text_offset
        
        # 对该句子进行分词
        words = Chinese_sentence_segmentation(sentence)
        
        # 调整位置偏移量（相对于整个文本）
        for word, start_pos, end_pos in words:
            result.append((
                word,
                sentence_start + start_pos,
                sentence_start + end_pos
            ))
        
        # 更新文本偏移量
        text_offset = sentence_start + len(sentence)
        
        # 跳过句子后的标点符号
        match = re.search(sentence_pattern, text[text_offset:])
        if match:
            text_offset += match.end()
    
    return result


def convert_segments_to_word_tokens(
    sentence_tokens: List[Dict[str, Any]],
    segments: List[Tuple[str, int, int]],
    starting_word_token_id: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[int, int], int]:
    """
    将分词结果转换为 word token 数据结构

    Args:
        sentence_tokens: 已生成的字符级 token 列表（包含 sentence_token_id）
        segments: 分词结果列表，每个元素为 (word, start_pos, end_pos)
        starting_word_token_id: 当前可用的 word_token_id（全局递增）

    Returns:
        Tuple:
            - word_tokens: [{word_token_id, word_body, token_ids, ...}, ...]
            - token_word_mapping: {sentence_token_id: word_token_id}
            - next_word_token_id: 下一个可用的 word_token_id
    """
    if not segments:
        return [], {}, starting_word_token_id

    # 构建字符位置到 sentence_token_id 的映射
    char_to_token_id: Dict[int, Optional[int]] = {}
    cursor = 0
    for token in sentence_tokens:
        token_body = token.get("token_body", "")
        sentence_token_id = token.get("sentence_token_id")
        if not token_body:
            continue
        length = len(token_body)
        for offset in range(length):
            char_to_token_id[cursor + offset] = sentence_token_id
        cursor += length

    word_tokens: List[Dict[str, Any]] = []
    token_word_mapping: Dict[int, int] = {}
    next_word_token_id = starting_word_token_id

    for word, start_pos, end_pos in segments:
        if word is None:
            continue
        if start_pos is None or end_pos is None or start_pos >= end_pos:
            continue

        token_ids: List[int] = []
        for idx in range(start_pos, end_pos):
            sentence_token_id = char_to_token_id.get(idx)
            if sentence_token_id is None:
                continue
            if not token_ids or token_ids[-1] != sentence_token_id:
                token_ids.append(sentence_token_id)

        if not token_ids:
            continue

        word_token = {
            "word_token_id": next_word_token_id,
            "word_body": word,
            "token_ids": token_ids,
            "pos_tag": None,
            "lemma": None,
            "linked_vocab_id": None,
        }
        word_tokens.append(word_token)

        for sentence_token_id in token_ids:
            token_word_mapping[sentence_token_id] = next_word_token_id

        next_word_token_id += 1

    return word_tokens, token_word_mapping, next_word_token_id


# 日文分词功能（待实现）
def Japanese_sentence_segmentation(sentence: str) -> List[Tuple[str, int, int]]:
    """
    日文句子分词（待实现）
    
    可以使用 mecab 或 janome 库实现
    
    Args:
        sentence: 输入的日文句子
        
    Returns:
        List[Tuple[str, int, int]]: 分词结果列表
    """
    # TODO: 实现日文分词
    raise NotImplementedError("日文分词功能尚未实现")


# 测试代码
if __name__ == "__main__":
    # 测试中文分词
    if JIEBA_AVAILABLE:
        print("=" * 60)
        print("测试中文分词功能")
        print("=" * 60)
        
        test_sentences = [
            "我喜欢学习编程",
            "今天天气真好。",
            "这是一个测试句子，包含标点符号！",
            "自然语言处理是人工智能的重要分支。"
        ]
        
        for sentence in test_sentences:
            print(f"\n原文: {sentence}")
            print(f"长度: {len(sentence)} 字符")
            
            # 测试带位置信息的分词
            result = Chinese_sentence_segmentation(sentence)
            print(f"分词结果（带位置）: {result}")
            
            # 测试简化版分词
            simple_result = Chinese_sentence_segmentation_simple(sentence)
            print(f"分词结果（简化）: {simple_result}")
            print("-" * 60)
    else:
        print("⚠️  jieba 库未安装，无法运行测试")
        print("   安装方法: pip install jieba")

