#!/usr/bin/env python3
"""
SelectedToken 功能完整使用示例
展示如何使用新的token选择功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated_language_system import IntegratedLanguageSystem
from assistants.chat_info.selected_token import SelectedToken, create_selected_token_from_text
from data_managers.data_classes_new import Sentence as NewSentence, Token

def create_sample_article() -> str:
    """创建示例文章"""
    return """
Learning a new language is challenging but rewarding. It requires dedication and practice, but the benefits are immense. 
When you learn a new language, you open doors to new cultures and opportunities. The process involves understanding grammar rules, 
building vocabulary, and developing listening and speaking skills. Although it may seem overwhelming at first, with consistent effort, 
you will see significant progress over time.
"""

def create_test_sentence() -> NewSentence:
    """创建测试句子"""
    tokens = [
        Token(token_body="Learning", token_type="text", difficulty_level="easy", global_token_id=1, sentence_token_id=1, pos_tag="VERB", lemma="learn", is_grammar_marker=False, linked_vocab_id=None),
        Token(token_body="a", token_type="text", difficulty_level="easy", global_token_id=2, sentence_token_id=2, pos_tag="DET", lemma="a", is_grammar_marker=False, linked_vocab_id=None),
        Token(token_body="new", token_type="text", difficulty_level="easy", global_token_id=3, sentence_token_id=3, pos_tag="ADJ", lemma="new", is_grammar_marker=False, linked_vocab_id=None),
        Token(token_body="language", token_type="text", difficulty_level="easy", global_token_id=4, sentence_token_id=4, pos_tag="NOUN", lemma="language", is_grammar_marker=False, linked_vocab_id=None),
        Token(token_body="is", token_type="text", difficulty_level="easy", global_token_id=5, sentence_token_id=5, pos_tag="AUX", lemma="be", is_grammar_marker=True, linked_vocab_id=None),
        Token(token_body="challenging", token_type="text", difficulty_level="hard", global_token_id=6, sentence_token_id=6, pos_tag="ADJ", lemma="challenging", is_grammar_marker=False, linked_vocab_id=1),
        Token(token_body="but", token_type="text", difficulty_level="easy", global_token_id=7, sentence_token_id=7, pos_tag="CCONJ", lemma="but", is_grammar_marker=False, linked_vocab_id=None),
        Token(token_body="rewarding", token_type="text", difficulty_level="hard", global_token_id=8, sentence_token_id=8, pos_tag="ADJ", lemma="rewarding", is_grammar_marker=False, linked_vocab_id=2)
    ]
    
    return NewSentence(
        text_id=1,
        sentence_id=1,
        sentence_body="Learning a new language is challenging but rewarding.",
        grammar_annotations=(),
        vocab_annotations=(),
        sentence_difficulty_level="medium",
        tokens=tuple(tokens)
    )

def example_full_workflow():
    """完整工作流程示例"""
    print("🚀 SelectedToken 完整工作流程示例")
    print("=" * 80)
    
    # 1. 初始化集成系统
    print("\n📋 步骤1: 初始化集成系统")
    print("-" * 50)
    
    system = IntegratedLanguageSystem()
    print("✅ 集成系统初始化完成")
    
    # 2. 处理文章
    print("\n📋 步骤2: 处理文章")
    print("-" * 50)
    
    article_text = create_sample_article()
    print(f"📖 文章内容: {article_text[:100]}...")
    
    try:
        result = system.process_article(article_text, "Language Learning Article")
        print("✅ 文章处理完成")
        print(f"   处理结果: {result}")
    except Exception as e:
        print(f"❌ 文章处理失败: {e}")
        return
    
    # 3. 获取句子列表
    print("\n📋 步骤3: 获取句子列表")
    print("-" * 50)
    
    sentences = system.get_article_sentences(1)  # 假设文章ID为1
    if not sentences:
        print("⚠️ 没有找到句子，使用测试句子")
        sentences = [create_test_sentence()]
    
    target_sentence = sentences[0]
    print(f"🎯 目标句子: {target_sentence.sentence_body}")
    
    # 4. 测试不同类型的提问
    print("\n📋 步骤4: 测试不同类型的提问")
    print("-" * 50)
    
    # 4.1 整句提问
    print("\n🔍 4.1 整句提问")
    print("-" * 30)
    
    try:
        system.process_and_ask(
            sentence=target_sentence,
            question="这句话的整体意思是什么？"
        )
        print("✅ 整句提问成功")
    except Exception as e:
        print(f"❌ 整句提问失败: {e}")
    
    # 4.2 特定单词提问
    print("\n🔍 4.2 特定单词提问")
    print("-" * 30)
    
    try:
        system.process_and_ask(
            sentence=target_sentence,
            question="challenging是什么意思？",
            selected_text="challenging"
        )
        print("✅ 特定单词提问成功")
    except Exception as e:
        print(f"❌ 特定单词提问失败: {e}")
    
    # 4.3 短语提问
    print("\n🔍 4.3 短语提问")
    print("-" * 30)
    
    try:
        system.process_and_ask(
            sentence=target_sentence,
            question="challenging but rewarding这个短语怎么理解？",
            selected_text="challenging but rewarding"
        )
        print("✅ 短语提问成功")
    except Exception as e:
        print(f"❌ 短语提问失败: {e}")
    
    # 4.4 语法结构提问
    print("\n🔍 4.4 语法结构提问")
    print("-" * 30)
    
    try:
        system.process_and_ask(
            sentence=target_sentence,
            question="这里的but是什么用法？",
            selected_text="but"
        )
        print("✅ 语法结构提问成功")
    except Exception as e:
        print(f"❌ 语法结构提问失败: {e}")
    
    # 5. 查看结果
    print("\n📋 步骤5: 查看处理结果")
    print("-" * 50)
    
    # 获取词汇列表
    vocab_list = system.get_vocab_list()
    print(f"📚 词汇列表: {vocab_list}")
    
    # 获取语法规则
    grammar_rules = system.get_grammar_rules()
    print(f"📖 语法规则: {grammar_rules}")
    
    print("\n🎉 完整工作流程示例完成！")
    print("=" * 80)

def example_selected_token_creation():
    """SelectedToken创建示例"""
    print("\n🔧 SelectedToken 创建示例")
    print("=" * 60)
    
    sentence = create_test_sentence()
    print(f"📖 测试句子: {sentence.sentence_body}")
    
    # 示例1: 整句选择
    print("\n📋 示例1: 整句选择")
    full_token = SelectedToken.from_full_sentence(sentence)
    print(f"   选择的文本: {full_token.token_text}")
    print(f"   token索引: {full_token.token_indices}")
    print(f"   是否整句: {full_token.is_full_sentence()}")
    
    # 示例2: 特定单词选择
    print("\n📋 示例2: 特定单词选择")
    word_token = create_selected_token_from_text(sentence, "challenging")
    print(f"   选择的文本: {word_token.token_text}")
    print(f"   token索引: {word_token.token_indices}")
    print(f"   是否单个token: {word_token.is_single_token()}")
    
    # 示例3: 短语选择
    print("\n📋 示例3: 短语选择")
    phrase_token = create_selected_token_from_text(sentence, "challenging but rewarding")
    print(f"   选择的文本: {phrase_token.token_text}")
    print(f"   token索引: {phrase_token.token_indices}")
    print(f"   token数量: {phrase_token.get_token_count()}")
    
    # 示例4: 转换为字典
    print("\n📋 示例4: 转换为字典")
    dict_data = word_token.to_dict()
    print(f"   字典格式: {dict_data}")
    
    print("\n🎉 SelectedToken 创建示例完成！")
    print("=" * 60)

def interactive_demo():
    """交互式演示"""
    print("\n🎮 交互式演示")
    print("=" * 60)
    
    system = IntegratedLanguageSystem()
    sentence = create_test_sentence()
    
    print(f"📖 示例句子: {sentence.sentence_body}")
    print("请输入你的问题 (输入 'quit' 退出):")
    
    while True:
        question = input("\n❓ 问题: ").strip()
        
        if question.lower() in ['quit', 'exit', '退出']:
            break
        
        if not question:
            continue
        
        # 询问是否选择特定文本
        selected_text = input("🎯 选择的文本 (直接回车表示整句): ").strip()
        if not selected_text:
            selected_text = None
        
        try:
            if selected_text:
                print(f"🎯 分析选择的文本: '{selected_text}'")
            else:
                print("📖 分析整句话")
            
            system.process_and_ask(
                sentence=sentence,
                question=question,
                selected_text=selected_text
            )
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
    
    print("\n👋 再见！")

if __name__ == "__main__":
    # 运行示例
    example_selected_token_creation()
    example_full_workflow()
    
    # 询问是否运行交互式演示
    choice = input("\n是否运行交互式演示？(y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        interactive_demo() 