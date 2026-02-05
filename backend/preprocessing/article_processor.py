#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文章处理主模块
整合句子分割和token分割功能，处理整个文章并输出结构化数据
"""

import json
import os
from typing import Dict, Any, List, Optional
from .sentence_processor import split_sentences
from .token_processor import split_tokens, create_token_with_id
from .language_classification import (
    is_non_whitespace_language,
    get_language_code,
    get_language_category
)
from .word_segmentation import word_segmentation

ENABLE_DEBUG_LOGGING = True

def process_article(
    raw_text: str, 
    text_id: int = 1, 
    text_title: str = "Article",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理整个文章，将raw string转换为结构化数据
    
    Args:
        raw_text: 原始文章文本
        text_id: 文章ID
        text_title: 文章标题
        language: 文章语言（如 "中文", "英文", "德文" 或 ISO 代码如 "zh", "en", "de"）
        
    Returns:
        Dict[str, Any]: 结构化的文章数据
    """
    print(f"开始处理文章: {text_title}")
    print(f"文章ID: {text_id}")
    print(f"原始文本长度: {len(raw_text)} 字符")
    
    # 检查语言类型
    language_code = get_language_code(language) if language else None
    is_non_whitespace = is_non_whitespace_language(language_code) if language_code else False
    language_category = get_language_category(language_code) if language_code else "unknown"
    
    print(f"语言: {language} (代码: {language_code}, 类型: {language_category})")
    if is_non_whitespace:
        print("⚠️  检测到非空格语言，将使用字符级别分词（word token 功能待实现）")
    else:
        print("✅ 检测到空格语言，使用单词级别分词")
    
    # 步骤1: 分割句子
    print("\n步骤1: 分割句子...")
    sentences_list = split_sentences(raw_text, language_code=language_code)
    print(f"分割得到 {len(sentences_list)} 个句子")
    
    # 步骤2: 为每个句子分割tokens并创建结构化数据
    print("\n步骤2: 分割tokens并创建结构化数据...")
    sentences = []
    global_token_id = 0
    global_word_token_id = 1
    
    for sentence_id, sentence_text in enumerate(sentences_list, 1):
        print(f"  处理句子 {sentence_id}/{len(sentences_list)}: {sentence_text[:50]}...")
        
        # 分割tokens（根据语言类型选择分词方式）
        token_dicts = split_tokens(sentence_text, is_non_whitespace=is_non_whitespace)
        
        # 为每个token添加ID
        tokens_with_id = []
        for token_id, token_dict in enumerate(token_dicts, 1):
            token_with_id = create_token_with_id(token_dict, global_token_id, token_id)
            tokens_with_id.append(token_with_id)
            global_token_id += 1

        sentence_word_tokens: List[Dict[str, Any]] = []
        if language_code == "zh":
            sentence_word_tokens, token_word_mapping, global_word_token_id = word_segmentation(
                language_code,
                sentence_text,
                tokens_with_id,
                global_word_token_id
            )
            if sentence_word_tokens:
                for token in tokens_with_id:
                    mapped_id = token_word_mapping.get(token["sentence_token_id"])
                    if mapped_id is not None:
                        token["word_token_id"] = mapped_id
                print(f"    - 生成 {len(sentence_word_tokens)} 个 word tokens")
        
        # 创建句子数据
        sentence_data = {
            "sentence_id": sentence_id,
            "sentence_body": sentence_text,
            "tokens": tokens_with_id,
            "word_tokens": sentence_word_tokens,
            "token_count": len(tokens_with_id)
        }
        
        sentences.append(sentence_data)
    
    # 步骤3: 创建最终结果
    print("\n步骤3: 创建结构化数据对象...")
    result = {
        "text_id": text_id,
        "text_title": text_title,
        "language": language,  # 保存语言信息
        "language_code": language_code,  # 保存语言代码
        "language_category": language_category,  # 保存语言分类
        "is_non_whitespace": is_non_whitespace,  # 是否为非空格语言
        "sentences": sentences,
        "total_sentences": len(sentences),
        "total_tokens": global_token_id,
        "total_word_tokens": global_word_token_id - 1 if global_word_token_id > 1 else 0
    }
    
    if language_code == "zh":
        _print_chinese_segmentation_debug(result)
    
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
                "tokens": sentence["tokens"],
                "word_tokens": sentence.get("word_tokens", [])
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
            "tokens": sentence["tokens"],
            "word_tokens": sentence.get("word_tokens", [])
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
                "is_grammar_marker": False,
                "word_token_id": token.get("word_token_id")
            })
    
    with open(os.path.join(text_dir, "tokens.json"), 'w', encoding='utf-8') as f:
        json.dump(all_tokens, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存到目录: {text_dir}")
    print(f"   生成文件:")
    print(f"   - original_text.json")
    print(f"   - sentences.json") 
    print(f"   - tokens.json")

def _print_chinese_segmentation_debug(result: Dict[str, Any]):
    if not ENABLE_DEBUG_LOGGING:
        return
    sentences = result.get("sentences", [])
    print("\n🔍 中文分词调试数据（基础流程）:")
    print(f"   - 总 sentence 数: {len(sentences)}")
    print(f"   - 总字级 token 数: {result.get('total_tokens', 0)}")
    print(f"   - 总 word token 数: {result.get('total_word_tokens', 0)}")
    for sentence in sentences:
        print(f"\n[Sentence {sentence.get('sentence_id')}] {sentence.get('sentence_body')}")
        print("  · 字级 tokens:")
        for token in sentence.get("tokens", []):
            print(
                f"      - token[{token['sentence_token_id']:>2}] "
                f"body='{token['token_body']}' type={token['token_type']} "
                f"word_token_id={token.get('word_token_id')}"
            )
        word_tokens = sentence.get("word_tokens") or []
        if word_tokens:
            print("  · word tokens:")
            for word_token in word_tokens:
                print(
                    f"      - word_token[{word_token['word_token_id']:>2}] "
                    f"body='{word_token['word_body']}' "
                    f"token_ids={word_token.get('token_ids')}"
                )

def process_article_simple(
    raw_text: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    简单处理文章：分割句子和tokens（简化版本）
    
    Args:
        raw_text: 原始文章文本
        language: 文章语言（如 "中文", "英文", "德文" 或 ISO 代码如 "zh", "en", "de"）
        
    Returns:
        Dict[str, Any]: 包含句子和tokens的结构化数据
    """
    print("=== 简单文章处理 ===")
    print(f"原始文本长度: {len(raw_text)} 字符")
    
    # 检查语言类型
    language_code = get_language_code(language) if language else None
    is_non_whitespace = is_non_whitespace_language(language_code) if language_code else False
    language_category = get_language_category(language_code) if language_code else "unknown"
    
    if language:
        print(f"语言: {language} (代码: {language_code}, 类型: {language_category})")
        if is_non_whitespace:
            print("⚠️  检测到非空格语言，将使用字符级别分词")
        else:
            print("✅ 检测到空格语言，使用单词级别分词")
    
    # 步骤1: 分割句子
    print("\n1. 分割句子...")
    sentences = split_sentences(raw_text, language_code=language_code)
    sentences = split_sentences(raw_text, language_code=language_code)
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
        
        # 分割tokens（根据语言类型选择分词方式）
        tokens = split_tokens(sentence_text, is_non_whitespace=is_non_whitespace)
        
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
    
    # 添加语言信息
    result["language"] = language
    result["language_code"] = language_code
    result["language_category"] = language_category
    result["is_non_whitespace"] = is_non_whitespace
    
    print(f"\n✅ 处理完成！")
    print(f"   总句子数: {result['total_sentences']}")
    print(f"   总token数: {result['total_tokens']}")
    
    return result 