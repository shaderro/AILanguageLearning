#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试token_to_vocab模块
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.token_data import Token, Sentence, OriginalText
from src.utils.token_to_vocab import TokenToVocabConverter, convert_token_to_vocab

def test_token_to_vocab():
    """测试token到vocab转换功能"""
    
    print("🔍 测试token_to_vocab模块")
    print("=" * 50)
    
    # 创建测试数据
    test_tokens = [
        Token(
            token_body="Artificial",
            token_type="text",
            difficulty_level="hard",
            global_token_id=1,
            sentence_token_id=1,
            pos_tag="ADJ",
            lemma="artificial",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="intelligence",
            token_type="text",
            difficulty_level="hard",
            global_token_id=2,
            sentence_token_id=2,
            pos_tag="NOUN",
            lemma="intelligence",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="the",
            token_type="text",
            difficulty_level="easy",
            global_token_id=3,
            sentence_token_id=3,
            pos_tag="DET",
            lemma="the",
            is_grammar_marker=False,
            linked_vocab_id=None
        )
    ]
    
    # 创建测试句子
    test_sentence = Sentence(
        text_id=1,
        sentence_id=1,
        sentence_body="Artificial intelligence has revolutionized technology.",
        grammar_annotations=[],
        vocab_annotations=[],
        tokens=test_tokens
    )
    
    # 创建测试文本
    test_text = OriginalText(
        text_id=1,
        text_title="测试文本",
        text_by_sentence=[test_sentence]
    )
    
    print(f"📝 测试句子: {test_sentence.sentence_body}")
    print(f"🔤 测试tokens: {[token.token_body for token in test_tokens]}")
    print("-" * 30)
    
    try:
        # 测试单个token转换
        print("1. 测试单个token转换:")
        for token in test_tokens:
            if token.difficulty_level == "hard":
                vocab = convert_token_to_vocab(token, test_sentence.sentence_body, 1, 1)
                if vocab:
                    print(f"   ✅ '{token.token_body}' -> vocab_id: {vocab.vocab_id}")
                else:
                    print(f"   ❌ '{token.token_body}' -> 转换失败")
            else:
                print(f"   ⚪ '{token.token_body}' -> 跳过（非hard难度）")
        
        print()
        
        # 测试批量转换
        print("2. 测试批量转换:")
        converter = TokenToVocabConverter("test_vocab_data.json")
        vocab_expressions = converter.convert_tokens_from_text(test_text)
        
        print(f"   找到 {len(vocab_expressions)} 个hard难度的vocab:")
        for vocab in vocab_expressions:
            print(f"   - {vocab.vocab_body}: {vocab.explanation[:50]}...")
        
        # 保存测试数据
        if vocab_expressions:
            converter.save_vocab_data(vocab_expressions)
        
        print()
        print("✅ 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_token_to_vocab() 