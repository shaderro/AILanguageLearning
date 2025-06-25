from data_managers.data_controller import DataController
from assistants.main_assistant import MainAssistant
from data_managers.data_classes import Sentence
import json

data_controller = DataController()
main_assistant = MainAssistant(data_controller)

if __name__ == "__main__":
    
    data_controller.load_data(
        "data/grammar_rules.json",
        "data/vocab_expressions.json",
        "data/original_texts.json"
    )

    print("✅ 启动语言学习助手。默认引用句如下：")
    test_sentence_str = (
        "Wikipedia is a free content online encyclopedia website in 344 languages of the world in which 342 languages are currently active and 14 are closed. "
)
    print("引用句（Quoted Sentence）:")
    print(test_sentence_str)
    test_sentence = Sentence(
        text_id=1,
        sentence_id=1,
        sentence_body=test_sentence_str,
        grammar_annotations=[],
        vocab_annotations=[]
    )
    data_controller.text_manager.add_text("Test Text")
    data_controller.text_manager.add_sentence_to_text(1, test_sentence_str)
    while True:
        user_input = input("\n🗨️ 请输入你的问题（或输入 q 退出）: ").strip()
        if user_input.lower() in ["q", "quit", "exit"]:
            data_controller.save_data(
                "data/grammar_rules.json",
                "data/vocab_expressions.json",
                "data/original_texts.json"
            )
            print("👋 已退出语言学习助手。")
            break
        if not user_input:
            print("⚠️ 输入为空，请重新输入。")
            continue
        main_assistant.run(test_sentence, user_input)