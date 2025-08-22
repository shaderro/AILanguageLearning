#!/usr/bin/env python3
"""
GrammarAnalysis 使用示例
展示如何使用语法分析助手
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from assistants.sub_assistants.grammar_analysis import GrammarAnalysis
import json

def example_usage():
    """使用示例"""
    print("📚 GrammarAnalysis 使用示例")
    print("=" * 60)
    
    # 创建语法分析助手
    analyzer = GrammarAnalysis()
    
    # 示例1: 简单句分析
    print("\n📋 示例1: 简单句分析")
    print("-" * 40)
    
    sentence1 = "Learning a new language is challenging but rewarding."
    context1 = "This sentence is about language learning."
    
    result1 = analyzer.analyze_sentence(sentence1, context1)
    
    print(f"句子: {sentence1}")
    print(f"上下文: {context1}")
    print(f"语法解释: {result1['explanation']}")
    print(f"关键词: {result1['keywords']}")
    
    # 示例2: 复合句分析
    print("\n📋 示例2: 复合句分析")
    print("-" * 40)
    
    sentence2 = "The book that I bought yesterday is very interesting."
    context2 = "Talking about a book purchase."
    
    result2 = analyzer.analyze_sentence(sentence2, context2)
    
    print(f"句子: {sentence2}")
    print(f"上下文: {context2}")
    print(f"语法解释: {result2['explanation']}")
    print(f"关键词: {result2['keywords']}")
    
    # 示例3: 条件句分析
    print("\n📋 示例3: 条件句分析")
    print("-" * 40)
    
    sentence3 = "If you study hard, you will succeed."
    
    result3 = analyzer.analyze_sentence(sentence3)  # 无上下文
    
    print(f"句子: {sentence3}")
    print(f"语法解释: {result3['explanation']}")
    print(f"关键词: {result3['keywords']}")
    
    # 示例4: 复杂句分析
    print("\n📋 示例4: 复杂句分析")
    print("-" * 40)
    
    sentence4 = "Although it was raining, we decided to go for a walk."
    context4 = "Making a decision despite bad weather."
    
    result4 = analyzer.analyze_sentence(sentence4, context4)
    
    print(f"句子: {sentence4}")
    print(f"上下文: {context4}")
    print(f"语法解释: {result4['explanation']}")
    print(f"关键词: {result4['keywords']}")
    
    # 示例5: 批量分析
    print("\n📋 示例5: 批量分析")
    print("-" * 40)
    
    sentences = [
        "She told me that she would come to the party.",
        "The professor who teaches English is very knowledgeable.",
        "When I arrived at the station, the train had already left."
    ]
    
    for i, sentence in enumerate(sentences, 1):
        print(f"\n句子 {i}: {sentence}")
        result = analyzer.analyze_sentence(sentence)
        print(f"关键词: {result['keywords']}")
        print(f"解释: {result['explanation'][:100]}...")
    
    print("\n🎉 示例完成！")
    print("=" * 60)

def interactive_analysis():
    """交互式分析"""
    print("\n🎮 交互式语法分析")
    print("=" * 60)
    
    analyzer = GrammarAnalysis()
    
    print("请输入要分析的句子 (输入 'quit' 退出):")
    
    while True:
        sentence = input("\n句子: ").strip()
        
        if sentence.lower() in ['quit', 'exit', '退出']:
            break
        
        if not sentence:
            continue
        
        context = input("上下文 (可选): ").strip()
        if not context:
            context = None
        
        try:
            result = analyzer.analyze_sentence(sentence, context)
            
            print(f"\n📖 分析结果:")
            print(f"语法解释: {result['explanation']}")
            print(f"关键词: {result['keywords']}")
            
            # 显示JSON格式
            print(f"\n📄 JSON格式:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
    
    print("\n👋 再见！")

if __name__ == "__main__":
    # 运行使用示例
    example_usage()
    
    # 询问是否运行交互式分析
    choice = input("\n是否运行交互式分析？(y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        interactive_analysis() 