#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文本处理工具集主入口
"""

import sys
import os
from src.core.text_processor import TextProcessor

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python main.py <输入文件> [文本ID] [输出目录]")
        print("示例: python main.py examples/test_article_5sentences.txt 1")
        return
    
    input_file = sys.argv[1]
    text_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_file):
        print(f"错误: 文件 '{input_file}' 不存在")
        return
    
    try:
        processor = TextProcessor()
        success = processor.process_file(input_file, text_id, output_dir)
        
        if success:
            print(f"✅ 文件处理成功！文本ID: {text_id}")
        else:
            print("❌ 文件处理失败")
            
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")

if __name__ == "__main__":
    main() 