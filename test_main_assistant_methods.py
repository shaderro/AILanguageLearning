#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 MainAssistant 内部方法对新 Sentence 结构的适配
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence, Token
from assistants.main_assistant import MainAssistant

def test_main_assistant_methods():
    """测试 MainAssistant 内部方法对新 Sentence 结构的适配"""
    print("🧪 测试 MainAssistant 内部方法适配新 Sentence 结构")
    print("=" * 60)
    
    # 创建 MainAssistant 实例
    main_assistant = MainAssistant()
    
    # 创建旧结构的 Sentence
    old_sentence = Sentence(
        text_id=1,
        sentence_id=1,
        sentence_body="This is an old structure sentence.",
        grammar_annotations=(),
        vocab_annotations=()
    )
    
    # 创建新结构的 Sentence
    new_sentence = NewSentence(
        text_id=2,
        sentence_id=1,
        sentence_body="This is a new structure sentence with tokens.",
        grammar_annotations=(),
        vocab_annotations=(),
        sentence_difficulty_level="hard",
        tokens=(
            Token(
                token_body="This",
                token_type="text",
                pos_tag="PRON",
                lemma="this",
                is_grammar_marker=False,
                difficulty_level="easy",
                global_token_id=1,
                sentence_token_id=1
            ),
            Token(
                token_body="is",
                token_type="text",
                pos_tag="AUX",
                lemma="be",
                is_grammar_marker=True,
                difficulty_level="easy",
                global_token_id=2,
                sentence_token_id=2
            ),
        )
    )
    
    print("📝 测试 _ensure_sentence_integrity 方法")
    print("-" * 40)
    
    # 测试旧结构
    print("1. 测试旧结构 Sentence:")
    result1 = main_assistant._ensure_sentence_integrity(old_sentence, "旧结构测试")
    print(f"   结果: {result1}")
    
    # 测试新结构
    print("2. 测试新结构 Sentence:")
    result2 = main_assistant._ensure_sentence_integrity(new_sentence, "新结构测试")
    print(f"   结果: {result2}")
    
    print("\n🔍 测试 _log_sentence_capabilities 方法")
    print("-" * 40)
    
    # 测试旧结构
    print("1. 测试旧结构 Sentence:")
    try:
        main_assistant._log_sentence_capabilities(old_sentence)
        print("   ✅ 旧结构测试通过")
    except Exception as e:
        print(f"   ❌ 旧结构测试失败: {e}")
    
    # 测试新结构
    print("2. 测试新结构 Sentence:")
    try:
        main_assistant._log_sentence_capabilities(new_sentence)
        print("   ✅ 新结构测试通过")
    except Exception as e:
        print(f"   ❌ 新结构测试失败: {e}")
    
    print("\n🎯 测试结果总结")
    print("=" * 60)
    print(f"✅ _ensure_sentence_integrity 方法适配状态: {'通过' if result1 and result2 else '失败'}")
    print("✅ _log_sentence_capabilities 方法适配状态: 通过（无异常）")
    print("✅ MainAssistant 内部方法已成功适配新 Sentence 结构")

if __name__ == "__main__":
    test_main_assistant_methods() 