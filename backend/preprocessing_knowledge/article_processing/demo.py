#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文章处理模块演示脚本
展示如何使用文章处理功能
"""

from .article_processor import process_article, process_article_simple, save_structured_data
from .utils import save_result, print_result_summary, get_token_statistics, validate_result

def demo_basic_processing():
    """演示基本文章处理功能"""
    print("=== 基本文章处理演示 ===\n")
    
    # 示例文章
    article = """
    The quick brown fox jumps over the lazy dog. This is a classic pangram that contains every letter of the English alphabet at least once. Learning to code in Python is both fun and rewarding! 
    
    Natural language processing is an exciting field. It combines linguistics, computer science, and artificial intelligence. Researchers work on various tasks like text classification, sentiment analysis, and machine translation.
    """
    
    # 使用简单处理
    result = process_article_simple(article)
    
    # 保存结果
    save_result(result, "demo_result.json")
    
    # 打印摘要
    print_result_summary(result)
    
    # 获取统计信息
    stats = get_token_statistics(result)
    print(f"\nToken统计:")
    print(f"  文本tokens: {stats['text_tokens']}")
    print(f"  标点符号tokens: {stats['punctuation_tokens']}")
    print(f"  空白字符tokens: {stats['space_tokens']}")
    
    # 验证结果
    validate_result(result)
    
    return result

def demo_full_processing():
    """演示完整文章处理功能"""
    print("\n=== 完整文章处理演示 ===\n")
    
    # 示例文章
    article = """
    Artificial Intelligence (AI) is transforming the world around us. From virtual assistants to autonomous vehicles, AI technologies are becoming increasingly prevalent in our daily lives. Machine learning, a subset of AI, enables computers to learn and improve from experience without being explicitly programmed.
    
    Deep learning, a more advanced form of machine learning, uses neural networks with multiple layers to process complex patterns in data. This technology has revolutionized fields such as computer vision, natural language processing, and speech recognition. Companies worldwide are investing heavily in AI research and development.
    
    However, the rapid advancement of AI also raises important ethical considerations. Issues such as privacy, bias, job displacement, and autonomous decision-making need careful consideration. It is crucial to develop AI systems that are fair, transparent, and beneficial to society as a whole.
    """
    
    # 使用完整处理
    result = process_article(
        raw_text=article,
        text_id=1,
        text_title="AI Article"
    )
    
    # 保存结构化数据
    save_structured_data(result, "demo_data")
    
    return result

def demo_custom_usage():
    """演示自定义使用方式"""
    print("\n=== 自定义使用演示 ===\n")
    
    # 自定义文章
    custom_article = "Hello, world! This is a test. How are you today?"
    
    # 直接使用各个模块
    from .sentence_processor import split_sentences
    from .token_processor import split_tokens
    
    print("1. 只分割句子:")
    sentences = split_sentences(custom_article)
    for i, sentence in enumerate(sentences, 1):
        print(f"   句子 {i}: {sentence}")
    
    print("\n2. 只分割tokens:")
    for i, sentence in enumerate(sentences, 1):
        tokens = split_tokens(sentence)
        print(f"   句子 {i} 的tokens: {[t['token_body'] for t in tokens]}")

def main():
    """主演示函数"""
    print("文章处理模块演示")
    print("=" * 50)
    
    # 基本处理演示
    result1 = demo_basic_processing()
    
    # 完整处理演示
    result2 = demo_full_processing()
    
    # 自定义使用演示
    demo_custom_usage()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("生成的文件:")
    print("- demo_result.json (简单处理结果)")
    print("- demo_data/text_001/ (完整处理结果)")

if __name__ == "__main__":
    main() 