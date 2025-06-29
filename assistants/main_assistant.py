import os
import json
print("✅ 当前运行文件：", __file__)
print("✅ 当前工作目录：", os.getcwd())
import re
from assistants.chat_info.dialogue_history import DialogueHistory
from assistants.chat_info.session_state import SessionState, CheckRelevantDecision, GrammarSummary, VocabSummary, GrammarToAdd, VocabToAdd
from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.check_if_grammar_relevant_assistant import CheckIfGrammarRelevantAssistant
from assistants.sub_assistants.check_if_vocab_relevant_assistant import CheckIfVocabRelevantAssistant
from assistants.sub_assistants.summarize_grammar_rule import SummarizeGrammarRuleAssistant
from assistants.sub_assistants.check_if_relevant import CheckIfRelevant
from assistants.sub_assistants.answer_question import AnswerQuestionAssistant
from assistants.sub_assistants.summarize_vocab import SummarizeVocabAssistant
from assistants.sub_assistants.compare_grammar_rule import CompareGrammarRuleAssistant
from assistants.sub_assistants.grammar_example_explanation import GrammarExampleExplanationAssistant
from assistants.sub_assistants.vocab_example_explanation import VocabExampleExplanationAssistant
from data_managers.data_classes import Sentence
from data_managers import data_controller
from data_managers.dialogue_record import DialogueRecordBySentence

