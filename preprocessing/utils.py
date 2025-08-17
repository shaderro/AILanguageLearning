#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块
提供文章处理相关的辅助功能
"""

import json
import os
from typing import Dict, Any, List

def save_result(result: Dict[str, Any], filename: str = "article_result.json"):
    """
    保存结果到JSON文件
    
    Args:
        result: 处理结果
        filename: 输出文件名
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 结果已保存到: {filename}")

def load_result(filename: str) -> Dict[str, Any]:
    """
    从JSON文件加载结果
    
    Args:
        filename: 输入文件名
        
    Returns:
        Dict[str, Any]: 加载的结果
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_result_summary(result: Dict[str, Any]):
    """
    打印结果摘要
    
    Args:
        result: 处理结果
    """
    print("\n=== 处理结果摘要 ===")
    print(f"总句子数: {result.get('total_sentences', 0)}")
    print(f"总token数: {result.get('total_tokens', 0)}")
    
    if 'sentences' in result:
        print(f"\n前3个句子预览:")
        for i, sentence in enumerate(result['sentences'][:3], 1):
            print(f"  句子 {i}: {sentence['sentence_body'][:50]}...")
            print(f"    Tokens: {sentence.get('token_count', 0)} 个")

def get_token_statistics(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取token统计信息
    
    Args:
        result: 处理结果
        
    Returns:
        Dict[str, Any]: 统计信息
    """
    if 'sentences' not in result:
        return {}
    
    text_tokens = 0
    punctuation_tokens = 0
    space_tokens = 0
    
    for sentence in result['sentences']:
        for token in sentence['tokens']:
            token_type = token['token_type']
            if token_type == 'text':
                text_tokens += 1
            elif token_type == 'punctuation':
                punctuation_tokens += 1
            elif token_type == 'space':
                space_tokens += 1
    
    return {
        'text_tokens': text_tokens,
        'punctuation_tokens': punctuation_tokens,
        'space_tokens': space_tokens,
        'total_tokens': text_tokens + punctuation_tokens + space_tokens
    }

def validate_result(result: Dict[str, Any]) -> bool:
    """
    验证处理结果的有效性
    
    Args:
        result: 处理结果
        
    Returns:
        bool: 是否有效
    """
    required_keys = ['sentences', 'total_sentences', 'total_tokens']
    
    # 检查必需字段
    for key in required_keys:
        if key not in result:
            print(f"❌ 缺少必需字段: {key}")
            return False
    
    # 检查句子数量
    if len(result['sentences']) != result['total_sentences']:
        print(f"❌ 句子数量不匹配: 实际 {len(result['sentences'])}, 声明 {result['total_sentences']}")
        return False
    
    # 检查token数量
    actual_tokens = sum(sentence.get('token_count', 0) for sentence in result['sentences'])
    if actual_tokens != result['total_tokens']:
        print(f"❌ Token数量不匹配: 实际 {actual_tokens}, 声明 {result['total_tokens']}")
        return False
    
    print("✅ 结果验证通过")
    return True 