#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
句子处理模块
提供句子分割功能
"""

import re
from typing import List

def split_sentences(text: str) -> List[str]:
    """
    将文本按句子分隔
    使用正则表达式匹配句号、问号、感叹号作为句子结束标记
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        List[str]: 分割后的句子列表
    """
    if not text:
        return []
    
    # 使用正则表达式分割句子
    # 匹配句号、问号、感叹号，后面跟着空格或换行符
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # 过滤掉空字符串并去除首尾空白
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    
    return sentences

def read_and_split_sentences(file_path: str) -> List[str]:
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
        return split_sentences(text)
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return [] 