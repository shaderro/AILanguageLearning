from data_managers.data_controller import DataController
from assistants.main_assistant import MainAssistant
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence, Token
import json

data_controller = DataController(3, use_new_structure=True, save_to_new_data_class=True)
main_assistant = MainAssistant(data_controller, 3)

if __name__ == "__main__":
    
    data_controller.load_data(
        "data/grammar_rules.json",
        "data/vocab_expressions.json",
        "data/original_texts.json",
        "data/dialogue_record.json",
        "data/dialogue_history.json"
    )
    print("✅ 启动语言学习助手。默认引用句如下：")
    test_sentence_str = (
        " Die Finne ist groß und stark gebogen, sie besitzt dabei zugleich eine sehr breite Basis. "
)
    print("引用句（Quoted Sentence）:")
    print(test_sentence_str)
    
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
    
    print("🔍 新数据结构句子信息:")
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
    data_controller.dialogue_record.add_ai_response(test_new_sentence, "这是一个复合句，包含两个主句，用逗号连接。")
    
    # 显示句子详细信息
    sentence_info = data_controller.dialogue_record.get_sentence_info(test_new_sentence)
    print(f"📊 句子详细信息: {sentence_info}")
    
    # 显示token详细信息
    tokens_info = data_controller.dialogue_record.get_tokens_info(test_new_sentence)
    print(f"🔤 Token详细信息: {tokens_info}")
    
    # 显示学习分析
    analytics = data_controller.dialogue_record.get_learning_analytics(test_new_sentence)
    print(f"📈 学习分析: {analytics}")
    
    # 显示对话记录
    data_controller.dialogue_record.print_records_by_sentence(test_new_sentence)
    
    # 测试session_state功能
    print("\n🧪 测试session_state功能:")
    main_assistant.session_state.set_current_sentence(test_new_sentence)
    main_assistant.session_state.set_current_input("Finne是什么意思？")
    main_assistant.session_state.set_current_response("Finne是德语名词，指鱼类的背鳍。")
    
    # 添加一些语法和词汇总结
    main_assistant.session_state.add_grammar_summary("主系表结构", "Die Finne ist groß 是典型的主系表结构")
    main_assistant.session_state.add_vocab_summary("Finne")
    main_assistant.session_state.add_grammar_to_add("德语定冠词", "Die是德语定冠词，表示阴性单数")
    main_assistant.session_state.add_vocab_to_add("Finne")
    
    # 显示session_state信息
    print(f"✅ 是否为新数据结构: {main_assistant.session_state.is_new_structure_sentence()}")
    print(f"✅ 句子难度: {main_assistant.session_state.get_sentence_difficulty()}")
    print(f"✅ 困难词汇: {main_assistant.session_state.get_hard_tokens()}")
    print(f"✅ 语法标记: {main_assistant.session_state.get_grammar_markers()}")
    
    sentence_info = main_assistant.session_state.get_current_sentence_info()
    print(f"📊 Session句子信息: {sentence_info}")
    
    tokens_info = main_assistant.session_state.get_current_sentence_tokens()
    print(f"🔤 Session Token信息: {tokens_info}")
    
    learning_context = main_assistant.session_state.get_learning_context()
    print(f"📈 Session学习上下文: {learning_context}")
    
    data_controller.text_manager.add_text("Test Text")
    data_controller.text_manager.add_sentence_to_text(1, test_sentence_str)
    while True:
        user_input = input("\n🗨️ 请输入你的问题（或输入 q 退出）: ").strip()
        if user_input.lower() in ["q", "quit", "exit"]:
            data_controller.save_data(
                "data/grammar_rules.json",
                "data/vocab_expressions.json",
                "data/original_texts.json",
                "data/dialogue_record.json",
                "data/dialogue_history.json"
            )
            print("👋 已退出语言学习助手。")
            break
        if not user_input:
            print("⚠️ 输入为空，请重新输入。")
            continue
        main_assistant.run(test_sentence, user_input)