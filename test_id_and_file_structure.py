#!/usr/bin/env python3
"""
测试ID处理和文件结构
验证 process_article 的ID处理以及文件结构是否符合要求
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_language_system import IntegratedLanguageSystem
import json

def test_id_handling():
    """测试ID处理"""
    print("🧪 测试ID处理")
    print("=" * 60)
    
    system = IntegratedLanguageSystem()
    
    # 测试文章1
    article1 = "Learning a new language is challenging but rewarding."
    print("\n📋 测试文章1 (ID: 1)")
    print("-" * 40)
    
    result1 = system.process_article(article1, text_id=1, title="Article 01")
    print(f"✅ 文章1处理完成")
    print(f"   返回的text_id: {result1['statistics']['text_id']}")
    print(f"   句子数量: {result1['statistics']['total_sentences']}")
    
    # 测试文章2
    article2 = "Grammar and vocabulary are essential components of language study."
    print("\n📋 测试文章2 (ID: 2)")
    print("-" * 40)
    
    result2 = system.process_article(article2, text_id=2, title="Article 02")
    print(f"✅ 文章2处理完成")
    print(f"   返回的text_id: {result2['statistics']['text_id']}")
    print(f"   句子数量: {result2['statistics']['total_sentences']}")
    
    # 测试文章3
    article3 = "The internet has revolutionized the way we learn languages."
    print("\n📋 测试文章3 (ID: 3)")
    print("-" * 40)
    
    result3 = system.process_article(article3, text_id=3, title="Article 03")
    print(f"✅ 文章3处理完成")
    print(f"   返回的text_id: {result3['statistics']['text_id']}")
    print(f"   句子数量: {result3['statistics']['total_sentences']}")
    
    # 验证ID是否正确传递
    print("\n📋 ID验证")
    print("-" * 40)
    
    for i, result in enumerate([result1, result2, result3], 1):
        expected_id = i
        actual_id = result['statistics']['text_id']
        if expected_id == actual_id:
            print(f"✅ 文章{i}: ID正确 ({actual_id})")
        else:
            print(f"❌ 文章{i}: ID错误 (期望: {expected_id}, 实际: {actual_id})")
        
        # 检查句子中的text_id
        for sentence in result['sentences']:
            if sentence.text_id == expected_id:
                print(f"   ✅ 句子text_id正确: {sentence.text_id}")
            else:
                print(f"   ❌ 句子text_id错误: {sentence.text_id}")

def test_file_structure():
    """测试文件结构"""
    print("\n🧪 测试文件结构")
    print("=" * 60)
    
    # 检查当前文件结构
    print("📋 当前data目录文件结构:")
    print("-" * 40)
    
    data_dir = "data"
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        
        # 分类文件
        article_files = [f for f in files if "original_text" in f and f.endswith('.json')]
        vocab_files = [f for f in files if "vocab" in f and f.endswith('.json')]
        grammar_files = [f for f in files if "grammar" in f and f.endswith('.json')]
        
        print(f"📄 文章文件: {len(article_files)} 个")
        for f in sorted(article_files):
            print(f"   - {f}")
        
        print(f"\n📚 词汇文件: {len(vocab_files)} 个")
        for f in sorted(vocab_files):
            print(f"   - {f}")
        
        print(f"\n📖 语法文件: {len(grammar_files)} 个")
        for f in sorted(grammar_files):
            print(f"   - {f}")
    
    # 检查期望的文件结构
    print("\n📋 期望的文件结构:")
    print("-" * 40)
    print("📁 article文件夹:")
    print("   - article01.json")
    print("   - article02.json")
    print("   - article03.json")
    print("📄 vocab.json")
    print("📄 grammar.json")
    
    # 检查是否按OriginalText结构存储
    print("\n📋 检查OriginalText数据结构:")
    print("-" * 40)
    
    try:
        # 尝试读取最新的文章文件
        latest_article_file = None
        for f in sorted(article_files, reverse=True):
            if "new_new.json" in f:
                latest_article_file = f
                break
        
        if latest_article_file:
            with open(os.path.join(data_dir, latest_article_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📄 检查文件: {latest_article_file}")
            
            if isinstance(data, list) and len(data) > 0:
                first_article = data[0]
                print(f"✅ 数据结构是列表")
                print(f"   文章数量: {len(data)}")
                
                # 检查是否包含OriginalText的字段
                required_fields = ['text_id', 'text_title', 'text_by_sentence']
                missing_fields = [field for field in required_fields if field not in first_article]
                
                if not missing_fields:
                    print(f"✅ 包含所有OriginalText字段: {required_fields}")
                    print(f"   文章ID: {first_article['text_id']}")
                    print(f"   文章标题: {first_article['text_title']}")
                    print(f"   句子数量: {len(first_article['text_by_sentence'])}")
                    
                    # 检查句子结构
                    if first_article['text_by_sentence']:
                        first_sentence = first_article['text_by_sentence'][0]
                        sentence_fields = ['text_id', 'sentence_id', 'sentence_body', 'sentence_difficulty_level', 'tokens']
                        sentence_missing = [field for field in sentence_fields if field not in first_sentence]
                        
                        if not sentence_missing:
                            print(f"✅ 句子结构完整: {sentence_fields}")
                        else:
                            print(f"❌ 句子缺少字段: {sentence_missing}")
                else:
                    print(f"❌ 缺少OriginalText字段: {missing_fields}")
            else:
                print(f"❌ 数据结构不是预期的列表格式")
        else:
            print("❌ 未找到最新的文章文件")
            
    except Exception as e:
        print(f"❌ 检查文件结构失败: {e}")

def test_article_folder_structure():
    """测试文章文件夹结构"""
    print("\n🧪 测试文章文件夹结构")
    print("=" * 60)
    
    # 检查是否存在article文件夹
    article_dir = "data/article"
    if os.path.exists(article_dir):
        print(f"✅ article文件夹存在: {article_dir}")
        
        files = os.listdir(article_dir)
        article_files = [f for f in files if f.startswith('article') and f.endswith('.json')]
        
        print(f"📄 文章文件数量: {len(article_files)}")
        for f in sorted(article_files):
            print(f"   - {f}")
    else:
        print(f"❌ article文件夹不存在: {article_dir}")
        print("   当前文件结构不符合期望")

def main():
    """主函数"""
    print("🎯 测试ID处理和文件结构")
    print("=" * 60)
    
    # 测试ID处理
    test_id_handling()
    
    # 测试文件结构
    test_file_structure()
    
    # 测试文章文件夹结构
    test_article_folder_structure()
    
    print("\n📋 总结和建议:")
    print("-" * 40)
    print("1. ID处理: 需要验证text_id是否正确传递")
    print("2. 文件结构: 当前不符合期望的article文件夹结构")
    print("3. 数据结构: 需要确认是否按OriginalText结构存储")
    print("4. 建议: 修改保存逻辑以符合期望的文件结构")

if __name__ == "__main__":
    main() 