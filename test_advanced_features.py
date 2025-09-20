#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试高级功能启用脚本
演示如何给text类型token增加enable_advanced_features
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.preprocessing.enhanced_processor import EnhancedArticleProcessor

def test_advanced_features():
    """测试高级功能"""
    print("=== 测试高级功能启用 ===\n")
    
    # 测试文本
    test_text = """
    This is a test article for demonstrating advanced features.
    The word "revolutionized" should be marked as hard difficulty.
    Grammar and vocabulary are essential components of language study.
    """
    
    # 1. 创建基础处理器（不启用高级功能）
    print("1. 基础处理器（无高级功能）:")
    basic_processor = EnhancedArticleProcessor()
    basic_result = basic_processor.process_article_enhanced(
        raw_text=test_text,
        text_id=1,
        text_title="Basic Test"
    )
    
    # 显示基础token信息
    first_sentence_tokens = basic_result['sentences'][0]['tokens']
    print(f"   第一个句子的前3个text类型token:")
    for token in first_sentence_tokens[:6]:  # 显示前6个token（包含空格）
        if token['token_type'] == 'text':
            print(f"   - {token['token_body']}: {list(token.keys())}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. 创建增强处理器（启用高级功能）
    print("2. 增强处理器（启用高级功能）:")
    enhanced_processor = EnhancedArticleProcessor()
    
    # 启用高级功能
    enhanced_processor.enable_advanced_features(
        enable_difficulty=True,
        enable_vocab=True
    )
    
    enhanced_result = enhanced_processor.process_article_enhanced(
        raw_text=test_text,
        text_id=2,
        text_title="Enhanced Test"
    )
    
    # 显示增强token信息
    first_sentence_tokens = enhanced_result['sentences'][0]['tokens']
    print(f"   第一个句子的前3个text类型token:")
    for token in first_sentence_tokens[:6]:  # 显示前6个token（包含空格）
        if token['token_type'] == 'text':
            print(f"   - {token['token_body']}: {list(token.keys())}")
            if 'difficulty_level' in token:
                print(f"     难度: {token['difficulty_level']}")
            if 'lemma' in token:
                print(f"     词根: {token['lemma']}")
            if 'linked_vocab_id' in token and token['linked_vocab_id']:
                print(f"     关联词汇ID: {token['linked_vocab_id']}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. 对比分析
    print("3. 功能对比:")
    print("   基础处理器token字段:", list(basic_result['sentences'][0]['tokens'][0].keys()))
    print("   增强处理器token字段:", list(enhanced_result['sentences'][0]['tokens'][0].keys()))
    
    # 4. 保存结果用于验证
    import json
    with open('test_basic_result.json', 'w', encoding='utf-8') as f:
        json.dump(basic_result, f, ensure_ascii=False, indent=2)
    
    with open('test_enhanced_result.json', 'w', encoding='utf-8') as f:
        json.dump(enhanced_result, f, ensure_ascii=False, indent=2)
    
    print("\n 测试完成！结果已保存到:")
    print("   - test_basic_result.json")
    print("   - test_enhanced_result.json")

if __name__ == "__main__":
    test_advanced_features()
