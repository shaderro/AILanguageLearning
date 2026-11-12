#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.text_processor import TextProcessor

def test_lemma_integration():
    """测试lemma集成功能"""
    
    print("🔍 测试lemma集成功能")
    print("=" * 50)
    
    # 创建文本处理器
    processor = TextProcessor()
    
    # 测试文本
    test_text = "Artificial intelligence has revolutionized the way we interact with technology."
    
    print(f"📝 测试文本: {test_text}")
    print("-" * 30)
    
    # 处理文本
    original_text = processor.process_text_to_structured_data(test_text, 999, "测试文本")
    
    # 分析结果
    print("📊 分析结果:")
    print("-" * 30)
    
    total_tokens = 0
    text_tokens = 0
    lemma_tokens = 0
    null_lemma_tokens = 0
    
    for sentence in original_text.text_by_sentence:
        print(f"\n📄 句子 {sentence.sentence_id}: {sentence.sentence_body}")
        print("   Tokens:")
        
        for token in sentence.tokens:
            total_tokens += 1
            lemma = token.lemma
            
            if token.token_type == "text":
                text_tokens += 1
                if lemma is not None:
                    lemma_tokens += 1
                    lemma_mark = "📝"
                else:
                    null_lemma_tokens += 1
                    lemma_mark = "❌"
            else:
                lemma_mark = "⚪"
                if lemma is None:
                    null_lemma_tokens += 1
                else:
                    print(f"⚠️  警告：非text类型token '{token.token_body}' 有lemma: {lemma}")
            
            print(f"     {lemma_mark} '{token.token_body}' ({token.token_type}) -> Lemma: {lemma}")
    
    print(f"\n📈 统计信息:")
    print("-" * 30)
    print(f"   总token数量: {total_tokens}")
    print(f"   text类型token: {text_tokens}")
    print(f"   有lemma的token: {lemma_tokens}")
    print(f"   无lemma的token: {null_lemma_tokens}")
    
    # 验证规则
    print(f"\n✅ 验证结果:")
    print("-" * 30)
    
    # 验证1: 只有text类型的token有lemma
    text_tokens_with_lemma = lemma_tokens
    if text_tokens_with_lemma == text_tokens:
        print("✅ 所有text类型token都有lemma")
    else:
        print(f"❌ 有 {text_tokens - text_tokens_with_lemma} 个text类型token没有lemma")
    
    # 验证2: 非text类型的token没有lemma
    non_text_tokens = total_tokens - text_tokens
    if null_lemma_tokens >= non_text_tokens:
        print("✅ 所有非text类型token都没有lemma")
    else:
        print(f"❌ 有 {non_text_tokens - null_lemma_tokens} 个非text类型token有lemma")
    
    # 显示一些lemma示例
    print(f"\n📋 Lemma示例:")
    print("-" * 30)
    
    lemma_examples = []
    for sentence in original_text.text_by_sentence:
        for token in sentence.tokens:
            if token.token_type == "text" and token.lemma:
                lemma_examples.append((token.token_body, token.lemma))
                if len(lemma_examples) >= 5:
                    break
        if len(lemma_examples) >= 5:
            break
    
    for i, (token_body, lemma) in enumerate(lemma_examples, 1):
        print(f"   {i}. '{token_body}' -> '{lemma}'")
    
    print(f"\n🎉 测试完成！")

if __name__ == "__main__":
    test_lemma_integration() 