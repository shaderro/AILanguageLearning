#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.agents.single_token_difficulty_estimation import SingleTokenDifficultyEstimator

def test_difficulty_estimation():
    """测试单词难度评估功能"""
    
    # 创建评估器实例
    estimator = SingleTokenDifficultyEstimator()
    
    # 测试单词列表
    test_words = [
        "hello",      # 简单词汇
        "cat",        # 简单词汇
        "beautiful",  # 中等词汇
        "ephemeral",  # 困难词汇
        "serendipity" # 困难词汇
    ]
    
    print("🔍 开始测试单词难度评估...")
    print("=" * 50)
    
    for word in test_words:
        try:
            print(f"📝 评估单词: '{word}'")
            result = estimator.run(word, verbose=True)
            print(f"✅ 结果: {result}")
            print("-" * 30)
        except Exception as e:
            print(f"❌ 评估失败: {e}")
            print("-" * 30)

if __name__ == "__main__":
    test_difficulty_estimation() 