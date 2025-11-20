#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token处理模块
提供token分割功能

支持两种分词模式：
1. 空格语言：按单词分词（word tokenization）
2. 非空格语言：按字符分词（character tokenization）
"""

import re
from typing import List, Dict, Any

def split_tokens(text: str, is_non_whitespace: bool = False) -> List[Dict[str, Any]]:
    """
    将文本分割成tokens，按照token_data.py中定义的数据结构
    
    Args:
        text: 输入的文本字符串
        is_non_whitespace: 是否为非空格语言（True=字符级别分词，False=单词级别分词）
        
    Returns:
        List[Dict[str, Any]]: 包含token_body和token_type的token列表
    """
    if not text:
        return []
    
    if is_non_whitespace:
        return split_tokens_char_level(text)
    else:
        return split_tokens_word_level(text)


def split_tokens_word_level(text: str) -> List[Dict[str, Any]]:
    """
    单词级别分词（用于空格语言：英文、德文等）
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[Dict[str, Any]]: 包含token_body和token_type的token列表
    """
    tokens = []
    
    # 使用正则表达式匹配不同类型的token
    # 匹配单词（包括连字符、撇号等）
    word_pattern = r'\b[\w\'-]+\b'
    # 匹配标点符号
    punctuation_pattern = r'[^\w\s]'
    # 匹配空白字符
    space_pattern = r'\s+'
    
    # 组合所有模式
    combined_pattern = f'({word_pattern})|({punctuation_pattern})|({space_pattern})'
    
    matches = re.finditer(combined_pattern, text)
    
    for match in matches:
        token_body = match.group(0)
        
        # 确定token类型
        if match.group(1):  # 单词
            token_type = "text"
        elif match.group(2):  # 标点符号
            token_type = "punctuation"
        elif match.group(3):  # 空白字符
            token_type = "space"
        else:
            continue  # 跳过不匹配的情况
        
        # 创建token字典，只包含前两项
        token = {
            "token_body": token_body,
            "token_type": token_type
        }
        
        tokens.append(token)
    
    return tokens


def split_tokens_char_level(text: str) -> List[Dict[str, Any]]:
    """
    字符级别分词（用于非空格语言：中文、日文等）
    
    将文本按字符分割，每个字符作为一个token（标点符号和空格单独处理）
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[Dict[str, Any]]: 包含token_body和token_type的token列表
    """
    tokens = []
    
    # 定义标点符号和空白字符的正则表达式
    # 匹配标点符号（包括中文标点）
    punctuation_pattern = r'[^\w\s\u4e00-\u9fff]'  # 非字母数字、非空白、非中文字符
    # 匹配空白字符
    space_pattern = r'\s+'
    
    i = 0
    while i < len(text):
        char = text[i]
        
        # 检查是否为空白字符
        if char.isspace():
            # 匹配连续的空白字符
            space_match = re.match(space_pattern, text[i:])
            if space_match:
                token_body = space_match.group(0)
                tokens.append({
                    "token_body": token_body,
                    "token_type": "space"
                })
                i += len(token_body)
                continue
        
        # 检查是否为标点符号
        if re.match(punctuation_pattern, char):
            tokens.append({
                "token_body": char,
                "token_type": "punctuation"
            })
            i += 1
            continue
        
        # 普通字符（包括中文字符、日文字符等）
        tokens.append({
            "token_body": char,
            "token_type": "text"
        })
        i += 1
    
    return tokens

def create_token_with_id(token_dict: Dict[str, Any], global_token_id: int, sentence_token_id: int) -> Dict[str, Any]:
    """
    为token添加ID信息
    
    Args:
        token_dict: 原始token字典
        global_token_id: 全局token ID
        sentence_token_id: 句子内token ID
        
    Returns:
        Dict[str, Any]: 包含ID信息的token字典
    """
    return {
        "token_body": token_dict["token_body"],
        "token_type": token_dict["token_type"],
        "global_token_id": global_token_id,
        "sentence_token_id": sentence_token_id
    } 