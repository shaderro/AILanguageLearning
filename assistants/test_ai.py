import json
import re
from data_managers.data_classes import OriginalText, Sentence
from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.chat_info.dialogue_history import DialogueHistory
from assistants.chat_info.session_state import SessionState
from assistants.chat_info.session_state import GrammarToAdd, VocabToAdd, GrammarSummary, VocabSummary, CheckRelevantDecision

def test_sub_assistent():
    sys_prompt = "你正在为一个AI语言学习助手工作，你负责判断用户输入是否与语言学习有关。" \
    "请只返回如下 JSON 格式：{{\"is_relevant\": true}} 或 {{\"is_relevant\": false}}"
    
    test_sub_assistent = SubAssistant(sys_prompt=sys_prompt, max_tokens=100, parse_json=True)
    user_prompt = "请问德语中的名词有多少种性别？"
    result = test_sub_assistent.run(user_prompt)
    print(result["is_relevant"])  # 应该输出 True 或 False
    print(type(result["is_relevant"]))

def test_dialogue_history():
    test_dialogue_history = DialogueHistory(max_turns=4)
    # 定义一个测试用的 Sentence
    test_sentence = Sentence(
        text_id=1,
        sentence_id=101,
        sentence_body="This is a test sentence.",
        grammar_annotations=[1, 2, 3],
        vocab_annotations=[4, 5, 6]
    )
    # 模拟对话历史
    message1 = [
        {"role": "user", "content": "user content 1"},
        {"role": "assistant", "content": "ai reply 1"}
    ]
    user_content = message1[0]["content"]
    ai_reply = message1[1]["content"]
    test_dialogue_history.add_message(user_content, ai_reply, test_sentence)
    print("round1: ")
    for i, message in enumerate(test_dialogue_history.messages_history):
        print(f"Message {i + 1}: {message}")

    message2 = [
        {"role": "user", "content": "user content 2"},
        {"role": "assistant", "content": "ai reply 2"}
    ]
    user_content = message2[0]["content"]
    ai_reply = message2[1]["content"]
    test_dialogue_history.add_message(user_content, ai_reply, test_sentence)
    print("round2: ")
    for i, message in enumerate(test_dialogue_history.messages_history):
        print(f"Message {i + 1}: {message}")

    message3 = [
        {"role": "user", "content": "user content 3"},
        {"role": "assistant", "content": "ai reply 3"}
    ]
    user_content = message3[0]["content"]
    ai_reply = message3[1]["content"]
    test_dialogue_history.add_message(user_content, ai_reply, test_sentence)
    print("round3: " )
    for i, message in enumerate(test_dialogue_history.messages_history):
        print(f"Message {i + 1}: {message}")

    message4 = [
        {"role": "user", "content": "user content 4"},
        {"role": "assistant", "content": "ai reply 4"}
    ]
    user_content = message4[0]["content"]
    ai_reply = message4[1]["content"]
    test_dialogue_history.add_message(user_content, ai_reply, test_sentence)
    print("round4: ")
    for i, message in enumerate(test_dialogue_history.messages_history):
        print(f"Message {i + 1}: {message}")

    message5 = [
        {"role": "user", "content": "user content 5"},
        {"role": "assistant", "content": "ai reply 5"}
    ]
    user_content = message5[0]["content"]
    ai_reply = message5[1]["content"]
    test_dialogue_history.add_message(user_content, ai_reply, test_sentence)
    print("round5: ")
    for i, message in enumerate(test_dialogue_history.messages_history):
        print(f"Message {i + 1}: {message}")


    message6 = [
        {"role": "user", "content": "user content 6"},
        {"role": "assistant", "content": "ai reply 6"}
    ]
    user_content = message6[0]["content"]
    ai_reply = message6[1]["content"]
    test_dialogue_history.add_message(user_content, ai_reply, test_sentence)
    print("round6: ")
    for i, message in enumerate(test_dialogue_history.messages_history):
        print(f"Message {i + 1}: {message}")

def test_sesseion_state():
    test_sesseion_state = SessionState(max_turns = 5)
    
    sentence = Sentence(
    text_id=2,
    sentence_id=202,
    sentence_body="This is another test sentence for session state.",
    grammar_annotations=[7, 8, 9],
    vocab_annotations=[10, 11, 12])

    test_sesseion_state.set_current_sentence(sentence)
    test_sesseion_state.set_current_input("This is a test input.")
    test_sesseion_state.set_current_response("This is a test response.")
    

    test_sesseion_state.set_check_relevant_decision(grammar=True, vocab=False)
    
    test_sesseion_state.set_grammar_summary("Test Grammar Rule", 
                                            "This is a test grammar rule summary.")
    
    test_sesseion_state.set_grammar_to_add("Test Grammar Rule",
                                           "This is a test grammar rule summary")
    
    print("Session State Details:")
    print(f"Current Sentence: {test_sesseion_state.current_sentence}")
    print(f"Current Input: {test_sesseion_state.current_input}")
    print(f"Current Response: {test_sesseion_state.current_response}")
    print(f"Check Relevant Decision: {test_sesseion_state.check_relevant_decision}")
    print(f"Grammar Summary: {test_sesseion_state.summarized_result}")
    print(f"Grammar To Add: {test_sesseion_state.grammar_to_add}")
    print(f"Vocab To Add: {test_sesseion_state.vocab_to_add}")

#test_dialogue_history()
test_sesseion_state()