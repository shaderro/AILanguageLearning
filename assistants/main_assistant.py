import os
import json
print("✅ 当前运行文件：", __file__)
print("✅ 当前工作目录：", os.getcwd())
from assistants.chat_info.dialogue_history import DialogueHistory
from assistants.chat_info.session_state import SessionState, CheckRelevantDecision, GrammarSummary, VocabSummary, GrammarToAdd, VocabToAdd
from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.check_if_grammar_relevant_assistant import CheckIfGrammarRelevantAssistant
from assistants.sub_assistants.check_if_vocab_relevant_assistant import CheckIfVocabRelevantAssistant
from assistants.sub_assistants.summarize_grammar_rule import SummarizeGrammarRuleAssistant
from assistants.sub_assistants.check_if_relevant import CheckIfRelevant
from assistants.sub_assistants.answer_question import AnswerQuestionAssistant
from assistants.sub_assistants.summarize_vocab import SummarizeVocabAssistant
from data_managers.data_classes import Sentence

class MainAssistant:
    
    def __init__(self):
        self.session_state = SessionState(max_turns=1)
        self.dialogue_history = DialogueHistory(max_turns=1)
        self.check_if_relevant = CheckIfRelevant()
        self.check_if_grammar_relavent_assistant = CheckIfGrammarRelevantAssistant()
        self.check_if_vocab_relevant_assistant = CheckIfVocabRelevantAssistant()
        self.answer_question_assistant = AnswerQuestionAssistant()
        self.summarize_grammar_rule_assistant = SummarizeGrammarRuleAssistant()
        self.summarize_vocab_rule_assistant = SummarizeVocabAssistant()

    #TODO: create a main assistant when first quoting a sentence, it will create a session state and dialogue history

    def run(self, quoted_sentence: Sentence, user_question: str):
        """
        主处理函数，接收引用的句子、用户问题和AI响应，并进行相关处理。
        """
        check_relevant_result = self.check_if_relevant.run(
            quoted_sentence.sentence_body,
            user_question
        )
        if not check_relevant_result.get("is_relevant", False):
            print("The sentence is not relevant to the question.")
            return
        # 如果句子与问题相关，继续处理
        print("The sentence is relevant to the question, proceeding with processing...")
        
        self.session_state.set_current_input(user_question)
        self.session_state.set_current_sentence(quoted_sentence)
        #回答问题
        ai_response = self.answer_question_assistant.run(
            quoted_sentence.sentence_body,
            user_question,
            #dialogue_context=self.dialogue_history.get_dialogue_context()
        )
        print("AI Response:", ai_response)
        self.session_state.set_current_response(ai_response)
        self.dialogue_history.add_message(
            user_input=user_question,
            ai_response=ai_response,
            quoted_sentence=quoted_sentence
        )
        #检查是否与语法相关
        grammar_relevant_response = self.check_if_grammar_relavent_assistant.run(quoted_sentence.sentence_body, user_question, ai_response)
        vocab_relevant_response = self.check_if_vocab_relevant_assistant.run(quoted_sentence.sentence_body, user_question, ai_response)
        #设置session_state的相关状态
        self.session_state.set_check_relevant_decision(
            grammar=grammar_relevant_response.get("is_grammar_relevant", False),
            vocab=vocab_relevant_response.get("is_vocab_relevant", False)
        )

        if self.session_state.check_relevant_decision.grammar:
            # get grammar summary result
            print("Grammar is relevant, processing grammar summary...")
            grammar_summary = self.summarize_grammar_rule_assistant.run(
                quoted_sentence.sentence_body,
                user_question,
                ai_response,
                verbose=True
                #dialogue_context=self.dialogue_history.get_dialogue_context()
            )
            print("grammar_summary type:", type(grammar_summary))
            rule_name=grammar_summary.get("grammar_rule_name", "Unknown")
            print("Grammar Rule Name:", rule_name)
            rule_summary=grammar_summary.get("grammar_rule_summary", "No summary provided")
            print("Grammar Rule Summary:", rule_summary)
            for grammar in grammar_summary:
                if isinstance(grammar, dict):
                    for key, value in grammar.items():
                        print(f"{key}: {value}")
            for grammar in grammar_summary:
                  # 确保 grammar 是合法的 JSON 格式
                print("Grammar type:", type(grammar))
                #print("loaded_grammar type:", type(loaded_grammar))
                #print("Grammar content:", loaded_grammar)
                print("Grammar content:", grammar)
                #loaded_grammar = json.loads(grammar)
            #for grammar in grammar_summary:
                # add grammar to session state
                #假设是新的语法规则

            """    
                self.session_state.grammar_to_add.append(
                    GrammarToAdd(
                        rule_name=grammar.get("grammar_rule_name", "Unknown"),
                        rule_explanation=grammar.get("grammar_rule_summary", "No explanation provided")
                    )
                )
            """
            #self.session_state.add_grammar_summary(
            print("Grammar Summary:", grammar_summary)
        if self.session_state.check_relevant_decision.vocab:
            # get vocab summary result
            print("Vocab is relevant, processing vocab summary...")
            vocab_summary = self.summarize_vocab_rule_assistant.run(
                quoted_sentence.sentence_body,
                user_question,
                ai_response,
                #dialogue_context=self.dialogue_history.get_dialogue_context()
            )
            """""
            for vocab in vocab_summary:
                # add vocab to session state
                #假设是新的词汇
                self.session_state.vocab_to_add.append(
                    VocabToAdd(
                        vocab=vocab.get("vocab", "Unknown")
                    )
                )
            print("Vocab Summary:", vocab_summary)
            """
        return

'''
main_assistant = MainAssistant()
test_sentence_str = "In York, Upper Canada, members of the Family Compact destroyed William Lyon Mackenzie's printing press in the Types Riot after Mackenzie accused them of corruption."
test_sentence = Sentence(text_id= 0, sentence_id = 0, sentence_body=test_sentence_str, grammar_annotations=[], vocab_annotations=[])
test_user_question = "我没懂"
#main_assistant.run(test_sentence, test_user_question)
'''

if __name__ == "__main__":
    print("✅ 启动语言学习助手。默认引用句如下：")
    test_sentence_str = (
        "Wikipedia is a free content online encyclopedia website in 344 languages of the world in which 342 languages are currently active and 14 are closed. "
)
    print("引用句（Quoted Sentence）:")
    print(test_sentence_str)
    test_sentence = Sentence(
        text_id=0,
        sentence_id=0,
        sentence_body=test_sentence_str,
        grammar_annotations=[],
        vocab_annotations=[]
    )
    
    main_assistant = MainAssistant()
    user_input = "in which是什么意思"
    main_assistant.run(test_sentence, user_input)
    """"
    while True:
        user_input = input("\n🗨️ 请输入你的问题（或输入 q 退出）: ").strip()
        if user_input.lower() in ["q", "quit", "exit"]:
            print("👋 已退出语言学习助手。")
            break
        if not user_input:
            print("⚠️ 输入为空，请重新输入。")
            continue
        main_assistant.run(test_sentence, user_input)
"""""