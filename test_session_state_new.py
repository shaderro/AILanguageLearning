#!/usr/bin/env python3

from assistants.chat_info.session_state import SessionState
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence, Token

def test_session_state_new():
    print("🧪 开始测试新session_state功能...")
    
    # 创建session_state实例
    session_state = SessionState()
    
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
    session_state.set_current_sentence(test_sentence)
    session_state.set_current_input("这句话是什么意思？")
    session_state.set_current_response("这句话描述了鱼鳍的特征。")
    
    print(f"✅ 是否为新数据结构: {session_state.is_new_structure_sentence()}")
    print(f"✅ 句子难度: {session_state.get_sentence_difficulty()}")
    print(f"✅ 困难词汇: {session_state.get_hard_tokens()}")
    print(f"✅ 语法标记: {session_state.get_grammar_markers()}")
    
    sentence_info = session_state.get_current_sentence_info()
    print(f"📊 句子信息: {sentence_info}")
    
    learning_context = session_state.get_learning_context()
    print(f"📈 学习上下文: {learning_context}")
    
    # 测试新数据结构
    print("\n🧪 测试新数据结构:")
    session_state.set_current_sentence(test_new_sentence)
    session_state.set_current_input("Finne是什么意思？")
    session_state.set_current_response("Finne是德语名词，指鱼类的背鳍。")
    
    # 添加一些语法和词汇总结
    session_state.add_grammar_summary("主系表结构", "Die Finne ist groß 是典型的主系表结构")
    session_state.add_vocab_summary("Finne")
    session_state.add_grammar_to_add("德语定冠词", "Die是德语定冠词，表示阴性单数")
    session_state.add_vocab_to_add("Finne")
    
    print(f"✅ 是否为新数据结构: {session_state.is_new_structure_sentence()}")
    print(f"✅ 句子难度: {session_state.get_sentence_difficulty()}")
    print(f"✅ 困难词汇: {session_state.get_hard_tokens()}")
    print(f"✅ 语法标记: {session_state.get_grammar_markers()}")
    
    sentence_info = session_state.get_current_sentence_info()
    print(f"📊 句子信息: {sentence_info}")
    
    tokens_info = session_state.get_current_sentence_tokens()
    print(f"🔤 Token信息: {tokens_info}")
    
    learning_context = session_state.get_learning_context()
    print(f"📈 学习上下文: {learning_context}")
    
    # 测试重置功能
    print("\n🧪 测试重置功能:")
    session_state.reset()
    
    print(f"✅ 重置后句子: {session_state.current_sentence}")
    print(f"✅ 重置后输入: {session_state.current_input}")
    print(f"✅ 重置后响应: {session_state.current_response}")
    print(f"✅ 重置后总结数量: {len(session_state.summarized_results)}")
    print(f"✅ 重置后语法添加数量: {len(session_state.grammar_to_add)}")
    print(f"✅ 重置后词汇添加数量: {len(session_state.vocab_to_add)}")
    
    print("\n✅ 新session_state功能测试完成！")

if __name__ == "__main__":
    test_session_state_new() 