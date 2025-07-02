#!/usr/bin/env python3
"""
测试新的JSON数据格式
"""

from data_managers.data_controller import DataController
from assistants.main_assistant import MainAssistant
from data_managers.data_classes import Sentence
import json

def test_new_format():
    print("🧪 开始测试新的JSON数据格式...")
    
    # 创建数据控制器和主助手
    data_controller = DataController(3)
    main_assistant = MainAssistant(data_controller, 3)
    
    # 加载现有数据
    data_controller.load_data(
        "data/grammar_rules.json",
        "data/vocab_expressions.json", 
        "data/original_texts.json",
        "data/dialogue_record.json",
        "data/dialogue_history.json"
    )
    
    # 确保测试所需的文本和句子存在
    print("📝 准备测试数据...")
    
    # 强制创建测试文本（覆盖现有数据）
    data_controller.text_manager.original_texts = {}  # 清空现有数据
    
    # 创建第一个文本
    data_controller.text_manager.add_text("First Test Text")
    data_controller.text_manager.add_sentence_to_text(1, "This is the first test sentence.")
    
    # 创建第二个文本
    data_controller.text_manager.add_text("Second Test Text")
    data_controller.text_manager.add_sentence_to_text(2, "This is the second test sentence.")
    
    # 验证创建成功
    text1 = data_controller.text_manager.get_text_by_id(1)
    text2 = data_controller.text_manager.get_text_by_id(2)
    print(f"✅ 文本1创建成功: {text1.text_title if text1 else '失败'}")
    print(f"✅ 文本2创建成功: {text2.text_title if text2 else '失败'}")
    
    # 创建测试句子对象
    test_sentence1 = Sentence(
        text_id=1,
        sentence_id=1,
        sentence_body="This is the first test sentence.",
        grammar_annotations=[],
        vocab_annotations=[]
    )
    
    test_sentence2 = Sentence(
        text_id=2,
        sentence_id=1,
        sentence_body="This is the second test sentence.",
        grammar_annotations=[],
        vocab_annotations=[]
    )
    
    # 模拟用户对话
    print("\n🗨️ 模拟用户对话...")
    
    # 第一个文章的对话
    print("📚 第一个文章 (text_id=1):")
    main_assistant.run(test_sentence1, "What does this sentence mean?")
    main_assistant.run(test_sentence1, "Can you explain the grammar?")
    
    # 第二个文章的对话
    print("\n📚 第二个文章 (text_id=2):")
    main_assistant.run(test_sentence2, "What vocabulary should I learn?")
    main_assistant.run(test_sentence2, "How do you pronounce this?")
    
    # 保存数据
    print("\n💾 保存数据...")
    data_controller.save_data(
        "data/grammar_rules.json",
        "data/vocab_expressions.json",
        "data/original_texts.json", 
        "data/dialogue_record.json",
        "data/dialogue_history.json"
    )
    
    # 检查保存的文件
    print("\n📄 检查新的对话记录格式:")
    try:
        with open("data/dialogue_record.json", "r", encoding="utf-8") as f:
            dialogue_record_data = json.load(f)
        
        print("对话记录结构:")
        print(json.dumps(dialogue_record_data, ensure_ascii=False, indent=2))
        
        # 检查按text_id组织的数据
        if "texts" in dialogue_record_data:
            for text_id, text_data in dialogue_record_data["texts"].items():
                print(f"\n📖 文章 {text_id}: {text_data.get('text_title', 'Unknown')}")
                for sentence_id, dialogues in text_data.get("sentences", {}).items():
                    print(f"  📝 句子 {sentence_id}: {len(dialogues)} 条对话")
                    for dialogue in dialogues:
                        print(f"    👤 {dialogue['user_question'][:30]}...")
        
    except Exception as e:
        print(f"❌ 读取对话记录文件失败: {e}")
    
    print("\n📄 检查新的对话历史格式:")
    try:
        with open("data/dialogue_history.json", "r", encoding="utf-8") as f:
            dialogue_history_data = json.load(f)
        
        print("对话历史结构:")
        print(json.dumps(dialogue_history_data, ensure_ascii=False, indent=2))
        
        # 检查按text_id组织的数据
        if "texts" in dialogue_history_data:
            for text_id, text_data in dialogue_history_data["texts"].items():
                print(f"\n📖 文章 {text_id}: {text_data.get('text_title', 'Unknown')}")
                print(f"  📊 消息数量: {len(text_data.get('messages', []))}")
                print(f"  📝 摘要: {text_data.get('current_summary', '')[:50]}...")
        
    except Exception as e:
        print(f"❌ 读取对话历史文件失败: {e}")
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    test_new_format() 