#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.text_processor import TextProcessor

def test_difficulty_integration():
    """测试难度评估集成功能"""
    
    print("🔍 测试难度评估集成功能")
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
    easy_tokens = 0
    hard_tokens = 0
    null_tokens = 0
    
    for sentence in original_text.text_by_sentence:
        print(f"\n📄 句子 {sentence.sentence_id}: {sentence.sentence_body}")
        print("   Tokens:")
        
        for token in sentence.tokens:
            total_tokens += 1
            difficulty = token.difficulty_level
            
            if token.token_type == "text":
                text_tokens += 1
                if difficulty == "easy":
                    easy_tokens += 1
                    difficulty_mark = "🟢"
                elif difficulty == "hard":
                    hard_tokens += 1
                    difficulty_mark = "🔴"
                else:
                    null_tokens += 1
                    difficulty_mark = "⚪"
            else:
                difficulty_mark = "⚪"
                if difficulty is None:
                    null_tokens += 1
                else:
                    print(f"⚠️  警告：非text类型token '{token.token_body}' 有难度级别: {difficulty}")
            
            print(f"     {difficulty_mark} '{token.token_body}' ({token.token_type}) -> {difficulty}")
    
    print(f"\n📈 统计信息:")
    print("-" * 30)
    print(f"   总token数量: {total_tokens}")
    print(f"   text类型token: {text_tokens}")
    print(f"   easy难度: {easy_tokens}")
    print(f"   hard难度: {hard_tokens}")
    print(f"   null难度: {null_tokens}")
    
    # 验证规则
    print(f"\n✅ 验证结果:")
    print("-" * 30)
    
    # 验证1: 只有text类型的token有难度评估
    text_tokens_with_difficulty = easy_tokens + hard_tokens
    if text_tokens_with_difficulty == text_tokens:
        print("✅ 所有text类型token都有难度评估")
    else:
        print(f"❌ 有 {text_tokens - text_tokens_with_difficulty} 个text类型token没有难度评估")
    
    # 验证2: 非text类型的token没有难度评估
    non_text_tokens = total_tokens - text_tokens
    if null_tokens >= non_text_tokens:
        print("✅ 所有非text类型token都没有难度评估")
    else:
        print(f"❌ 有 {non_text_tokens - null_tokens} 个非text类型token有难度评估")
    
    print(f"\n🎉 测试完成！")

if __name__ == "__main__":
    test_difficulty_integration() 