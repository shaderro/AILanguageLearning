from data_managers.data_controller import DataController
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence, Token

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
if test_new_sentence.tokens:
    print(f"   - 前3个tokens: {[(t.token_body, t.token_type, t.difficulty_level) for t in test_new_sentence.tokens[:3]]}")

# 测试新对话记录功能
print("\n🧪 测试新对话记录功能:")
data_controller.dialogue_record.add_user_message(test_new_sentence, "Finne是什么意思？")
data_controller.dialogue_record.add_ai_response(test_new_sentence, "Finne是德语名词，指鱼类的背鳍。")

# 添加更多对话
data_controller.dialogue_record.add_user_message(test_new_sentence, "这句话的语法结构是什么？")
data_controller.dialogue_record.add_ai_response(test_new_sentence, "这是一个复合句，包含两个主句，用逗号连接。第一个主句是主系表结构，第二个主句是主谓宾结构。")

# 显示句子详细信息
sentence_info = data_controller.dialogue_record.get_sentence_info(test_new_sentence)
print(f"📊 句子详细信息: {sentence_info}")

# 显示对话记录
data_controller.dialogue_record.print_records_by_sentence(test_new_sentence)

# 测试旧数据结构
print("\n🧪 测试旧数据结构对话记录:")
data_controller.dialogue_record.add_user_message(test_sentence, "这句话是什么意思？")
data_controller.dialogue_record.add_ai_response(test_sentence, "这句话描述了鱼鳍的特征。")
data_controller.dialogue_record.print_records_by_sentence(test_sentence)

print("\n✅ 新对话记录功能测试完成！") 