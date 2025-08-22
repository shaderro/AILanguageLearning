#!/usr/bin/env python3
"""
测试 SelectedToken 功能
验证用户选择特定token进行提问的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from assistants.chat_info.selected_token import SelectedToken, create_selected_token_from_text
from data_managers.data_classes_new import Sentence as NewSentence, Token
from assistants.main_assistant import MainAssistant
from data_managers.data_controller import DataController

def create_test_sentence() -> NewSentence:
    """创建测试句子"""
    tokens = [
        Token(
            token_body="Learning",
            token_type="text",
            difficulty_level="easy",
            global_token_id=1,
            sentence_token_id=1,
            pos_tag="VERB",
            lemma="learn",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="a",
            token_type="text",
            difficulty_level="easy",
            global_token_id=2,
            sentence_token_id=2,
            pos_tag="DET",
            lemma="a",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="new",
            token_type="text",
            difficulty_level="easy",
            global_token_id=3,
            sentence_token_id=3,
            pos_tag="ADJ",
            lemma="new",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="language",
            token_type="text",
            difficulty_level="easy",
            global_token_id=4,
            sentence_token_id=4,
            pos_tag="NOUN",
            lemma="language",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="is",
            token_type="text",
            difficulty_level="easy",
            global_token_id=5,
            sentence_token_id=5,
            pos_tag="AUX",
            lemma="be",
            is_grammar_marker=True,
            linked_vocab_id=None
        ),
        Token(
            token_body="challenging",
            token_type="text",
            difficulty_level="hard",
            global_token_id=6,
            sentence_token_id=6,
            pos_tag="ADJ",
            lemma="challenging",
            is_grammar_marker=False,
            linked_vocab_id=1
        ),
        Token(
            token_body="but",
            token_type="text",
            difficulty_level="easy",
            global_token_id=7,
            sentence_token_id=7,
            pos_tag="CCONJ",
            lemma="but",
            is_grammar_marker=False,
            linked_vocab_id=None
        ),
        Token(
            token_body="rewarding",
            token_type="text",
            difficulty_level="hard",
            global_token_id=8,
            sentence_token_id=8,
            pos_tag="ADJ",
            lemma="rewarding",
            is_grammar_marker=False,
            linked_vocab_id=2
        )
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

def test_selected_token_creation():
    """测试SelectedToken创建"""
    print("🧪 测试 SelectedToken 创建")
    print("=" * 60)
    
    # 创建测试句子
    sentence = create_test_sentence()
    print(f"📖 测试句子: {sentence.sentence_body}")
    
    # 测试1: 整句选择
    print("\n📋 测试1: 整句选择")
    print("-" * 40)
    
    full_sentence_token = SelectedToken.from_full_sentence(sentence)
    print(f"✅ 整句选择创建成功")
    print(f"   token_indices: {full_sentence_token.token_indices}")
    print(f"   token_text: {full_sentence_token.token_text}")
    print(f"   is_full_sentence: {full_sentence_token.is_full_sentence()}")
    print(f"   is_single_token: {full_sentence_token.is_single_token()}")
    
    # 测试2: 特定token选择
    print("\n📋 测试2: 特定token选择")
    print("-" * 40)
    
    specific_token = SelectedToken.from_sentence_and_indices(
        sentence, 
        token_indices=[5, 6],  # "is challenging"
        token_text="is challenging"
    )
    print(f"✅ 特定token选择创建成功")
    print(f"   token_indices: {specific_token.token_indices}")
    print(f"   token_text: {specific_token.token_text}")
    print(f"   is_full_sentence: {specific_token.is_full_sentence()}")
    print(f"   is_single_token: {specific_token.is_single_token()}")
    
    # 测试3: 从文本创建
    print("\n📋 测试3: 从文本创建")
    print("-" * 40)
    
    # 测试选择"challenging"
    challenging_token = create_selected_token_from_text(sentence, "challenging")
    print(f"✅ 从文本'challenging'创建成功")
    print(f"   token_indices: {challenging_token.token_indices}")
    print(f"   token_text: {challenging_token.token_text}")
    
    # 测试选择"challenging but rewarding"
    phrase_token = create_selected_token_from_text(sentence, "challenging but rewarding")
    print(f"✅ 从文本'challenging but rewarding'创建成功")
    print(f"   token_indices: {phrase_token.token_indices}")
    print(f"   token_text: {phrase_token.token_text}")
    
    # 测试4: 转换为字典
    print("\n📋 测试4: 转换为字典")
    print("-" * 40)
    
    dict_data = challenging_token.to_dict()
    print(f"✅ 转换为字典成功")
    print(f"   字典内容: {dict_data}")
    
    print("\n🎉 SelectedToken 创建测试完成！")
    print("=" * 60)

def test_main_assistant_integration():
    """测试与MainAssistant的集成"""
    print("\n🧪 测试与 MainAssistant 的集成")
    print("=" * 60)
    
    # 创建数据控制器和主助手
    data_controller = DataController(max_turns=10, use_new_structure=True, save_to_new_data_class=True)
    main_assistant = MainAssistant(data_controller, max_turns=10)
    
    # 创建测试句子
    sentence = create_test_sentence()
    
    # 测试1: 整句提问
    print("\n📋 测试1: 整句提问")
    print("-" * 40)
    
    try:
        main_assistant.run(
            quoted_sentence=sentence,
            user_question="这句话是什么意思？"
        )
        print("✅ 整句提问测试成功")
    except Exception as e:
        print(f"❌ 整句提问测试失败: {e}")
    
    # 测试2: 特定token提问
    print("\n📋 测试2: 特定token提问")
    print("-" * 40)
    
    try:
        main_assistant.run(
            quoted_sentence=sentence,
            user_question="challenging是什么意思？",
            selected_text="challenging"
        )
        print("✅ 特定token提问测试成功")
    except Exception as e:
        print(f"❌ 特定token提问测试失败: {e}")
    
    # 测试3: 短语提问
    print("\n📋 测试3: 短语提问")
    print("-" * 40)
    
    try:
        main_assistant.run(
            quoted_sentence=sentence,
            user_question="challenging but rewarding这个短语怎么理解？",
            selected_text="challenging but rewarding"
        )
        print("✅ 短语提问测试成功")
    except Exception as e:
        print(f"❌ 短语提问测试失败: {e}")
    
    # 检查会话状态
    print("\n📋 检查会话状态")
    print("-" * 40)
    
    session_state = main_assistant.session_state
    if session_state.current_selected_token:
        print(f"✅ 会话状态包含selected_token")
        print(f"   选择的文本: {session_state.current_selected_token.token_text}")
        print(f"   token索引: {session_state.current_selected_token.token_indices}")
        print(f"   是否整句: {session_state.current_selected_token.is_full_sentence()}")
    else:
        print("⚠️ 会话状态中没有selected_token")
    
    print("\n🎉 MainAssistant 集成测试完成！")
    print("=" * 60)

def test_dialogue_history():
    """测试对话历史记录"""
    print("\n🧪 测试对话历史记录")
    print("=" * 60)
    
    from assistants.chat_info.dialogue_history import DialogueHistory
    
    # 创建对话历史
    dialogue_history = DialogueHistory(max_turns=10)
    
    # 创建测试句子和selected_token
    sentence = create_test_sentence()
    selected_token = create_selected_token_from_text(sentence, "challenging")
    
    # 添加消息
    dialogue_history.add_message(
        user_input="challenging是什么意思？",
        ai_response="challenging的意思是'有挑战性的'，指需要付出努力才能完成的事情。",
        quoted_sentence=sentence,
        selected_token=selected_token
    )
    
    print("✅ 对话历史记录添加成功")
    print(f"   消息数量: {len(dialogue_history.messages_history)}")
    
    # 检查最后一条消息
    if dialogue_history.messages_history:
        last_message = dialogue_history.messages_history[-1]
        print(f"   最后一条消息包含selected_token: {'selected_token' in last_message}")
        if 'selected_token' in last_message:
            print(f"   selected_token内容: {last_message['selected_token']}")
    
    print("\n🎉 对话历史记录测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    # 运行所有测试
    test_selected_token_creation()
    test_main_assistant_integration()
    test_dialogue_history()
    
    print("\n🎉 所有测试完成！")
    print("=" * 60) 