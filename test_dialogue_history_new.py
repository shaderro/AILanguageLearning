#!/usr/bin/env python3

from assistants.chat_info.dialogue_history import DialogueHistory
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence, Token

def test_dialogue_history_new():
    print("🧪 开始测试新DialogueHistory功能...")
    
    # 创建DialogueHistory实例
    dialogue_history = DialogueHistory(max_turns=5)
    
    # 创建测试句子
    test_sentence_str = "Die Finne ist groß und stark gebogen, sie besitzt dabei zugleich eine sehr breite Basis."
    
    # 创建旧数据结构的测试句子
    test_sentence = Sentence(
        text_id=1,
        sentence_id=1,
        sentence_body=test_sentence_str,
        grammar_annotations=(),
        vocab_annotations=()
    )
    
    # 创建新数据结构的测试句子
    test_new_sentence = NewSentence(
        text_id=2,
        sentence_id=1,
        sentence_body=test_sentence_str,
        grammar_annotations=(),
        vocab_annotations=(),
        sentence_difficulty_level="hard",
        tokens=(
            Token(
                token_body="Die",
                token_type="text",
                difficulty_level="hard",
                global_token_id=1,
                sentence_token_id=1,
                pos_tag="DET",
                lemma="der",
                is_grammar_marker=True,
                linked_vocab_id=None
            ),
            Token(
                token_body="Finne",
                token_type="text",
                difficulty_level="hard",
                global_token_id=2,
                sentence_token_id=2,
                pos_tag="NOUN",
                lemma="Finne",
                is_grammar_marker=False,
                linked_vocab_id=None
            ),
            Token(
                token_body="ist",
                token_type="text",
                difficulty_level="easy",
                global_token_id=3,
                sentence_token_id=3,
                pos_tag="VERB",
                lemma="sein",
                is_grammar_marker=True,
                linked_vocab_id=None
            ),
            Token(
                token_body="groß",
                token_type="text",
                difficulty_level="easy",
                global_token_id=4,
                sentence_token_id=4,
                pos_tag="ADJ",
                lemma="groß",
                is_grammar_marker=False,
                linked_vocab_id=None
            ),
            Token(
                token_body="und",
                token_type="text",
                difficulty_level="easy",
                global_token_id=5,
                sentence_token_id=5,
                pos_tag="CONJ",
                lemma="und",
                is_grammar_marker=True,
                linked_vocab_id=None
            )
        )
    )
    
    # 测试旧数据结构
    print("\n🧪 测试旧数据结构:")
    dialogue_history.add_message("这句话是什么意思？", "这句话描述了鱼鳍的特征。", test_sentence)
    dialogue_history.add_message("Finne是什么？", "Finne是德语名词，指鱼类的背鳍。", test_sentence)
    
    print(f"✅ 消息数量: {len(dialogue_history.messages_history)}")
    print(f"✅ 当前总结: {dialogue_history.summary}")
    
    # 测试新数据结构
    print("\n🧪 测试新数据结构:")
    dialogue_history.add_message("Finne是什么意思？", "Finne是德语名词，指鱼类的背鳍。", test_new_sentence)
    dialogue_history.add_message("这句话的语法结构是什么？", "这是一个复合句，包含两个主句，用逗号连接。", test_new_sentence)
    dialogue_history.add_message("Die和ist的语法功能是什么？", "Die是定冠词，ist是系动词sein的第三人称单数现在时形式。", test_new_sentence)
    
    print(f"✅ 消息数量: {len(dialogue_history.messages_history)}")
    
    # 测试分析功能
    print("\n📊 对话分析:")
    analytics = dialogue_history.get_dialogue_analytics()
    for key, value in analytics.items():
        if isinstance(value, dict):
            print(f"   - {key}:")
            for sub_key, sub_value in value.items():
                print(f"     * {sub_key}: {sub_value}")
        else:
            print(f"   - {key}: {value}")
    
    # 测试消息分类功能
    print("\n🔍 消息分类:")
    new_messages = dialogue_history.get_new_structure_messages()
    old_messages = dialogue_history.get_old_structure_messages()
    print(f"✅ 新数据结构消息数量: {len(new_messages)}")
    print(f"✅ 旧数据结构消息数量: {len(old_messages)}")
    
    # 测试难度级别过滤
    hard_messages = dialogue_history.get_messages_by_difficulty("hard")
    print(f"✅ 困难级别消息数量: {len(hard_messages)}")
    
    # 测试困难词汇总结
    print("\n📚 困难词汇总结:")
    hard_tokens_summary = dialogue_history.get_hard_tokens_summary()
    for token, info in hard_tokens_summary.items():
        print(f"   - {token}: 出现{info['count']}次")
        for context in info['contexts'][:2]:  # 只显示前2个上下文
            print(f"     * 句子: {context['sentence'][:50]}...")
            print(f"     * 问题: {context['user_question']}")
    
    # 测试数据保存和加载
    print("\n💾 测试数据保存和加载:")
    try:
        # 保存数据
        dialogue_history.save_to_file("test_dialogue_history_new.json")
        print("✅ 数据保存成功")
        
        # 创建新的实例来测试加载
        new_dialogue_history = DialogueHistory(max_turns=5)
        new_dialogue_history.load_from_file("test_dialogue_history_new.json")
        print("✅ 数据加载成功")
        
        # 验证加载的数据
        print(f"✅ 加载的消息数量: {len(new_dialogue_history.messages_history)}")
        print(f"✅ 加载的总结: {new_dialogue_history.summary}")
        
        # 验证数据结构类型
        loaded_analytics = new_dialogue_history.get_dialogue_analytics()
        print(f"✅ 加载的数据类型分布: {loaded_analytics['data_types']}")
        
    except Exception as e:
        print(f"❌ 数据保存/加载失败: {e}")
    
    print("\n✅ 新DialogueHistory功能测试完成！")

if __name__ == "__main__":
    test_dialogue_history_new() 