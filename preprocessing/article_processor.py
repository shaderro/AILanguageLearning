#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文章处理主模块
整合句子分割和token分割功能，处理整个文章并输出结构化数据
"""

import json
import os
from typing import Dict, Any, List
from .sentence_processor import split_sentences
from .token_processor import split_tokens, create_token_with_id

def process_article(raw_text: str, text_id: int = 1, text_title: str = "Article") -> Dict[str, Any]:
    """
    处理整个文章，将raw string转换为结构化数据
    
    Args:
        raw_text: 原始文章文本
        text_id: 文章ID
        text_title: 文章标题
        
    Returns:
        Dict[str, Any]: 结构化的文章数据
    """
    print(f"开始处理文章: {text_title}")
    print(f"文章ID: {text_id}")
    print(f"原始文本长度: {len(raw_text)} 字符")
    
    # 步骤1: 分割句子
    print("\n步骤1: 分割句子...")
    sentences_text = split_sentences(raw_text)
    print(f"分割得到 {len(sentences_text)} 个句子")
    
    # 步骤2: 为每个句子分割tokens并创建结构化数据
    print("\n步骤2: 分割tokens并创建结构化数据...")
    sentences = []
    global_token_id = 0
    
    for sentence_id, sentence_text in enumerate(sentences_text, 1):
        print(f"  处理句子 {sentence_id}/{len(sentences_text)}: {sentence_text[:50]}...")
        
        # 分割tokens
        token_dicts = split_tokens(sentence_text)
        
        # 为每个token添加ID
        tokens_with_id = []
        for token_id, token_dict in enumerate(token_dicts, 1):
            token_with_id = create_token_with_id(token_dict, global_token_id, token_id)
            tokens_with_id.append(token_with_id)
            global_token_id += 1
        
        # 创建句子数据
        sentence_data = {
            "sentence_id": sentence_id,
            "sentence_body": sentence_text,
            "tokens": tokens_with_id,
            "token_count": len(tokens_with_id)
        }
        
        sentences.append(sentence_data)
    
    # 步骤3: 创建最终结果
    print("\n步骤3: 创建结构化数据对象...")
    result = {
        "text_id": text_id,
        "text_title": text_title,
        "sentences": sentences,
        "total_sentences": len(sentences),
        "total_tokens": global_token_id
    }
    
    print(f"✅ 文章处理完成！")
    print(f"   总句子数: {len(sentences)}")
    print(f"   总token数: {global_token_id}")
    
    return result

def save_structured_data(result: Dict[str, Any], output_dir: str = "data"):
    """
    保存结构化数据到JSON文件
    
    Args:
        result: 结构化的文章数据
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建子目录
    text_dir = os.path.join(output_dir, f"text_{result['text_id']:03d}")
    os.makedirs(text_dir, exist_ok=True)
    
    # 保存original_text.json
    original_text_data = {
        "text_id": result["text_id"],
        "text_title": result["text_title"],
        "text_by_sentence": [
            {
                "text_id": result["text_id"],
                "sentence_id": sentence["sentence_id"],
                "sentence_body": sentence["sentence_body"],
                "grammar_annotations": [],
                "vocab_annotations": [],
                "tokens": sentence["tokens"]
            }
            for sentence in result["sentences"]
        ]
    }
    
    with open(os.path.join(text_dir, "original_text.json"), 'w', encoding='utf-8') as f:
        json.dump(original_text_data, f, ensure_ascii=False, indent=2)
    
    # 保存sentences.json
    sentences_data = [
        {
            "text_id": result["text_id"],
            "sentence_id": sentence["sentence_id"],
            "sentence_body": sentence["sentence_body"],
            "grammar_annotations": [],
            "vocab_annotations": [],
            "tokens": sentence["tokens"]
        }
        for sentence in result["sentences"]
    ]
    
    with open(os.path.join(text_dir, "sentences.json"), 'w', encoding='utf-8') as f:
        json.dump(sentences_data, f, ensure_ascii=False, indent=2)
    
    # 保存tokens.json (所有tokens的扁平化列表)
    all_tokens = []
    for sentence in result["sentences"]:
        for token in sentence["tokens"]:
            all_tokens.append({
                "token_body": token["token_body"],
                "token_type": token["token_type"],
                "difficulty_level": None,
                "global_token_id": token["global_token_id"],
                "sentence_token_id": token["sentence_token_id"],
                "sentence_id": sentence["sentence_id"],
                "text_id": result["text_id"],
                "linked_vocab_id": None,
                "pos_tag": None,
                "lemma": None,
                "is_grammar_marker": False
            })
    
    with open(os.path.join(text_dir, "tokens.json"), 'w', encoding='utf-8') as f:
        json.dump(all_tokens, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存到目录: {text_dir}")
    print(f"   生成文件:")
    print(f"   - original_text.json")
    print(f"   - sentences.json") 
    print(f"   - tokens.json")

def process_article_simple(raw_text: str) -> Dict[str, Any]:
    """
    简单处理文章：分割句子和tokens（简化版本）
    
    Args:
        raw_text: 原始文章文本
        
    Returns:
        Dict[str, Any]: 包含句子和tokens的结构化数据
    """
    print("=== 简单文章处理 ===")
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
            token_with_id = create_token_with_id(token, global_token_id, token_id)
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