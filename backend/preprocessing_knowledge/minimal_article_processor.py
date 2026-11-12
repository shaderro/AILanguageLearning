#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
最小化文章处理脚本
直接复制核心功能，不依赖其他模块
"""

import re
import json

def split_sentences(text: str):
    """
    将文本按句子分隔
    使用正则表达式匹配句号、问号、感叹号作为句子结束标记
    """
    # 使用正则表达式分割句子
    # 匹配句号、问号、感叹号，后面跟着空格或换行符
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # 过滤掉空字符串并去除首尾空白
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    
    return sentences

def split_tokens(text: str):
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

def process_article_minimal(raw_text: str):
    """
    最小化处理文章：分割句子和tokens
    
    Args:
        raw_text: 原始文章文本
        
    Returns:
        dict: 包含句子和tokens的结构化数据
    """
    print("=== 最小化文章处理 ===")
    print(f"原始文本长度: {len(raw_text)} 字符")
    
    # 步骤1: 分割句子
    print("\n1. 分割句子...")
    sentences = split_sentences(raw_text)
    print(f"分割得到 {len(sentences)} 个句子")
    
    # 步骤2: 为每个句子分割tokens
    print("\n2. 分割tokens...")
    result = {
        "sentences": [],
        "total_sentences": len(sentences),
        "total_tokens": 0
    }
    
    global_token_id = 0
    
    for sentence_id, sentence_text in enumerate(sentences, 1):
        print(f"  处理句子 {sentence_id}: {sentence_text[:50]}...")
        
        # 分割tokens
        tokens = split_tokens(sentence_text)
        
        # 为每个token添加ID
        tokens_with_id = []
        for token_id, token in enumerate(tokens, 1):
            token_with_id = {
                "token_body": token["token_body"],
                "token_type": token["token_type"],
                "global_token_id": global_token_id,
                "sentence_token_id": token_id
            }
            tokens_with_id.append(token_with_id)
            global_token_id += 1
        
        # 创建句子数据
        sentence_data = {
            "sentence_id": sentence_id,
            "sentence_body": sentence_text,
            "tokens": tokens_with_id,
            "token_count": len(tokens_with_id)
        }
        
        result["sentences"].append(sentence_data)
        result["total_tokens"] = global_token_id
    
    print(f"\n✅ 处理完成！")
    print(f"   总句子数: {result['total_sentences']}")
    print(f"   总token数: {result['total_tokens']}")
    
    return result

def save_result(result, filename="article_result.json"):
    """保存结果到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 结果已保存到: {filename}")

def main():
    """主函数"""
    # 示例文章
    article = """
    The quick brown fox jumps over the lazy dog. This is a classic pangram that contains every letter of the English alphabet at least once. Learning to code in Python is both fun and rewarding! 
    
    Natural language processing is an exciting field. It combines linguistics, computer science, and artificial intelligence. Researchers work on various tasks like text classification, sentiment analysis, and machine translation.
    """
    
    # 处理文章
    result = process_article_minimal(article)
    
    # 保存结果
    save_result(result)
    
    # 显示部分结果
    print("\n=== 处理结果预览 ===")
    for sentence in result["sentences"][:2]:  # 只显示前2个句子
        print(f"\n句子 {sentence['sentence_id']}: {sentence['sentence_body']}")
        print(f"Tokens ({sentence['token_count']}):")
        for token in sentence['tokens'][:5]:  # 只显示前5个tokens
            print(f"  [{token['global_token_id']}] '{token['token_body']}' ({token['token_type']})")

if __name__ == "__main__":
    main() 