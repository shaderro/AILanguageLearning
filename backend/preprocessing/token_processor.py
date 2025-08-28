#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token处理模块
提供token分割功能
"""

import re
from typing import List, Dict, Any

def split_tokens(text: str) -> List[Dict[str, Any]]:
    """
    将文本分割成tokens，按照token_data.py中定义的数据结构
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[Dict[str, Any]]: 包含token_body和token_type的token列表
    """
    if not text:
        return []
    
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