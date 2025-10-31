import os
import json
print("✅ 当前运行文件：", __file__)
print("✅ 当前工作目录：", os.getcwd())
import re
from backend.assistants.chat_info.dialogue_history import DialogueHistory
from backend.assistants.chat_info.session_state import SessionState, CheckRelevantDecision, GrammarSummary, VocabSummary, GrammarToAdd, VocabToAdd
from backend.assistants.chat_info.selected_token import SelectedToken, create_selected_token_from_text
from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.check_if_grammar_relevant_assistant import CheckIfGrammarRelevantAssistant
from backend.assistants.sub_assistants.check_if_vocab_relevant_assistant import CheckIfVocabRelevantAssistant
from backend.assistants.sub_assistants.summarize_grammar_rule import SummarizeGrammarRuleAssistant
from backend.assistants.sub_assistants.check_if_relevant import CheckIfRelevant
from backend.assistants.sub_assistants.answer_question import AnswerQuestionAssistant
from backend.assistants.sub_assistants.summarize_vocab import SummarizeVocabAssistant
# CompareGrammarRuleAssistant（语法相似度比较，已启用）
from backend.assistants.sub_assistants.compare_grammar_rule import CompareGrammarRuleAssistant
from backend.assistants.sub_assistants.grammar_example_explanation import GrammarExampleExplanationAssistant
from backend.assistants.sub_assistants.vocab_example_explanation import VocabExampleExplanationAssistant
from backend.assistants.sub_assistants.vocab_explanation import VocabExplanationAssistant
from backend.data_managers.data_classes import Sentence
# 导入新数据结构类
try:
    from backend.data_managers.data_classes_new import Sentence as NewSentence, Token
    NEW_STRUCTURE_AVAILABLE = True
except ImportError:
    NEW_STRUCTURE_AVAILABLE = False
    print("⚠️ 新数据结构类不可用，将使用旧结构")
from backend.data_managers import data_controller
from backend.data_managers.dialogue_record import DialogueRecordBySentence
# 只读能力探测适配层（不改变业务逻辑）
from backend.assistants.adapters import CapabilityDetector, DataAdapter, GrammarRuleAdapter, VocabAdapter

# 定义联合类型，支持新旧两种 Sentence 类型
from typing import Union
SentenceType = Union[Sentence, NewSentence] if NEW_STRUCTURE_AVAILABLE else Sentence

# 全局开关：临时关闭语法相关能力（对比/生成规则与例句）
DISABLE_GRAMMAR_FEATURES = True

