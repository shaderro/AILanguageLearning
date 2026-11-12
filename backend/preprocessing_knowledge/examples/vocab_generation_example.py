#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vocab生成示例
展示如何使用token_to_vocab模块从处理后的文本中生成vocab
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.text_processor import TextProcessor
from src.utils.token_to_vocab import TokenToVocabConverter

def generate_vocab_from_text():
    """从文本生成vocab示例"""
    
    print("🔍 Vocab生成示例")
    print("=" * 50)
    
    # 测试文本
    test_text = """
    Artificial intelligence has revolutionized the way we interact with technology. 
    Machine learning algorithms can process vast amounts of data to identify patterns 
    and make predictions. Deep learning networks, inspired by neural structures, 
    have achieved remarkable breakthroughs in image recognition and natural language processing.
    """
    
    print(f"📝 输入文本:\n{test_text.strip()}")
    print("-" * 30)
    
    try:
        # 1. 使用TextProcessor处理文本
        print("1. 处理文本...")
        processor = TextProcessor()
        original_text = processor.process_text_to_structured_data(test_text, 1, "AI技术文本")
        
        print(f"   ✅ 处理完成！")
        print(f"   📄 句子数量: {len(original_text.text_by_sentence)}")
        
        # 统计hard难度的token
        hard_tokens = []
        for sentence in original_text.text_by_sentence:
            for token in sentence.tokens:
                if token.token_type == "text" and token.difficulty_level == "hard":
                    hard_tokens.append(token.token_body)
        
        print(f"   🔤 Hard难度token: {hard_tokens}")
        print()
        
        # 2. 使用TokenToVocabConverter生成vocab
        print("2. 生成vocab...")
        converter = TokenToVocabConverter("vocab_data.json")
        vocab_expressions = converter.convert_tokens_from_text(original_text)
        
        print(f"   ✅ 生成完成！")
        print(f"   📚 生成vocab数量: {len(vocab_expressions)}")
        
        # 显示生成的vocab
        for vocab in vocab_expressions:
            print(f"   - {vocab.vocab_body}: {vocab.explanation[:100]}...")
        
        print()
        
        # 3. 保存vocab数据
        print("3. 保存vocab数据...")
        converter.save_vocab_data(vocab_expressions)
        
        print()
        print("🎉 Vocab生成完成！")
        print(f"📁 数据已保存到: vocab_data.json")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")

def main():
    """主函数"""
    generate_vocab_from_text()

if __name__ == "__main__":
    main() 