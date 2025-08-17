#!/usr/bin/env python3

from data_managers.data_controller import DataController
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence, Token

def test_new_dialogue_record():
    print("🧪 开始测试新对话记录功能...")
    
    # 创建数据控制器，启用新结构模式
    data_controller = DataController(3, use_new_structure=True, save_to_new_data_class=True)
    
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
    
    print("🔍 旧数据结构句子信息:")
    print(f"   - text_id: {test_sentence.text_id}")
    print(f"   - sentence_id: {test_sentence.sentence_id}")
    print(f"   - grammar_annotations: {test_sentence.grammar_annotations}")
    print(f"   - vocab_annotations: {test_sentence.vocab_annotations}")
    
    print("\n🔍 新数据结构句子信息:")
    print(f"   - text_id: {test_new_sentence.text_id}")
    print(f"   - sentence_id: {test_new_sentence.sentence_id}")
    print(f"   - difficulty_level: {test_new_sentence.sentence_difficulty_level}")
    print(f"   - tokens_count: {len(test_new_sentence.tokens) if test_new_sentence.tokens else 0}")
    
    # 测试新对话记录功能
    print("\n🧪 测试新对话记录功能:")
    data_controller.dialogue_record.add_user_message(test_new_sentence, "Finne是什么意思？")
    data_controller.dialogue_record.add_ai_response(test_new_sentence, "Finne是德语名词，指鱼类的背鳍。")
    
    # 添加更多对话
    data_controller.dialogue_record.add_user_message(test_new_sentence, "这句话的语法结构是什么？")
    data_controller.dialogue_record.add_ai_response(test_new_sentence, "这是一个复合句，包含两个主句，用逗号连接。第一个主句是主系表结构，第二个主句是主谓宾结构。")
    
    data_controller.dialogue_record.add_user_message(test_new_sentence, "Die和ist的语法功能是什么？")
    data_controller.dialogue_record.add_ai_response(test_new_sentence, "Die是定冠词，ist是系动词sein的第三人称单数现在时形式。")
    
    # 显示句子详细信息
    print("\n📊 句子详细信息:")
    sentence_info = data_controller.dialogue_record.get_sentence_info(test_new_sentence)
    for key, value in sentence_info.items():
        print(f"   - {key}: {value}")
    
    # 显示token详细信息
    print("\n🔤 Token详细信息:")
    tokens_info = data_controller.dialogue_record.get_tokens_info(test_new_sentence)
    for key, value in tokens_info.items():
        if isinstance(value, list) and len(value) > 0:
            print(f"   - {key}: {value}")
        elif isinstance(value, dict) and value:
            print(f"   - {key}: {value}")
        elif not isinstance(value, (list, dict)):
            print(f"   - {key}: {value}")
    
    # 显示学习分析
    print("\n📈 学习分析:")
    analytics = data_controller.dialogue_record.get_learning_analytics(test_new_sentence)
    for key, value in analytics.items():
        if isinstance(value, dict):
            print(f"   - {key}:")
            for sub_key, sub_value in value.items():
                print(f"     * {sub_key}: {sub_value}")
        elif isinstance(value, list):
            print(f"   - {key}: {value}")
        else:
            print(f"   - {key}: {value}")
    
    # 显示对话记录
    print("\n📚 对话记录:")
    data_controller.dialogue_record.print_records_by_sentence(test_new_sentence)
    
    # 测试旧数据结构
    print("\n🧪 测试旧数据结构对话记录:")
    data_controller.dialogue_record.add_user_message(test_sentence, "这句话是什么意思？")
    data_controller.dialogue_record.add_ai_response(test_sentence, "这句话描述了鱼鳍的特征。")
    data_controller.dialogue_record.print_records_by_sentence(test_sentence)
    
    # 测试数据保存和加载
    print("\n💾 测试数据保存功能:")
    try:
        data_controller.dialogue_record.save_all_to_file("test_dialogue_record_new.json")
        print("✅ 数据保存成功")
        
        # 创建新的对话记录实例来测试加载
        from data_managers.dialogue_record_new import DialogueRecordBySentenceNew
        new_record = DialogueRecordBySentenceNew()
        new_record.load_from_file("test_dialogue_record_new.json")
        print("✅ 数据加载成功")
        
        # 验证加载的数据
        loaded_records = new_record.get_records_by_sentence(test_new_sentence)
        print(f"✅ 加载的对话记录数量: {len(loaded_records)}")
        
    except Exception as e:
        print(f"❌ 数据保存/加载失败: {e}")
    
    print("\n✅ 新对话记录功能测试完成！")

if __name__ == "__main__":
    test_new_dialogue_record() 