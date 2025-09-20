#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文章预处理器测试脚本
用于测试 article_processor.py 的功能
处理 hp1.txt 文件并输出结果到 result 文件夹
"""

import sys
import os
import json
from datetime import datetime

# 添加后端路径到系统路径
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.append(backend_path)

# 导入文章处理器
from preprocessing.article_processor import process_article

def test_article_processor():
    """测试文章处理器功能"""
    
    print(" 开始测试文章预处理器...")
    print(f" 当前工作目录: {os.getcwd()}")
    print(f" 后端路径: {backend_path}")
    
    # 文件路径
    input_file = "raw_txt/hp1.txt"
    output_dir = "result"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f" 错误: 输入文件不存在: {input_file}")
        return False
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 读取输入文件
        print(f"\n 读取文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        print(f" 文件信息:")
        print(f"   - 文件大小: {len(raw_text)} 字符")
        print(f"   - 行数: {len(raw_text.splitlines())} 行")
        
        # 处理文章
        print(f"\n 开始处理文章...")
        result = process_article(
            raw_text=raw_text,
            text_id=1,
            text_title="Harry Potter und der Stein der Weisen - Kapitel 1"
        )
        
        # 输出处理结果摘要
        print(f"\n 处理结果摘要:")
        print(f"   - 文章ID: {result['text_id']}")
        print(f"   - 文章标题: {result['text_title']}")
        print(f"   - 总句子数: {result['total_sentences']}")
        print(f"   - 总token数: {result['total_tokens']}")
        
        # 显示前3个句子的预览
        print(f"\n 前3个句子预览:")
        for i, sentence in enumerate(result['sentences'][:3], 1):
            print(f"   句子 {i}: {sentence['sentence_body'][:80]}...")
            print(f"   Token数: {sentence['token_count']}")
        
        # 保存结果到JSON文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"hp1_processed_{timestamp}.json")
        
        print(f"\n 保存结果到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 保存简化版本（只包含基本信息）
        summary_file = os.path.join(output_dir, f"hp1_summary_{timestamp}.json")
        summary = {
            "text_id": result['text_id'],
            "text_title": result['text_title'],
            "total_sentences": result['total_sentences'],
            "total_tokens": result['total_tokens'],
            "processing_timestamp": timestamp,
            "first_sentence": result['sentences'][0]['sentence_body'] if result['sentences'] else "",
            "last_sentence": result['sentences'][-1]['sentence_body'] if result['sentences'] else ""
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f" 测试完成!")
        print(f"   - 完整结果: {output_file}")
        print(f"   - 摘要结果: {summary_file}")
        
        return True
        
    except Exception as e:
        print(f" 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print(" 文章预处理器测试脚本")
    print("=" * 60)
    
    success = test_article_processor()
    
    print("\n" + "=" * 60)
    if success:
        print(" 测试成功完成!")
    else:
        print(" 测试失败!")
    print("=" * 60)

if __name__ == "__main__":
    main()
