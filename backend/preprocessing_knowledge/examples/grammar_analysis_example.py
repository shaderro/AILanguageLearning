#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语法分析助手使用示例
展示如何使用GrammarAnalysisAssistant进行语法分析
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def grammar_analysis_example():
    """语法分析示例"""
    
    print("🔍 语法分析助手使用示例")
    print("=" * 50)
    
    try:
        # 导入语法分析助手
        from src.agents.grammar_analysis import GrammarAnalysisAssistant
        
        # 创建语法分析助手实例
        grammar_assistant = GrammarAnalysisAssistant()
        
        # 测试句子列表
        test_cases = [
            {
                "sentence": "Artificial intelligence has revolutionized the way we interact with technology.",
                "context": "This sentence discusses the impact of AI on technology interaction."
            },
            {
                "sentence": "Although the weather was terrible, we still enjoyed our vacation.",
                "context": "This sentence describes a vacation experience despite bad weather."
            },
            {
                "sentence": "The book that I bought yesterday is very interesting.",
                "context": "This sentence talks about a book purchase and its quality."
            }
        ]
        
        print("📚 开始语法分析...")
        print()
        
        for i, case in enumerate(test_cases, 1):
            print(f"📝 测试 {i}: {case['sentence']}")
            print(f"📖 上下文: {case['context']}")
            print("-" * 40)
            
            try:
                # 进行语法分析
                result = grammar_assistant.analyze_grammar(
                    case['sentence'], 
                    case['context']
                )
                
                if result and "explanation" in result and "keywords" in result:
                    print("✅ 语法分析成功！")
                    print(f"📖 语法讲解: {result['explanation']}")
                    print(f"🔑 关键词: {result['keywords']}")
                else:
                    print("❌ 语法分析失败：返回结果格式不正确")
                    print(f"结果: {result}")
                    
            except Exception as e:
                print(f"❌ 语法分析异常: {e}")
            
            print()
        
        print("🎉 语法分析示例完成！")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    grammar_analysis_example()

if __name__ == "__main__":
    main() 