class MainAssistant:
    
    def __init__(self, data_controller_instance=None, max_turns=100, session_state_instance=None):
        # 允许传入外部的 session_state 实例，以便共享状态
        self.session_state = session_state_instance if session_state_instance else SessionState()
        self.check_if_relevant = CheckIfRelevant()
        self.check_if_grammar_relavent_assistant = CheckIfGrammarRelevantAssistant()
        self.check_if_vocab_relevant_assistant = CheckIfVocabRelevantAssistant()
        self.answer_question_assistant = AnswerQuestionAssistant()
        self.summarize_grammar_rule_assistant = SummarizeGrammarRuleAssistant()
        self.summarize_vocab_rule_assistant = SummarizeVocabAssistant()
        # 语法比较功能（已启用）
        self.compare_grammar_rule_assistant = CompareGrammarRuleAssistant()
        self.grammar_example_explanation_assistant = GrammarExampleExplanationAssistant()
        self.vocab_example_explanation_assistant = VocabExampleExplanationAssistant()
        self.vocab_explanation_assistant = VocabExplanationAssistant()
        self.data_controller = data_controller_instance if data_controller_instance else data_controller.DataController(max_turns)
        # 使用 data_controller 的实例而不是创建新的
        self.dialogue_record = self.data_controller.dialogue_record
        self.dialogue_history = self.data_controller.dialogue_history
        
        # 只读：能力探测缓存（不用于业务分支，仅打印）
        self._capabilities_cache = {}

    def run(self, quoted_sentence: SentenceType, user_question: str, selected_text: str = None):
        """
        主处理函数，支持用户选择特定token或整句话进行提问
        
        Args:
            quoted_sentence: 完整的句子对象（支持新旧两种类型）
            user_question: 用户问题
            selected_text: 用户选择的特定文本（可选），如果为None则使用完整句子
        """
        # 🔧 优化：只重置处理结果，保留上下文（避免重复设置）
        # 上下文（sentence、input、token）已由 Mock Server 通过 session API 设置
        self.session_state.reset_processing_results()
        
        # 📋 使用已设置的上下文，或者从参数设置（兼容直接调用）
        # 如果 session_state 中没有上下文，说明是直接调用（非 Mock Server），需要设置
        if not self.session_state.current_sentence:
            print("📝 [MainAssistant] Session state 为空，从参数设置上下文")
            
            # 创建SelectedToken对象
            if selected_text:
                selected_token = create_selected_token_from_text(quoted_sentence, selected_text)
                effective_sentence_body = selected_text
                print(f"🎯 用户选择了特定文本: '{selected_text}'")
            else:
                selected_token = SelectedToken.from_full_sentence(quoted_sentence)
                effective_sentence_body = quoted_sentence.sentence_body
                print(f"📖 用户选择了整句话: '{quoted_sentence.sentence_body}'")
            
            # 设置会话状态
            self.session_state.set_current_sentence(quoted_sentence)
            self.session_state.set_current_selected_token(selected_token)
            self.session_state.set_current_input(user_question)
        else:
            print("✅ [MainAssistant] 使用 session_state 中的上下文（已由 Mock Server 设置）")
            # 从 session_state 读取已设置的值
            effective_sentence_body = selected_text if selected_text else (
                self.session_state.current_selected_token.token_text 
                if self.session_state.current_selected_token 
                else quoted_sentence.sentence_body
            )
        
        # 只读演示：能力探测与打印（不改业务逻辑）
        self._log_sentence_capabilities(quoted_sentence)
        
        # 记录用户消息（包含selected_token信息）
        # 使用 session_state 中的 selected_token
        current_selected_token = self.session_state.current_selected_token
        if current_selected_token:
            self.dialogue_record.add_user_message(quoted_sentence, user_question, current_selected_token)
        else:
            # 兜底：如果 session_state 中没有，创建一个整句选择的 token
            fallback_token = SelectedToken.from_full_sentence(quoted_sentence)
            self.dialogue_record.add_user_message(quoted_sentence, user_question, fallback_token)
        
        print("The question is relevant to language learning, proceeding with processing...")
        
        # 回答问题（会在内部设置 current_response）
        ai_response = self.answer_question_function(quoted_sentence, user_question, effective_sentence_body)
        
        # 记录AI响应（包含selected_token信息）
        self.dialogue_record.add_ai_response(quoted_sentence, ai_response)
        
        # 检查是否加入新语法和词汇
        self.handle_grammar_vocab_function(quoted_sentence, user_question, ai_response, effective_sentence_body)
        self.add_new_to_data()
        
        print("✅ 处理完成，已更新会话状态和对话历史。")
        self.print_data_controller_data()
        return

    def print_data_controller_data(self):
        """
        打印数据管理器中的数据，便于调试和验证。
        """
        print("📚 Grammar Rules (by name):", self.data_controller.grammar_manager.get_all_rules_name())
        print("📖 Vocab List:", self.data_controller.vocab_manager.get_all_vocab_body())
        
        # 显示规则的ID顺序
        self.data_controller.grammar_manager.print_rules_order()
        
        #print("Session State:", self.session_state)

    def _ensure_sentence_integrity(self, sentence: SentenceType, context: str) -> bool:
        """
        确保句子完整性并打印调试信息
        
        Args:
            sentence: 要验证的句子对象（支持新旧两种类型）
            context: 验证上下文
            
        Returns:
            bool: 句子是否完整
        """
        if sentence and hasattr(sentence, 'text_id') and hasattr(sentence, 'sentence_id'):
            print(f"✅ {context}: 句子数据结构完整性验证通过 - text_id:{sentence.text_id}, sentence_id:{sentence.sentence_id}")
            return True
        else:
            print(f"❌ {context}: 句子数据结构完整性验证失败")
            return False

    def check_if_topic_relevant_function(self, quoted_sentence: SentenceType, user_question: str, effective_sentence_body: str = None) -> bool:
        sentence_to_check = effective_sentence_body if effective_sentence_body else quoted_sentence.sentence_body
        result = self.check_if_relevant.run(
            sentence_to_check,
            user_question
        )
        # 确保 result 是字典类型
        if isinstance(result, str):
            result = {"is_relevant": False}
        
        # 验证句子完整性
        self._ensure_sentence_integrity(quoted_sentence, "Check Relevant")
        
        return result.get("is_relevant", False)

    def answer_question_function(self, quoted_sentence: SentenceType, user_question: str, sentence_body: str) -> str:
        """
        使用AI回答用户问题。
        
        Args:
            quoted_sentence: 完整的句子对象
            user_question: 用户问题
            sentence_body: 用户选择的文本（可能是完整句子或选中的部分）
        """
        # 判断用户是选择了完整句子还是特定部分
        full_sentence = quoted_sentence.sentence_body
        
        # 如果 sentence_body 不等于完整句子，说明用户选择了特定部分
        if sentence_body != full_sentence:
            # 用户选择了特定文本（如单词或短语）
            quoted_part = sentence_body
            print(f"🎯 [AnswerQuestion] 用户选择了特定文本: '{quoted_part}'")
            print(f"📖 [AnswerQuestion] 完整句子: '{full_sentence}'")
            ai_response = self.answer_question_assistant.run(
                full_sentence=full_sentence,
                user_question=user_question,
                quoted_part=quoted_part
            )
        else:
            # 用户选择了整句话
            print(f"📖 [AnswerQuestion] 用户选择了整句话: '{full_sentence}'")
            ai_response = self.answer_question_assistant.run(
                full_sentence=full_sentence,
                user_question=user_question
            )
        
        print("AI Response:", ai_response)
        if isinstance(ai_response, (dict, list)):
            ai_response = str(ai_response)
        # ✅ 设置响应（这里是唯一设置 current_response 的地方）
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

    def handle_grammar_vocab_function(self, quoted_sentence: SentenceType, user_question: str, ai_response: str, effective_sentence_body: str = None):
        """
        处理与语法和词汇相关的操作。
        """
        # 如果没有提供effective_sentence_body，使用完整句子
        if effective_sentence_body is None:
            effective_sentence_body = quoted_sentence.sentence_body
            
        # 检查是否与语法相关
        if DISABLE_GRAMMAR_FEATURES:
            print("⏸️ [MainAssistant] Grammar features are DISABLED (skip relevance/summarize/compare/generation)")
            grammar_relevant_response = {"is_grammar_relevant": False}
        else:
            grammar_relevant_response = self.check_if_grammar_relavent_assistant.run(effective_sentence_body, user_question, ai_response)
        vocab_relevant_response = self.check_if_vocab_relevant_assistant.run(effective_sentence_body, user_question, ai_response)
        
        # 确保响应是字典类型
        if isinstance(grammar_relevant_response, str):
            grammar_relevant_response = {"is_grammar_relevant": False}
        if isinstance(vocab_relevant_response, str):
            vocab_relevant_response = {"is_vocab_relevant": False}
        
        self.session_state.set_check_relevant_decision(
            grammar=grammar_relevant_response.get("is_grammar_relevant", False),
            vocab=vocab_relevant_response.get("is_vocab_relevant", False)
        )

        if (not DISABLE_GRAMMAR_FEATURES) and self.session_state.check_relevant_decision and self.session_state.check_relevant_decision.grammar:
            print("✅ 语法相关，开始总结语法规则。")
            # 确保所有参数都不为 None
            sentence_body = effective_sentence_body
            user_input = self.session_state.current_input if self.session_state.current_input else user_question
            ai_response_str = self.session_state.current_response if self.session_state.current_response else ai_response
            
            grammar_summary = self.summarize_grammar_rule_assistant.run(
                sentence_body,
                user_input,
                ai_response_str
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
        if self.session_state.check_relevant_decision and self.session_state.check_relevant_decision.vocab:
            print("✅ 词汇相关，开始总结词汇。")
            # 确保所有参数都不为 None
            sentence_body = effective_sentence_body
            user_input = self.session_state.current_input if self.session_state.current_input else user_question
            ai_response_str = self.session_state.current_response if self.session_state.current_response else ai_response
            
            vocab_summary = self.summarize_vocab_rule_assistant.run(
                sentence_body,
                user_input,
                ai_response_str
            )
            if isinstance(vocab_summary, dict):
                self.session_state.add_vocab_summary(vocab_summary.get("vocab", "Unknown"))
            elif isinstance(vocab_summary, list) and len(vocab_summary) > 0:
                for vocab in vocab_summary:
                    self.session_state.add_vocab_summary(
                        vocab=vocab.get("vocab", "Unknown")
                    )

        # 语法处理：检查相似度，为现有规则添加例句或添加新规则
        if DISABLE_GRAMMAR_FEATURES:
            print("⏸️ [MainAssistant] Grammar compare/new-rule flow disabled — skipping grammar pipeline")
            current_grammar_rule_names = []
            new_grammar_summaries = []
        else:
            print("🔍 处理语法规则：检查相似度...")
        
            current_grammar_rule_names = self.data_controller.grammar_manager.get_all_rules_name()
            print(f"📚 当前已有 {len(current_grammar_rule_names)} 个语法规则")
            print(f"📚 现有语法规则列表: {current_grammar_rule_names}")
            new_grammar_summaries = []
        
        for result in self.session_state.summarized_results:
            if isinstance(result, GrammarSummary):
                print(f"🔍 检查语法规则: {result.grammar_rule_name}")
                has_similar = False
                
                # 检查是否与现有语法相似
                for existing_rule in current_grammar_rule_names:
                    print(f"🔍 [DEBUG] 比较语法规则: '{existing_rule}' vs '{result.grammar_rule_name}'")
                    compare_result = self.compare_grammar_rule_assistant.run(
                        existing_rule,
                        result.grammar_rule_name,
                        verbose=False
                    )
                    print(f"🔍 [DEBUG] 相似度比较结果: {compare_result}")
                    
                    # 确保 compare_result 是字典类型
                    if isinstance(compare_result, str):
                        try:
                            compare_result = json.loads(compare_result)
                            print(f"🔍 [DEBUG] 解析JSON后的结果: {compare_result}")
                        except Exception as e:
                            print(f"❌ [DEBUG] JSON解析失败: {e}")
                            compare_result = {"is_similar": False}
                    elif isinstance(compare_result, list) and len(compare_result) > 0:
                        compare_result = compare_result[0] if isinstance(compare_result[0], dict) else {"is_similar": False}
                        print(f"🔍 [DEBUG] 取列表第一个元素: {compare_result}")
                    elif not isinstance(compare_result, dict):
                        print(f"❌ [DEBUG] 结果不是字典类型: {type(compare_result)}")
                        compare_result = {"is_similar": False}
                    
                    is_similar = compare_result.get("is_similar", False)
                    print(f"🔍 [DEBUG] 最终相似度判断: {is_similar}")
                    
                    if is_similar:
                        print(f"✅ 语法规则 '{result.grammar_rule_name}' 与现有规则 '{existing_rule}' 相似")
                        has_similar = True
                        existing_rule_id = self.data_controller.grammar_manager.get_id_by_rule_name(existing_rule)
                        
                        # 为现有语法规则添加新例句
                        current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else quoted_sentence
                        if current_sentence:
                            # 验证句子完整性
                            self._ensure_sentence_integrity(current_sentence, "现有语法 Example 调用")
                            print(f"🔍 [DEBUG] 调用grammar_example_explanation_assistant for '{existing_rule}'")
                            example_explanation = self.grammar_example_explanation_assistant.run(
                                sentence=current_sentence,
                                grammar=existing_rule
                            )
                            print(f"🔍 [DEBUG] example_explanation结果: {example_explanation}")
                            
                            try:
                                print(f"🔍 [DEBUG] 尝试添加现有语法的grammar_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, rule_id={existing_rule_id}")
                                print(f"🔍 [DEBUG] explanation_context: {example_explanation}")
                                
                                # 🔧 新增：为现有语法创建grammar notation（在add_grammar_example之前）
                                print(f"🔍 [DEBUG] ========== 开始为现有语法创建grammar notation ==========")
                                print(f"🔍 [DEBUG] 当前句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                                print(f"🔍 [DEBUG] 现有语法规则ID: {existing_rule_id}")
                                print(f"🔍 [DEBUG] 现有语法规则名称: {existing_rule}")
                                
                                # 获取 token_indices（从 session_state 中的 selected_token）
                                token_indices = self._get_token_indices_from_selection(current_sentence)
                                print(f"🔍 [DEBUG] 提取的token_indices: {token_indices}")
                                print(f"🔍 [DEBUG] token_indices类型: {type(token_indices)}")
                                print(f"🔍 [DEBUG] token_indices长度: {len(token_indices) if token_indices else 0}")
                                
                                # 使用unified_notation_manager创建grammar notation
                                from backend.data_managers.unified_notation_manager import get_unified_notation_manager
                                notation_manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
                                print(f"🔍 [DEBUG] notation_manager创建成功: {type(notation_manager)}")
                                
                                print(f"🔍 [DEBUG] 调用mark_notation参数:")
                                print(f"  - notation_type: grammar")
                                print(f"  - user_id: default_user")
                                print(f"  - text_id: {current_sentence.text_id}")
                                print(f"  - sentence_id: {current_sentence.sentence_id}")
                                print(f"  - grammar_id: {existing_rule_id}")
                                print(f"  - marked_token_ids: {token_indices}")
                                
                                success = notation_manager.mark_notation(
                                    notation_type="grammar",
                                    user_id="default_user",
                                    text_id=current_sentence.text_id,
                                    sentence_id=current_sentence.sentence_id,
                                    grammar_id=existing_rule_id,
                                    marked_token_ids=token_indices
                                )
                                
                                print(f"🔍 [DEBUG] mark_notation返回结果: {success}")
                                print(f"🔍 [DEBUG] 结果类型: {type(success)}")
                                
                                if success:
                                    print(f"✅ [DEBUG] 现有语法的grammar_notation创建成功")
                                    print(f"🔍 [DEBUG] ========== 现有语法grammar notation创建完成 ==========")
                                else:
                                    print(f"❌ [DEBUG] 现有语法的grammar_notation创建失败")
                                    print(f"🔍 [DEBUG] ========== 现有语法grammar notation创建失败 ==========")
                                
                                # 然后添加grammar example
                                self.data_controller.add_grammar_example(
                                    rule_id=existing_rule_id,
                                    text_id=current_sentence.text_id,
                                    sentence_id=current_sentence.sentence_id,
                                    explanation_context=example_explanation
                                )
                                print(f"✅ [DEBUG] 现有语法的grammar_example添加成功")
                                    
                            except ValueError as e:
                                print(f"⚠️ [DEBUG] 跳过添加现有语法的grammar_example，因为: {e}")
                            except Exception as e:
                                print(f"❌ [DEBUG] 添加现有语法的grammar_example时发生错误: {e}")
                        break
                
                # 如果没有相似的，添加为新语法
                if not has_similar:
                    print(f"🆕 新语法知识点：'{result.grammar_rule_name}'，将添加为新规则")
                    new_grammar_summaries.append(result)
        
        # 将新语法添加到 grammar_to_add
        if not DISABLE_GRAMMAR_FEATURES:
            for grammar in new_grammar_summaries:
                print(f"🆕 添加新语法: {grammar.grammar_rule_name}")
                self.session_state.add_grammar_to_add(
                    rule_name=grammar.grammar_rule_name,
                    rule_explanation=grammar.grammar_rule_summary
                )

        print("grammar to add：", self.session_state.grammar_to_add)
        #add to data
        
        # 调试信息：打印summarized_results的内容
        print("🔍 [DEBUG] summarized_results 内容:")
        for i, result in enumerate(self.session_state.summarized_results):
            print(f"  {i}: {type(result)} - {result}")
        
        current_vocab_list = self.data_controller.vocab_manager.get_all_vocab_body()
        print(f"🔍 [DEBUG] 当前词汇列表: {current_vocab_list}")
        
        new_vocab = []
        for result in self.session_state.summarized_results:
            print(f"🔍 [DEBUG] 处理结果: {type(result)} - {result}")
            print(f"🔍 [DEBUG] isinstance(result, VocabSummary): {isinstance(result, VocabSummary)}")
            print(f"🔍 [DEBUG] result.__class__.__name__: {result.__class__.__name__}")
            print(f"🔍 [DEBUG] VocabSummary.__name__: {VocabSummary.__name__}")
            has_similar = False
            
            # 使用更宽松的检查方式
            if hasattr(result, 'vocab') and result.__class__.__name__ == 'VocabSummary':
                print(f"🔍 [DEBUG] 找到VocabSummary: {result.vocab}")
                for vocab in current_vocab_list:
                    compare_result = self.fuzzy_match_expressions(vocab, result.vocab)
                    print(f"🔍 [DEBUG] 比较 '{vocab}' 与 '{result.vocab}': {compare_result}")
                    if compare_result:
                        print(f"✅ 词汇 '{vocab}' 与现有词汇 '{result.vocab}' 相似")
                        has_similar = True
                        existing_vocab_id = self.data_controller.vocab_manager.get_id_by_vocab_body(vocab)
                        current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else quoted_sentence
                        # 验证句子完整性
                        self._ensure_sentence_integrity(current_sentence, "Vocab Explanation 调用")
                        print(f"🔍 [DEBUG] 调用vocab_example_explanation_assistant for '{vocab}'")
                        example_explanation = self.vocab_example_explanation_assistant.run(
                            sentence=current_sentence,
                            vocab=vocab
                        )
                        print(f"🔍 [DEBUG] example_explanation结果: {example_explanation}")
                        
                        # 检查text_id是否存在，如果不存在则跳过添加example
                        try:
                            # 🔧 获取 token_indices（从 session_state 中的 selected_token）
                            token_indices = self._get_token_indices_from_selection(current_sentence)
                            print(f"🔍 [DEBUG] 尝试添加现有词汇的vocab_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, vocab_id={existing_vocab_id}, token_indices={token_indices}")
                            self.data_controller.add_vocab_example(
                                vocab_id=existing_vocab_id,
                                text_id=current_sentence.text_id,
                                sentence_id=current_sentence.sentence_id,
                                context_explanation=example_explanation,
                                token_indices=token_indices
                            )
                            print(f"✅ [DEBUG] 现有词汇的vocab_example添加成功")
                        except ValueError as e:
                            print(f"⚠️ [DEBUG] 跳过添加现有词汇的vocab_example，因为: {e}")
                            print(f"🔍 [DEBUG] 句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                        except Exception as e:
                            print(f"❌ [DEBUG] 添加现有词汇的vocab_example时发生错误: {e}")
                        break
                if not has_similar:
                    print(f"🆕 新词汇知识点：'{result.vocab}'，将添加到已有规则中")
                    new_vocab.append(result)
            else:
                print(f"🔍 [DEBUG] 跳过非VocabSummary结果: {type(result)}")
        
        print("新单词列表：", new_vocab) 
        for vocab in new_vocab:
            print(f"🔍 [DEBUG] 添加新词汇到vocab_to_add: {vocab.vocab}")
            self.session_state.add_vocab_to_add(vocab=vocab.vocab)
        
        print(f"🔍 [DEBUG] 最终vocab_to_add: {self.session_state.vocab_to_add}")

    def add_new_to_data(self):
        """
        将新语法和词汇添加到数据管理器中。
        """
        print(f"🔍 [DEBUG] ========== 开始执行 add_new_to_data ==========")
        print(f"🔍 [DEBUG] grammar_to_add 长度: {len(self.session_state.grammar_to_add) if self.session_state.grammar_to_add else 0}")
        print(f"🔍 [DEBUG] vocab_to_add 长度: {len(self.session_state.vocab_to_add) if self.session_state.vocab_to_add else 0}")
        
        if DISABLE_GRAMMAR_FEATURES:
            print("⏸️ [MainAssistant] Grammar add/new-example disabled — skip grammar_to_add processing")
        elif self.session_state.grammar_to_add:
            print(f"🔍 [DEBUG] 处理grammar_to_add: {len(self.session_state.grammar_to_add)} 个语法规则")
            for grammar in self.session_state.grammar_to_add:
                print(f"🔍 [DEBUG] 处理新语法: {grammar.rule_name}")
                
                # 添加新语法规则
                self.data_controller.add_new_grammar_rule(
                    rule_name=grammar.rule_name,
                    rule_explanation=grammar.rule_explanation
                )
                print(f"✅ [DEBUG] 新语法规则已添加")
                
                # 为这个语法规则生成例句
                current_sentence = self.session_state.current_sentence
                if current_sentence:
                    # 验证句子完整性
                    self._ensure_sentence_integrity(current_sentence, "新语法 Explanation 调用")
                    print(f"🔍 [DEBUG] 调用grammar_example_explanation_assistant for '{grammar.rule_name}'")
                    example_explanation = self.grammar_example_explanation_assistant.run(
                        sentence=current_sentence,
                        grammar=grammar.rule_name
                    )
                    print(f"🔍 [DEBUG] grammar_example_explanation结果: {example_explanation}")
                    
                    # 添加语法例句
                    try:
                        grammar_rule_id = self.data_controller.grammar_manager.get_id_by_rule_name(grammar.rule_name)
                        print(f"🔍 [DEBUG] 尝试添加grammar_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, rule_id={grammar_rule_id}")
                        self.data_controller.add_grammar_example(
                            rule_id=grammar_rule_id,
                            text_id=current_sentence.text_id,
                            sentence_id=current_sentence.sentence_id,
                            explanation_context=example_explanation
                        )
                        print(f"✅ [DEBUG] grammar_example添加成功")
                        
                        # 🔧 新增：创建grammar notation
                        try:
                            print(f"🔍 [DEBUG] ========== 开始创建新语法的grammar notation ==========")
                            print(f"🔍 [DEBUG] 当前句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                            print(f"🔍 [DEBUG] 语法规则ID: {grammar_rule_id}")
                            print(f"🔍 [DEBUG] 语法规则名称: {grammar.rule_name}")
                            
                            # 获取 token_indices（从 session_state 中的 selected_token）
                            token_indices = self._get_token_indices_from_selection(current_sentence)
                            print(f"🔍 [DEBUG] 提取的token_indices: {token_indices}")
                            print(f"🔍 [DEBUG] token_indices类型: {type(token_indices)}")
                            print(f"🔍 [DEBUG] token_indices长度: {len(token_indices) if token_indices else 0}")
                            
                            # 使用unified_notation_manager创建grammar notation
                            from backend.data_managers.unified_notation_manager import get_unified_notation_manager
                            notation_manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=True)
                            print(f"🔍 [DEBUG] notation_manager创建成功: {type(notation_manager)}")
                            
                            print(f"🔍 [DEBUG] 调用mark_notation参数:")
                            print(f"  - notation_type: grammar")
                            print(f"  - user_id: default_user")
                            print(f"  - text_id: {current_sentence.text_id}")
                            print(f"  - sentence_id: {current_sentence.sentence_id}")
                            print(f"  - grammar_id: {grammar_rule_id}")
                            print(f"  - marked_token_ids: {token_indices}")
                            
                            success = notation_manager.mark_notation(
                                notation_type="grammar",
                                user_id="default_user",
                                text_id=current_sentence.text_id,
                                sentence_id=current_sentence.sentence_id,
                                grammar_id=grammar_rule_id,
                                marked_token_ids=token_indices
                            )
                            
                            print(f"🔍 [DEBUG] mark_notation返回结果: {success}")
                            print(f"🔍 [DEBUG] 结果类型: {type(success)}")
                            
                            if success:
                                print(f"✅ [DEBUG] grammar_notation创建成功")
                                print(f"🔍 [DEBUG] ========== 新语法grammar notation创建完成 ==========")
                            else:
                                print(f"❌ [DEBUG] grammar_notation创建失败")
                                print(f"🔍 [DEBUG] ========== 新语法grammar notation创建失败 ==========")
                        except Exception as notation_error:
                            print(f"❌ [DEBUG] 创建grammar_notation时发生错误: {notation_error}")
                            print(f"❌ [DEBUG] 错误类型: {type(notation_error)}")
                            import traceback
                            print(f"❌ [DEBUG] 错误堆栈: {traceback.format_exc()}")
                            print(f"🔍 [DEBUG] ========== 新语法grammar notation创建异常 ==========")
                            
                    except ValueError as e:
                        print(f"⚠️ [DEBUG] 跳过添加grammar_example，因为: {e}")
                        print(f"🔍 [DEBUG] 句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                    except Exception as e:
                        print(f"❌ [DEBUG] 添加grammar_example时发生错误: {e}")
        else:
            print("🔍 [DEBUG] grammar_to_add为空，跳过新语法处理")

        if self.session_state.vocab_to_add:
            print(f"🔍 [DEBUG] 处理vocab_to_add: {len(self.session_state.vocab_to_add)} 个词汇")
            for vocab in self.session_state.vocab_to_add:
                print(f"🔍 [DEBUG] 处理新词汇: {vocab.vocab}")
                # 生成词汇解释
                current_sentence = self.session_state.current_sentence
                if current_sentence:
                    # 验证句子完整性
                    self._ensure_sentence_integrity(current_sentence, "新词汇 Explanation 调用")
                    print(f"🔍 [DEBUG] 调用vocab_explanation_assistant for '{vocab.vocab}'")
                    vocab_explanation = self.vocab_explanation_assistant.run(
                        sentence=current_sentence,
                        vocab=vocab.vocab
                    )
                    print(f"🔍 [DEBUG] vocab_explanation结果: {vocab_explanation}")
                    # 解析JSON响应
                    if isinstance(vocab_explanation, str):
                        try:
                            import json
                            explanation_data = json.loads(vocab_explanation)
                            explanation_text = explanation_data.get("explanation", "No explanation provided")
                        except:
                            explanation_text = vocab_explanation
                    else:
                        explanation_text = str(vocab_explanation)
                else:
                    explanation_text = "No explanation provided"
                
                print(f"🔍 [DEBUG] 添加新词汇到数据库: {vocab.vocab}")
                # 添加新词汇
                self.data_controller.add_new_vocab(vocab_body=vocab.vocab, explanation=explanation_text)
                
                # 生成词汇例句解释
                if current_sentence:
                    print(f"🔍 [DEBUG] 调用vocab_example_explanation_assistant for '{vocab.vocab}'")
                    example_explanation = self.vocab_example_explanation_assistant.run(
                        sentence=current_sentence,
                        vocab=vocab.vocab
                    )
                    print(f"🔍 [DEBUG] example_explanation结果: {example_explanation}")
                    
                    # 检查text_id是否存在，如果不存在则跳过添加example
                    try:
                        vocab_id = self.data_controller.vocab_manager.get_id_by_vocab_body(vocab.vocab)
                        # 🔧 获取 token_indices（从 session_state 中的 selected_token）
                        token_indices = self._get_token_indices_from_selection(current_sentence)
                        print(f"🔍 [DEBUG] 尝试添加vocab_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, vocab_id={vocab_id}, token_indices={token_indices}")
                        self.data_controller.add_vocab_example(
                            vocab_id=vocab_id,
                            text_id=current_sentence.text_id,
                            sentence_id=current_sentence.sentence_id,
                            context_explanation=example_explanation,
                            token_indices=token_indices
                        )
                        print(f"✅ [DEBUG] vocab_example添加成功")
                    except ValueError as e:
                        print(f"⚠️ [DEBUG] 跳过添加vocab_example，因为: {e}")
                        print(f"🔍 [DEBUG] 句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                    except Exception as e:
                        print(f"❌ [DEBUG] 添加vocab_example时发生错误: {e}")
        else:
            print("🔍 [DEBUG] vocab_to_add为空，跳过新词汇处理")

    def _get_token_indices_from_selection(self, sentence: SentenceType) -> list:
        """
        从 session_state 中的 selected_token 提取 sentence_token_id 列表
        
        Args:
            sentence: 当前句子对象
            
        Returns:
            list[int]: sentence_token_id 列表（如 [3, 4, 5]）
        """
        print(f"🔍 [TokenIndices] ========== 开始提取token_indices ==========")
        token_indices = []
        
        # 从 session_state 获取选中的 token
        selected_token = self.session_state.current_selected_token
        print(f"🔍 [TokenIndices] selected_token存在: {selected_token is not None}")
        if not selected_token:
            print("⚠️ [TokenIndices] 没有选中的 token，返回空列表")
            return []

        print(f"🔍 [TokenIndices] selected_token类型: {type(selected_token)}")
        print(f"🔍 [TokenIndices] selected_token属性: {dir(selected_token)}")
        if hasattr(selected_token, 'token_text'):
            print(f"🔍 [TokenIndices] selected_token.token_text: '{selected_token.token_text}'")
        if hasattr(selected_token, 'token_indices'):
            print(f"🔍 [TokenIndices] selected_token.token_indices: {selected_token.token_indices}")

        # 1) 优先使用 session 中已存在的 token_indices（来自前端/MockServer），且不是整句 [-1]
        if hasattr(selected_token, 'token_indices') and isinstance(selected_token.token_indices, list):
            print(f"🔍 [TokenIndices] 发现token_indices属性: {selected_token.token_indices}")
            incoming_indices = [int(i) for i in selected_token.token_indices if isinstance(i, (int, float, str)) and str(i).lstrip('-').isdigit()]
            print(f"🔍 [TokenIndices] 处理后的incoming_indices: {incoming_indices}")
            if incoming_indices and not (len(incoming_indices) == 1 and incoming_indices[0] == -1):
                print(f"✅ [TokenIndices] 使用 session_state.token_indices: {incoming_indices}")
                print(f"🔍 [TokenIndices] ========== 使用session token_indices完成 ==========")
                return incoming_indices
            else:
                print(f"🔍 [TokenIndices] incoming_indices为空或为整句标记[-1]，继续查找")
        
        # 检查句子是否有 tokens 列表（新数据结构）
        print(f"🔍 [TokenIndices] 句子有tokens属性: {hasattr(sentence, 'tokens')}")
        if hasattr(sentence, 'tokens'):
            print(f"🔍 [TokenIndices] sentence.tokens存在: {sentence.tokens is not None}")
            print(f"🔍 [TokenIndices] sentence.tokens长度: {len(sentence.tokens) if sentence.tokens else 0}")
        
        if not hasattr(sentence, 'tokens') or not sentence.tokens:
            print("⚠️ [TokenIndices] 句子没有 tokens 列表，返回空列表")
            print(f"🔍 [TokenIndices] ========== 句子无tokens完成 ==========")
            return []
        
        # 获取选中的文本
        selected_text = selected_token.token_text
        print(f"🔍 [TokenIndices] 查找选中文本: '{selected_text}'")
        
        # 辅助函数：去除标点符号
        import string
        def strip_punctuation(text: str) -> str:
            return text.strip(string.punctuation + '。，！？；：""''（）【】《》、')
        
        selected_clean = strip_punctuation(selected_text)
        print(f"🔍 [TokenIndices] 清理后的选中文本: '{selected_clean}'")
        
        # 2) 回退：根据选中文本在句子的 tokens 中查找匹配的 token
        print(f"🔍 [TokenIndices] 开始遍历句子tokens:")
        for i, token in enumerate(sentence.tokens):
            print(f"  Token {i}: {token}")
            if hasattr(token, 'token_type'):
                print(f"    - token_type: {token.token_type}")
            if hasattr(token, 'token_body'):
                print(f"    - token_body: '{token.token_body}'")
            if hasattr(token, 'sentence_token_id'):
                print(f"    - sentence_token_id: {token.sentence_token_id}")
                
            if token.token_type == 'text':  # 只考虑文本 token
                token_clean = strip_punctuation(token.token_body)
                print(f"    - 清理后的token_body: '{token_clean}'")
                print(f"    - 比较: '{token_clean.lower()}' == '{selected_clean.lower()}' ? {token_clean.lower() == selected_clean.lower()}")
                if token_clean.lower() == selected_clean.lower():
                    if token.sentence_token_id is not None:
                        token_indices.append(token.sentence_token_id)
                        print(f"  ✅ 找到匹配 token: '{token.token_body}' → sentence_token_id={token.sentence_token_id}")
                    else:
                        print(f"  ⚠️ 找到匹配token但sentence_token_id为None: '{token.token_body}'")
                else:
                    print(f"  ❌ 不匹配: '{token.token_body}'")
        
        if not token_indices:
            print(f"⚠️ [TokenIndices] 未找到匹配的 token，返回空列表")
        else:
            print(f"✅ [TokenIndices] 提取到 token_indices: {token_indices}")
        
        print(f"🔍 [TokenIndices] ========== token_indices提取完成 ==========")
        return token_indices
    
    def _log_sentence_capabilities(self, sentence: SentenceType):
        """只读：打印句子层能力（tokens/难度等），不影响任何分支"""
        try:
            if sentence in self._capabilities_cache:
                caps = self._capabilities_cache[sentence]
            else:
                caps = CapabilityDetector.detect_sentence_capabilities(sentence)
                self._capabilities_cache[sentence] = caps
            print(f"🔍 Sentence capabilities: has_tokens={caps.get('has_tokens')}, token_count={caps.get('token_count')}, has_difficulty_level={caps.get('has_difficulty_level')}")
            # 若具备 tokens，演示性打印前若干 token 文本（不参与逻辑）
            if caps.get('has_tokens'):
                tokens = DataAdapter.get_tokens(sentence) or []
                preview = ", ".join([getattr(t, 'token_body', str(t)) for t in tokens[:10]])
                print(f"   ⤷ tokens preview: {preview}")
        except Exception as e:
            print(f"[Warn] capability logging failed: {e}")

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
        grammar_annotations=(),
        vocab_annotations=()
    )
    
    main_assistant = MainAssistant()
    user_input = "in which是什么语法知识点？为什么用are而不是is？请总结出两个知识点" 
    main_assistant.run(test_sentence, user_input)

    #add sentence to example logic
    