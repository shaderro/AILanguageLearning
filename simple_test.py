#!/usr/bin/env python3

from data_managers.data_controller import DataController
from data_managers.data_classes_new import Sentence as NewSentence, Token

print("开始测试新对话记录功能...")

# 创建数据控制器，启用新结构模式
data_controller = DataController(3, use_new_structure=True, save_to_new_data_class=True)

# 创建新数据结构的测试句子
test_new_sentence = NewSentence(
    text_id=2,
    sentence_id=1,
    sentence_body="Die Finne ist groß und stark gebogen.",
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
        )
    )
)

print("🔍 新数据结构句子信息:")
print(f"   - text_id: {test_new_sentence.text_id}")
print(f"   - sentence_id: {test_new_sentence.sentence_id}")
print(f"   - difficulty_level: {test_new_sentence.sentence_difficulty_level}")
print(f"   - tokens_count: {len(test_new_sentence.tokens) if test_new_sentence.tokens else 0}")

# 测试新对话记录功能
print("\n🧪 测试新对话记录功能:")
data_controller.dialogue_record.add_user_message(test_new_sentence, "Finne是什么意思？")
data_controller.dialogue_record.add_ai_response(test_new_sentence, "Finne是德语名词，指鱼类的背鳍。")

# 显示句子详细信息
sentence_info = data_controller.dialogue_record.get_sentence_info(test_new_sentence)
print(f"📊 句子详细信息: {sentence_info}")

# 显示对话记录
data_controller.dialogue_record.print_records_by_sentence(test_new_sentence)

print("\n✅ 新对话记录功能测试完成！") 