class MainAssistant:
    
    def __init__(self, data_controller_instance=None, max_turns = None):
        self.session_state = SessionState()
        self.dialogue_history = DialogueHistory(max_turns)
        self.check_if_relevant = CheckIfRelevant()
        self.check_if_grammar_relavent_assistant = CheckIfGrammarRelevantAssistant()
        self.check_if_vocab_relevant_assistant = CheckIfVocabRelevantAssistant()
        self.answer_question_assistant = AnswerQuestionAssistant()
        self.summarize_grammar_rule_assistant = SummarizeGrammarRuleAssistant()
        self.summarize_vocab_rule_assistant = SummarizeVocabAssistant()
        self.compare_grammar_rule_assistant = CompareGrammarRuleAssistant()
        self.grammar_example_explanation_assistant = GrammarExampleExplanationAssistant()
        self.vocab_example_explanation_assistant = VocabExampleExplanationAssistant()
        self.data_controller = data_controller_instance if data_controller_instance else data_controller.DataController()
        self.dialogue_record = DialogueRecordBySentence()

    def run(self, quoted_sentence: Sentence, user_question: str):
        """
        主处理函数，接收引用的句子、用户问题和AI响应，并进行相关处理。
        """
        self.session_state.reset()  # 重置会话状态
        self.dialogue_history.add_message(user_input=user_question, ai_response="", quoted_sentence=quoted_sentence)
        self.dialogue_record.add_user_message(quoted_sentence, user_question)
        #是否和主题相关
        if(self.check_if_topic_relevant_function(quoted_sentence, user_question) is False):
            print("The question is not relevant to language learning, skipping processing.")
            self.dialogue_record.add_ai_response(quoted_sentence, "The question is not relevant to language learning, skipping processing.")
            return
        print("The question is relevant to language learning, proceeding with processing...")
        #回答问题
        ai_response = self.answer_question_function(quoted_sentence, user_question)
        self.dialogue_record.add_ai_response(quoted_sentence, ai_response)
        #检查是否加入新语法和词汇
        self.handle_grammar_vocab_function(quoted_sentence, user_question, ai_response)
        self.add_new_to_data()
        print("✅ 处理完成，已更新会话状态和对话历史。")
        self.print_data_controller_data()
        return

    def print_data_controller_data(self):
        """
        打印数据管理器中的数据，便于调试和验证。
        """
        print("Grammar Rules:", self.data_controller.grammar_manager.get_all_rules_name())
        print("Vocab List:", self.data_controller.vocab_manager.get_all_vocab_body())
        #print("Session State:", self.session_state)

    def check_if_topic_relevant_function(self, quoted_sentence: Sentence, user_question: str) -> bool:
        result = self.check_if_relevant.run(
            quoted_sentence.sentence_body,
            user_question
        )
        if(result.get("is_relevant") is True):
            self.session_state.set_current_input(user_question)
            self.session_state.set_current_sentence(quoted_sentence)
        return result.get("is_relevant", False)

    def answer_question_function(self, quoted_sentence: Sentence, user_question: str) -> str:
        """
        使用AI回答用户问题。
        """
        ai_response = self.answer_question_assistant.run(
            quoted_sentence.sentence_body,
            user_question
        )
        print("AI Response:", ai_response)
        self.session_state.set_current_response(ai_response)
        self.dialogue_history.add_message(user_input=user_question, ai_response=ai_response, quoted_sentence=quoted_sentence)

        return ai_response

    def fuzzy_match_expressions(self, expr1: str, expr2: str) -> bool:
        """
        忽略大小写，支持'...'通配匹配，即表达之间允许省略部分内容
        """
        e1 = expr1.strip().lower()
        e2 = expr2.strip().lower()

        # 如果两个表达完全一致
        if e1 == e2:
            return True

        # 如果 e1 包含省略号
        if '...' in e1:
            pattern = re.escape(e1).replace(r'\.\.\.', '.*')
            return re.fullmatch(pattern, e2) is not None

        # 如果 e2 包含省略号
        if '...' in e2:
            pattern = re.escape(e2).replace(r'\.\.\.', '.*')
            return re.fullmatch(pattern, e1) is not None

        return False

    def handle_grammar_vocab_function(self, quoted_sentence: Sentence, user_question: str, ai_response: str):
        """
        处理与语法和词汇相关的操作。
        """
        # 检查是否与语法相关
        grammar_relevant_response = self.check_if_grammar_relavent_assistant.run(quoted_sentence.sentence_body, user_question, ai_response)
        vocab_relevant_response = self.check_if_vocab_relevant_assistant.run(quoted_sentence.sentence_body, user_question, ai_response)
        
        self.session_state.set_check_relevant_decision(
            grammar=grammar_relevant_response.get("is_grammar_relevant", False),
            vocab=vocab_relevant_response.get("is_vocab_relevant", False)
        )

        if self.session_state.check_relevant_decision.grammar:
            print("✅ 语法相关，开始总结语法规则。")
            grammar_summary = self.summarize_grammar_rule_assistant.run(
                self.session_state.current_sentence.sentence_body,
                self.session_state.current_input,
                self.session_state.current_response
            )
            if isinstance(grammar_summary, dict):
                self.session_state.add_grammar_summary(
                    grammar_summary.get("grammar_rule_name", "Unknown"),
                    grammar_summary.get("grammar_rule_summary", "No explanation provided")
                )
            elif isinstance(grammar_summary, list) and len(grammar_summary) > 0:
                for grammar in grammar_summary:
                    self.session_state.add_grammar_summary(
                        name=grammar.get("grammar_rule_name", "Unknown"),
                        summary=grammar.get("grammar_rule_summary", "No explanation provided")
                    )

        # 检查是否与词汇相关
        if self.session_state.check_relevant_decision.vocab:
            print("✅ 词汇相关，开始总结词汇。")
            vocab_summary = self.summarize_vocab_rule_assistant.run(
                self.session_state.current_sentence.sentence_body,
                self.session_state.current_input,
                self.session_state.current_response
            )
            if isinstance(vocab_summary, dict):
                self.session_state.add_vocab_summary(vocab_summary.get("vocab", "Unknown"))
            elif isinstance(vocab_summary, list) and len(vocab_summary) > 0:
                for vocab in vocab_summary:
                    self.session_state.add_vocab_summary(
                        vocab=vocab.get("vocab", "Unknown")
                    )

        current_grammar_rule_names = self.data_controller.grammar_manager.get_all_rules_name()
        new_grammar_summaries = []
        for result in self.session_state.summarized_results:
            has_similar = False
            for existing_rule in current_grammar_rule_names:
                if isinstance(result, GrammarSummary):
                    compare_result = self.compare_grammar_rule_assistant.run(
                        existing_rule,
                        result.grammar_rule_name,
                        verbose=True
                    )
                    if compare_result.get("is_similar", False):
                        print(f"✅ 语法规则 '{existing_rule}' 与现有规则 '{result.grammar_rule_name}' 相似")
                        has_similar = True
                        existing_rule_id = self.data_controller.grammar_manager.get_id_by_rule_name(existing_rule)
                        example_explanation = self.grammar_example_explanation_assistant.run(
                            sentence=self.session_state.current_sentence,
                            grammar=self.data_controller.grammar_manager.get_rule_by_id(existing_rule_id).name)
                        self.data_controller.add_grammar_example(
                            rule_id=existing_rule_id,
                            text_id=self.session_state.current_sentence.text_id,
                            sentence_id=self.session_state.current_sentence.sentence_id,
                            explanation_context=example_explanation
                        )
                        break  # 跳出内层循环
            if not has_similar and isinstance(result, GrammarSummary):
                print(f"🆕 新语法知识点：'{result.grammar_rule_name}'，将添加到已有规则中")
                new_grammar_summaries.append(result)

        for grammar in new_grammar_summaries:
            self.session_state.add_grammar_to_add(
                #GrammarToAdd(
                    rule_name=grammar.grammar_rule_name,
                    rule_explanation=grammar.grammar_rule_summary
                #)
            )

        print("grammar to add：", self.session_state.grammar_to_add)
        #add to data
        
        current_vocab_list = self.data_controller.vocab_manager.get_all_vocab_body()
        new_vocab = []
        for result in self.session_state.summarized_results:
            has_similar = False
            for vocab in current_vocab_list:
                if isinstance(result, VocabSummary):
                    compare_result = self.fuzzy_match_expressions(vocab,result.vocab)
                    if compare_result:
                        print(f"✅ 词汇 '{vocab}' 与现有词汇 '{result.vocab}' 相似")
                        has_similar = True
                        existing_vocab_id = self.data_controller.vocab_manager.get_id_by_vocab_body(vocab)
                        example_explanation = self.vocab_example_explanation_assistant.run(
                            sentence=self.session_state.current_sentence,
                            vocab=vocab
                        )
                        self.data_controller.add_vocab_example(
                            vocab_id=existing_vocab_id,
                            text_id=self.session_state.current_sentence.text_id,
                            sentence_id=self.session_state.current_sentence.sentence_id,
                            context_explanation=example_explanation
                        )
                        break
            if not has_similar and isinstance(result, VocabSummary):
                print(f"🆕 新词汇知识点：'{result.vocab}'，将添加到已有规则中")
                new_vocab.append(result)
        print("新单词列表：", new_vocab) 
        for vocab in new_vocab:
            self.session_state.add_vocab_to_add(
                #VocabToAdd(
                    vocab=vocab.vocab
                #)
            )

    def add_new_to_data(self):
        """
        将新语法和词汇添加到数据管理器中。
        """
        if self.session_state.grammar_to_add:
            for grammar in self.session_state.grammar_to_add:
                self.data_controller.add_new_grammar_rule(
                    rule_name=grammar.rule_name,
                    rule_explanation=grammar.rule_explanation
                )
            example_explanation = self.grammar_example_explanation_assistant.run(
                            sentence=self.session_state.current_sentence,
                            grammar=grammar.rule_name)
                        
            self.data_controller.add_grammar_example(
                rule_id=self.data_controller.grammar_manager.get_id_by_rule_name(grammar.rule_name),
                text_id=self.session_state.current_sentence.text_id,
                sentence_id=self.session_state.current_sentence.sentence_id,
                explanation_context=example_explanation
            )

        if self.session_state.vocab_to_add:
            for vocab in self.session_state.vocab_to_add:
                self.data_controller.add_new_vocab(vocab_body=vocab.vocab, explanation="test explanation")  
            
            example_explanation = self.vocab_example_explanation_assistant.run(
                            sentence=self.session_state.current_sentence,
                            vocab=vocab.vocab)
            self.data_controller.add_vocab_example(
                vocab_id=self.data_controller.vocab_manager.get_id_by_vocab_body(vocab.vocab),
                text_id=self.session_state.current_sentence.text_id,
                sentence_id=self.session_state.current_sentence.sentence_id,
                context_explanation=example_explanation
            )

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
    user_input = "in which是什么语法知识点？为什么用are而不是is？请总结出两个知识点" 
    main_assistant.run(test_sentence, user_input)

    #add sentence to example logic
    