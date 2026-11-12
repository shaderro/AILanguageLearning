#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整的文章处理脚本
整合句子分割和token分割功能，处理整个文章并输出结构化数据
"""

import json
import os
from typing import List, Dict, Any
from src.core.sentence_splitter import split_sentences
from src.core.token_splitter import split_tokens
from src.core.token_data import OriginalText, Sentence, Token

def process_article(raw_text: str, text_id: int = 1, text_title: str = "Article") -> OriginalText:
    """
    处理整个文章，将raw string转换为结构化数据
    
    Args:
        raw_text: 原始文章文本
        text_id: 文章ID
        text_title: 文章标题
        
    Returns:
        OriginalText: 结构化的文章数据
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
        
        # 创建Token对象列表
        tokens = []
        for token_id, token_dict in enumerate(token_dicts, 1):
            token = Token(
                token_body=token_dict["token_body"],
                token_type=token_dict["token_type"],
                global_token_id=global_token_id,
                sentence_token_id=token_id
            )
            tokens.append(token)
            global_token_id += 1
        
        # 创建Sentence对象
        sentence = Sentence(
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_body=sentence_text,
            grammar_annotations=[],
            vocab_annotations=[],
            tokens=tokens
        )
        sentences.append(sentence)
    
    # 步骤3: 创建OriginalText对象
    print("\n步骤3: 创建结构化数据对象...")
    original_text = OriginalText(
        text_id=text_id,
        text_title=text_title,
        text_by_sentence=sentences
    )
    
    print(f"✅ 文章处理完成！")
    print(f"   总句子数: {len(sentences)}")
    print(f"   总token数: {global_token_id}")
    
    return original_text

def save_structured_data(original_text: OriginalText, output_dir: str = "data"):
    """
    保存结构化数据到JSON文件
    
    Args:
        original_text: 结构化的文本数据
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建子目录
    text_dir = os.path.join(output_dir, f"text_{original_text.text_id:03d}")
    os.makedirs(text_dir, exist_ok=True)
    
    # 保存original_text.json
    original_text_data = {
        "text_id": original_text.text_id,
        "text_title": original_text.text_title,
        "text_by_sentence": [
            {
                "text_id": sentence.text_id,
                "sentence_id": sentence.sentence_id,
                "sentence_body": sentence.sentence_body,
                "grammar_annotations": sentence.grammar_annotations,
                "vocab_annotations": sentence.vocab_annotations,
                "tokens": [
                    {
                        "token_body": token.token_body,
                        "token_type": token.token_type,
                        "difficulty_level": token.difficulty_level,
                        "global_token_id": token.global_token_id,
                        "sentence_token_id": token.sentence_token_id,
                        "linked_vocab_id": token.linked_vocab_id,
                        "pos_tag": token.pos_tag,
                        "lemma": token.lemma,
                        "is_grammar_marker": token.is_grammar_marker
                    }
                    for token in sentence.tokens
                ]
            }
            for sentence in original_text.text_by_sentence
        ]
    }
    
    with open(os.path.join(text_dir, "original_text.json"), 'w', encoding='utf-8') as f:
        json.dump(original_text_data, f, ensure_ascii=False, indent=2)
    
    # 保存sentences.json
    sentences_data = [
        {
            "text_id": sentence.text_id,
            "sentence_id": sentence.sentence_id,
            "sentence_body": sentence.sentence_body,
            "grammar_annotations": sentence.grammar_annotations,
            "vocab_annotations": sentence.vocab_annotations,
            "tokens": [
                {
                    "token_body": token.token_body,
                    "token_type": token.token_type,
                    "difficulty_level": token.difficulty_level,
                    "global_token_id": token.global_token_id,
                    "sentence_token_id": token.sentence_token_id,
                    "linked_vocab_id": token.linked_vocab_id,
                    "pos_tag": token.pos_tag,
                    "lemma": token.lemma,
                    "is_grammar_marker": token.is_grammar_marker
                }
                for token in sentence.tokens
            ]
        }
        for sentence in original_text.text_by_sentence
    ]
    
    with open(os.path.join(text_dir, "sentences.json"), 'w', encoding='utf-8') as f:
        json.dump(sentences_data, f, ensure_ascii=False, indent=2)
    
    # 保存tokens.json (所有tokens的扁平化列表)
    all_tokens = []
    for sentence in original_text.text_by_sentence:
        for token in sentence.tokens:
            all_tokens.append({
                "token_body": token.token_body,
                "token_type": token.token_type,
                "difficulty_level": token.difficulty_level,
                "global_token_id": token.global_token_id,
                "sentence_token_id": token.sentence_token_id,
                "sentence_id": sentence.sentence_id,
                "text_id": sentence.text_id,
                "linked_vocab_id": token.linked_vocab_id,
                "pos_tag": token.pos_tag,
                "lemma": token.lemma,
                "is_grammar_marker": token.is_grammar_marker
            })
    
    with open(os.path.join(text_dir, "tokens.json"), 'w', encoding='utf-8') as f:
        json.dump(all_tokens, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存到目录: {text_dir}")
    print(f"   生成文件:")
    print(f"   - original_text.json")
    print(f"   - sentences.json") 
    print(f"   - tokens.json")

def main():
    """主函数：演示文章处理功能"""
    print("=== 文章处理工具 ===\n")
    
    # 示例文章
    sample_article = """
    The quick brown fox jumps over the lazy dog. This is a classic pangram that contains every letter of the English alphabet at least once. Learning to code in Python is both fun and rewarding! 
    
    Natural language processing is an exciting field. It combines linguistics, computer science, and artificial intelligence. Researchers work on various tasks like text classification, sentiment analysis, and machine translation.
    """
    
    # 处理文章
    original_text = process_article(
        raw_text=sample_article,
        text_id=1,
        text_title="Sample Article"
    )
    
    # 保存数据
    save_structured_data(original_text, "data")
    
    print("\n=== 处理完成 ===")

if __name__ == "__main__":
    main() 