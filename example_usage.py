#!/usr/bin/env python3
"""
语言学习系统使用示例
展示如何使用集成系统进行文章处理和问答
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_language_system import IntegratedLanguageSystem

def example_usage():
    """使用示例"""
    print("🎯 语言学习系统使用示例")
    print("=" * 60)
    
    # 1. 创建系统
    print("📋 1. 创建语言学习系统")
    print("-" * 40)
    system = IntegratedLanguageSystem()
    
    # 2. 处理文章
    print("\n📋 2. 处理文章")
    print("-" * 40)
    
    # 示例文章
    article = """
    Artificial Intelligence (AI) has revolutionized many industries in recent years. 
    Machine learning algorithms can process vast amounts of data and identify patterns that humans might miss. 
    Deep learning, a subset of machine learning, uses neural networks to solve complex problems.
    """
    
    print("📖 原始文章:")
    print(article.strip())
    
    # 处理文章
    sentences = system.process_article(article, text_id=1, title="AI Article")
    
    # 3. 显示处理结果
    print("\n📋 3. 处理结果")
    print("-" * 40)
    
    for i, sentence in enumerate(sentences, 1):
        print(f"句子 {i}: {sentence.sentence_body}")
        print(f"难度: {sentence.sentence_difficulty_level}")
        print(f"Token数量: {len(sentence.tokens)}")
        
        # 显示困难词汇
        hard_tokens = [t for t in sentence.tokens if t.difficulty_level == 'hard']
        if hard_tokens:
            print(f"困难词汇: {[t.token_body for t in hard_tokens]}")
        print()
    
    # 4. 用户问答
    print("📋 4. 用户问答")
    print("-" * 40)
    
    # 示例问题
    questions = [
        "Artificial Intelligence是什么意思？",
        "machine learning和deep learning有什么区别？",
        "neural networks是什么？"
    ]
    
    for question in questions:
        print(f"\n❓ 问题: {question}")
        
        # 找到相关的句子
        target_sentence = None
        for sentence in sentences:
            # 简单的关键词匹配
            if any(keyword in sentence.sentence_body.lower() for keyword in question.lower().split()):
                target_sentence = sentence
                break
        
        if target_sentence:
            print(f"📖 引用句子: {target_sentence.sentence_body}")
            answer = system.ask_question(target_sentence, question)
            print(f"🤖 回答: {answer}")
        else:
            print("⚠️ 未找到相关句子")
    
    # 5. 系统状态
    print("\n📋 5. 系统状态")
    print("-" * 40)
    system.print_system_status()
    
    print("\n🎉 使用示例完成！")

def interactive_demo():
    """交互式演示"""
    print("\n🎮 交互式演示")
    print("=" * 60)
    
    system = IntegratedLanguageSystem()
    
    # 处理文章
    article = input("请输入要学习的文章 (或按回车使用默认文章): ").strip()
    if not article:
        article = """
        The Internet of Things (IoT) connects everyday devices to the internet. 
        Smart homes use IoT technology to control lighting, temperature, and security systems. 
        This technology makes our lives more convenient and efficient.
        """
        print("使用默认文章...")
    
    sentences = system.process_article(article, text_id=1, title="Interactive Article")
    
    print(f"\n✅ 文章处理完成，共 {len(sentences)} 个句子")
    
    # 交互式问答
    print("\n💬 开始问答 (输入 'quit' 退出):")
    
    while True:
        question = input("\n❓ 请输入问题: ").strip()
        
        if question.lower() in ['quit', 'exit', '退出']:
            break
        
        if not question:
            continue
        
        # 找到最相关的句子
        target_sentence = None
        best_match_score = 0
        
        for sentence in sentences:
            # 简单的关键词匹配评分
            keywords = question.lower().split()
            sentence_words = sentence.sentence_body.lower().split()
            match_score = sum(1 for keyword in keywords if any(keyword in word for word in sentence_words))
            
            if match_score > best_match_score:
                best_match_score = match_score
                target_sentence = sentence
        
        if target_sentence:
            print(f"📖 引用句子: {target_sentence.sentence_body}")
            answer = system.ask_question(target_sentence, question)
            print(f"🤖 回答: {answer}")
        else:
            print("⚠️ 未找到相关句子，请尝试其他问题")
    
    print("\n👋 演示结束！")

if __name__ == "__main__":
    # 运行使用示例
    example_usage()
    
    # 询问是否运行交互式演示
    choice = input("\n是否运行交互式演示？(y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        interactive_demo() 