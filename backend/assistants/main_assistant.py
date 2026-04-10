import os
import json
import inspect
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
from backend.assistants.sub_assistants.grammar_explanation import GrammarExplanationAssistant
from backend.assistants.sub_assistants.vocab_example_explanation import VocabExampleExplanationAssistant
from backend.assistants.sub_assistants.vocab_explanation import VocabExplanationAssistant
from backend.data_managers.data_classes import Sentence
# 导入新数据结构类
try:
    from backend.data_managers.data_classes_new import Sentence as NewSentence, Token, WordToken
    NEW_STRUCTURE_AVAILABLE = True
except ImportError:
    NEW_STRUCTURE_AVAILABLE = False
    print("⚠️ 新数据结构类不可用，将使用旧结构")
from backend.data_managers import data_controller
from backend.data_managers.dialogue_record import DialogueRecordBySentence
# 只读能力探测适配层（不改变业务逻辑）
from backend.assistants.adapters import CapabilityDetector, DataAdapter, GrammarRuleAdapter, VocabAdapter
from backend.preprocessing.language_classification import (
    get_language_code,
    is_non_whitespace_language
)

MAX_KNOWLEDGE_ITEMS_PER_CHAT = 3

# 定义联合类型，支持新旧两种 Sentence 类型
from typing import Union, Optional, Tuple
SentenceType = Union[Sentence, NewSentence] if NEW_STRUCTURE_AVAILABLE else Sentence

# 全局开关：临时关闭语法相关能力（对比/生成规则与例句）
DISABLE_GRAMMAR_FEATURES = True


def _preview_for_log(value, max_len: int = 240) -> str:
    """Avoid dumping full model outputs / summaries into server logs."""
    if value is None:
        return ""
    s = str(value)
    if len(s) <= max_len:
        return s
    return f"{s[:max_len]}…(truncated len={len(s)})"


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
        self.grammar_explanation_assistant = GrammarExplanationAssistant()
        self.vocab_example_explanation_assistant = VocabExampleExplanationAssistant()
        self.vocab_explanation_assistant = VocabExplanationAssistant()
        self.data_controller = data_controller_instance if data_controller_instance else data_controller.DataController(max_turns)
        # 使用 data_controller 的实例而不是创建新的
        self.dialogue_record = self.data_controller.dialogue_record
        self.dialogue_history = self.data_controller.dialogue_history
        
        # 只读：能力探测缓存（不用于业务分支，仅打印）
        self._capabilities_cache = {}
        
        # 当前处理的句子语言信息（在 run() 方法中设置）
        self.current_language: Optional[str] = None
        self.current_language_code: Optional[str] = None
        self.current_is_non_whitespace: bool = False
        
        # 🔧 UI 语言（用于控制 AI 输出语言，如"中文"、"英文"）
        self.ui_language: Optional[str] = None
        self.processed_articles_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "current", "articles")
        )
        
        # 🔧 Token 记录相关：user_id 和 session（用于在 API 调用后记录 token 使用）
        self._user_id: Optional[int] = None
        self._db_session = None
    
    def set_user_context(self, user_id: Optional[int] = None, session=None):
        """
        设置用户上下文（用于 token 记录和扣减）
        
        Args:
            user_id: 用户 ID
            session: 数据库会话
        """
        self._user_id = user_id
        self._db_session = session

    def _ma_log(self, msg: str) -> None:
        """Prefix assistant logs with user_id (matches /api/chat server logs during beta)."""
        uid = self._user_id
        print(f"[user_id={uid}] [MainAssistant] {msg}")

    def _detect_sentence_language(self, sentence: SentenceType) -> Tuple[Optional[str], Optional[str], bool]:
        """
        检测句子的语言信息
        
        Args:
            sentence: 句子对象（支持新旧两种类型）
            
        Returns:
            Tuple[language, language_code, is_non_whitespace]:
                - language: 语言名称（如 "中文", "英文"），如果无法获取则为 None
                - language_code: 语言代码（如 "zh", "en"），如果无法获取则为 None
                - is_non_whitespace: 是否为非空格语言（True/False），如果无法判断则默认为 False
        """
        # 方法0: 如果 session_state 中已经存储了语言信息，直接使用
        if hasattr(self.session_state, 'current_language_code'):
            stored_language_code = getattr(self.session_state, 'current_language_code', None)
            stored_language = getattr(self.session_state, 'current_language', None)
            stored_is_non_whitespace = getattr(self.session_state, 'current_is_non_whitespace', None)
            if stored_language_code:
                if stored_is_non_whitespace is None:
                    stored_is_non_whitespace = is_non_whitespace_language(stored_language_code)
                return stored_language, stored_language_code, bool(stored_is_non_whitespace)

        # 方法1: 检查 NewSentence 是否有 word_tokens（最直接的方式）
        if NEW_STRUCTURE_AVAILABLE and isinstance(sentence, NewSentence):
            if sentence.word_tokens is not None and len(sentence.word_tokens) > 0:
                # 有 word_tokens 说明是非空格语言
                # 尝试从关联的 OriginalText 获取具体语言信息
                language, language_code = self._get_language_from_text(sentence.text_id)
                if language_code:
                    is_non_whitespace = is_non_whitespace_language(language_code)
                    return language, language_code, is_non_whitespace
                else:
                    # 无法获取具体语言，但根据 word_tokens 存在可以判断为非空格语言
                    return None, None, True
        
        # 方法2: 从关联的 OriginalText 获取语言信息
        language, language_code = self._get_language_from_text(sentence.text_id)
        if language_code:
            is_non_whitespace = is_non_whitespace_language(language_code)
            return language, language_code, is_non_whitespace
        
        # 方法3: 根据句子内容进行简单推断（例如检测中文字符）
        sentence_body = getattr(sentence, 'sentence_body', '')
        if sentence_body:
            try:
                import re
                if re.search(r'[\u4e00-\u9fff]', sentence_body):
                    return "中文", "zh", True
            except Exception as e:
                print(f"⚠️ [MainAssistant] 基于句子内容推断语言失败: {e}")
        
        # 方法4: 无法判断，返回默认值（假设为空格语言）
        return None, None, False
    
    def _get_language_from_text(self, text_id: int) -> Tuple[Optional[str], Optional[str]]:
        """
        从 text_id 获取语言信息
        
        Args:
            text_id: 文章ID
            
        Returns:
            Tuple[language, language_code]: 语言名称和语言代码，如果无法获取则为 (None, None)
        """
        try:
            # 尝试从 data_controller 获取 OriginalText
            if hasattr(self.data_controller, 'text_manager'):
                text_manager = self.data_controller.text_manager
                # 尝试调用 get_text_by_id 获取文章信息
                if hasattr(text_manager, 'get_text_by_id'):
                    get_text_fn = text_manager.get_text_by_id
                    text_dto = None
                    try:
                        signature = inspect.signature(get_text_fn)
                        if 'include_sentences' in signature.parameters:
                            text_dto = get_text_fn(text_id, include_sentences=False)
                        else:
                            text_dto = get_text_fn(text_id)
                    except (ValueError, TypeError):
                        # 签名获取失败或不支持参数信息，回退到无关键字调用
                        text_dto = get_text_fn(text_id)
                    if text_dto and hasattr(text_dto, 'language') and text_dto.language:
                        language = text_dto.language
                        language_code = get_language_code(language)
                        return language, language_code
        except Exception as e:
            print(f"⚠️ [MainAssistant] 获取语言信息失败: {e}")
        
        return None, None

    def _clean_vocab_for_matching(self, vocab: str) -> str:
        """
        清理词汇用于匹配（去除标点、空格、转小写）
        
        Args:
            vocab: 原始词汇字符串
            
        Returns:
            str: 清理后的词汇字符串
        """
        import string
        # 去除中英文标点
        punctuation = string.punctuation + '。，！？；：""''（）【】《》、'
        cleaned = vocab.strip().lower()
        for p in punctuation:
            cleaned = cleaned.replace(p, '')
        return cleaned.strip()

    def _load_sentence_from_processed_files(self, text_id: int, sentence_id: int) -> Optional['NewSentence']:
        try:
            sentences_path = os.path.join(self.processed_articles_dir, f"text_{text_id}", "sentences.json")
            if not os.path.exists(sentences_path):
                return None
            with open(sentences_path, "r", encoding="utf-8") as f:
                sentences_data = json.load(f)
            for entry in sentences_data:
                if entry.get("sentence_id") == sentence_id:
                    tokens_data = entry.get("tokens") or []
                    word_tokens_data = entry.get("word_tokens") or []
                    tokens = tuple([
                        Token(
                            token_body=token.get("token_body", ""),
                            token_type=token.get("token_type", "text"),
                            difficulty_level=token.get("difficulty_level"),
                            global_token_id=token.get("global_token_id"),
                            sentence_token_id=token.get("sentence_token_id"),
                            pos_tag=token.get("pos_tag"),
                            lemma=token.get("lemma"),
                            is_grammar_marker=token.get("is_grammar_marker", False),
                            linked_vocab_id=token.get("linked_vocab_id"),
                            word_token_id=token.get("word_token_id"),
                        )
                        for token in tokens_data
                    ])
                    word_tokens = tuple([
                        WordToken(
                            word_token_id=wt.get("word_token_id"),
                            token_ids=tuple(wt.get("token_ids") or []),
                            word_body=wt.get("word_body", ""),
                            pos_tag=wt.get("pos_tag"),
                            lemma=wt.get("lemma"),
                            linked_vocab_id=wt.get("linked_vocab_id"),
                        )
                        for wt in word_tokens_data
                    ])
                    return NewSentence(
                        text_id=text_id,
                        sentence_id=sentence_id,
                        sentence_body=entry.get("sentence_body", ""),
                        grammar_annotations=tuple(entry.get("grammar_annotations") or []),
                        vocab_annotations=tuple(entry.get("vocab_annotations") or []),
                        sentence_difficulty_level=entry.get("sentence_difficulty_level"),
                        tokens=tokens,
                        word_tokens=word_tokens if word_tokens else None,
                    )
        except Exception as e:
            print(f"⚠️ [MainAssistant] 无法从文件加载句子(word_tokens): {e}")
        return None

    def _ensure_sentence_has_word_tokens(self, sentence: SentenceType) -> SentenceType:
        has_word_tokens = getattr(sentence, "word_tokens", None)
        has_tokens = getattr(sentence, "tokens", None)
        text_id = getattr(sentence, "text_id", None)
        sentence_id = getattr(sentence, "sentence_id", None)
        if has_word_tokens and has_tokens:
            return sentence
        if text_id is None or sentence_id is None or not NEW_STRUCTURE_AVAILABLE:
            return sentence
        enriched = self._load_sentence_from_processed_files(text_id, sentence_id)
        if not enriched:
            return sentence
        if isinstance(sentence, NewSentence):
            return NewSentence(
                text_id=sentence.text_id,
                sentence_id=sentence.sentence_id,
                sentence_body=sentence.sentence_body,
                grammar_annotations=sentence.grammar_annotations,
                vocab_annotations=sentence.vocab_annotations,
                sentence_difficulty_level=sentence.sentence_difficulty_level,
                tokens=enriched.tokens if not has_tokens else sentence.tokens,
                word_tokens=enriched.word_tokens if not has_word_tokens else sentence.word_tokens,
            )
        return enriched

    def _match_vocab_to_word_token(self, vocab: str, sentence: SentenceType) -> Optional[int]:
        """
        尝试将 vocab 匹配到句子的 word token（仅用于非空格语言）
        
        Args:
            vocab: 总结出的词汇
            sentence: 句子对象
            
        Returns:
            word_token_id: 如果匹配成功，返回 word_token_id；否则返回 None
        """
        sentence = self._ensure_sentence_has_word_tokens(sentence)
        # 1. 检查是否为非空格语言
        if not self.current_is_non_whitespace:
            return None
        
        # 2. 检查句子是否有 word_tokens
        if not NEW_STRUCTURE_AVAILABLE or not isinstance(sentence, NewSentence):
            return None
        
        if not sentence.word_tokens or len(sentence.word_tokens) == 0:
            return None
        
        # 3. 清理 vocab（去除标点、空格、转小写）
        vocab_clean = self._clean_vocab_for_matching(vocab)
        if not vocab_clean:
            return None
        
        # 4. 尝试匹配 word tokens
        for word_token in sentence.word_tokens:
            if not hasattr(word_token, 'word_body') or not hasattr(word_token, 'word_token_id'):
                continue
            
            word_body_clean = self._clean_vocab_for_matching(word_token.word_body)
            if not word_body_clean:
                continue
            
            # 精确匹配
            if vocab_clean == word_body_clean:
                print(f"✅ [WordToken匹配] vocab '{vocab}' 精确匹配到 word_token '{word_token.word_body}' (word_token_id={word_token.word_token_id})")
                return word_token.word_token_id
            
            # 部分匹配：如果 vocab 是单个字符，检查是否属于 word token
            if len(vocab_clean) == 1 and vocab_clean in word_body_clean:
                print(f"✅ [WordToken匹配] vocab '{vocab}' 部分匹配到 word_token '{word_token.word_body}' (word_token_id={word_token.word_token_id})")
                return word_token.word_token_id
        
        print(f"⚠️ [WordToken匹配] vocab '{vocab}' 未匹配到任何 word_token，将回退到字符 token 匹配")
        return None

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
        
        # 🌐 检测句子语言信息（用于后续非空格语言的特殊处理）
        language, language_code, is_non_whitespace = self._detect_sentence_language(quoted_sentence)
        # 存储语言信息供后续使用
        self.current_language = language
        self.current_language_code = language_code
        self.current_is_non_whitespace = is_non_whitespace
        
        # 总是打印语言检测结果（用于调试）
        if language_code:
            print(f"🌐 [MainAssistant] 检测到语言: {language} (代码: {language_code}, 非空格语言: {is_non_whitespace})")
        else:
            print(f"🌐 [MainAssistant] 无法检测语言，使用默认处理（假设为空格语言，is_non_whitespace={is_non_whitespace}）")
        
        # 额外调试：检查句子是否有 word_tokens
        if NEW_STRUCTURE_AVAILABLE and isinstance(quoted_sentence, NewSentence):
            has_word_tokens = quoted_sentence.word_tokens is not None and len(quoted_sentence.word_tokens) > 0
            print(f"🔍 [MainAssistant] 句子是否有 word_tokens: {has_word_tokens} (text_id={quoted_sentence.text_id})")
        
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
        # 🔧 获取 user_id 用于数据库保存（实现跨设备同步）
        user_id = str(self.session_state.user_id) if hasattr(self.session_state, 'user_id') and self.session_state.user_id else None
        current_selected_token = self.session_state.current_selected_token
        if current_selected_token:
            self.dialogue_record.add_user_message(quoted_sentence, user_question, current_selected_token, user_id=user_id)
        else:
            # 兜底：如果 session_state 中没有，创建一个整句选择的 token
            fallback_token = SelectedToken.from_full_sentence(quoted_sentence)
            self.dialogue_record.add_user_message(quoted_sentence, user_question, fallback_token, user_id=user_id)
        
        print("The question is relevant to language learning, proceeding with processing...")
        
        # 回答问题（会在内部设置 current_response）
        ai_response = self.answer_question_function(quoted_sentence, user_question, effective_sentence_body)
        
        # 记录AI响应（包含selected_token信息）
        self.dialogue_record.add_ai_response(quoted_sentence, ai_response, user_id=user_id)
        
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
        _names = self.data_controller.grammar_manager.get_all_rules_name()
        _vocabs = self.data_controller.vocab_manager.get_all_vocab_body()
        print(f"📚 Grammar Rules count={len(_names)} sample={_preview_for_log(_names[:15], 200)}")
        print(f"📖 Vocab List count={len(_vocabs)} sample={_preview_for_log(_vocabs[:20], 200)}")
        
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
            self._ma_log(f"🎯 [AnswerQuestion] 用户选择了特定文本: '{_preview_for_log(quoted_part, 120)}'")
            self._ma_log(f"📖 [AnswerQuestion] 完整句子: '{_preview_for_log(full_sentence, 160)}'")
            ai_response = self.answer_question_assistant.run(
                full_sentence=full_sentence,
                user_question=user_question,
                quoted_part=quoted_part,
                ui_language=self.ui_language,
                user_id=self._user_id,
                session=self._db_session
            )
        else:
            # 用户选择了整句话
            self._ma_log(f"📖 [AnswerQuestion] 用户选择了整句话: '{_preview_for_log(full_sentence, 160)}'")
            ai_response = self.answer_question_assistant.run(
                full_sentence=full_sentence,
                user_question=user_question,
                ui_language=self.ui_language,
                user_id=self._user_id,
                session=self._db_session
            )
        
        self._ma_log(
            f"AI Response len={len(str(ai_response)) if ai_response is not None else 0} "
            f"type={type(ai_response)}: {_preview_for_log(ai_response, 320)}"
        )
        
        # 🔧 处理 JSON 解析结果
        if isinstance(ai_response, dict):
            # 如果返回的是字典，尝试提取 answer 字段
            if "answer" in ai_response:
                ai_response = ai_response["answer"]
                self._ma_log("✅ 从字典中提取 answer 字段: " + (str(ai_response)[:100] if len(str(ai_response)) > 100 else str(ai_response)))
            else:
                # 如果没有 answer 字段，将整个字典转换为字符串（向后兼容）
                self._ma_log("⚠️ 字典中没有 answer 字段，转换为字符串")
                ai_response = str(ai_response)
        elif isinstance(ai_response, list):
            # 如果是列表，转换为字符串（向后兼容）
            self._ma_log("⚠️ 返回的是列表，转换为字符串")
            ai_response = str(ai_response)
        elif ai_response is None:
            # 解析失败（这种情况应该不会发生，因为 SubAssistant.run() 现在返回原始文本）
            self._ma_log("❌ AI 响应为 None，使用错误提示")
            ai_response = "抱歉，AI响应解析失败，请重试。"
        # 如果已经是字符串，直接使用
        
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
        self._ma_log("handle_grammar_vocab_function 开始")
        # 🌐 确保语言信息已检测（如果还没有检测，则现在检测）
        # 这很重要，因为 handle_grammar_vocab_function 可能被直接调用，绕过了 run() 方法
        if self.current_language_code is None:
            self._ma_log("🔍 [DEBUG] [handle_grammar_vocab_function] 语言信息未设置，执行语言检测...")
            language, language_code, is_non_whitespace = self._detect_sentence_language(quoted_sentence)
            self.current_language = language
            self.current_language_code = language_code
            self.current_is_non_whitespace = is_non_whitespace
            if language_code:
                self._ma_log(f"🌐 [handle_grammar_vocab_function] 检测到语言: {language} (代码: {language_code}, 非空格语言: {is_non_whitespace})")
            else:
                self._ma_log(f"🌐 [handle_grammar_vocab_function] 无法检测语言，使用默认处理（假设为空格语言，is_non_whitespace={is_non_whitespace}）")
        else:
            self._ma_log(f"🌐 [handle_grammar_vocab_function] 使用已检测的语言信息: {self.current_language} (代码: {self.current_language_code}, 非空格语言: {self.current_is_non_whitespace})")
        
        # 🔧 保存 selected_token 的引用（避免在后续处理中被清空）
        saved_selected_token = self.session_state.current_selected_token
        self._ma_log(f"🔍 [DEBUG] [handle_grammar_vocab_function] 保存 selected_token 引用: {saved_selected_token is not None}")
        if saved_selected_token:
            self._ma_log(f"🔍 [DEBUG] [handle_grammar_vocab_function] selected_token.token_text: '{getattr(saved_selected_token, 'token_text', None)}'")
            self._ma_log(f"🔍 [DEBUG] [handle_grammar_vocab_function] selected_token.token_indices: {getattr(saved_selected_token, 'token_indices', None)}")
        
        # 如果没有提供effective_sentence_body，使用完整句子
        if effective_sentence_body is None:
            effective_sentence_body = quoted_sentence.sentence_body
            
        # 检查是否与语法相关
        if DISABLE_GRAMMAR_FEATURES:
            self._ma_log("⏸️ Grammar features are DISABLED (skip relevance/summarize/compare/generation)")
            grammar_relevant_response = {"is_grammar_relevant": False}
        else:
            grammar_relevant_response = self.check_if_grammar_relavent_assistant.run(
                effective_sentence_body, user_question, ai_response,
                user_id=self._user_id, session=self._db_session
            )
        vocab_relevant_response = self.check_if_vocab_relevant_assistant.run(
            effective_sentence_body, user_question, ai_response,
            user_id=self._user_id, session=self._db_session
        )
        
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
            
            # 🔧 使用 UI 语言而不是文章语言
            output_language = self.ui_language or self.session_state.current_language or "中文"
            grammar_summary = self.summarize_grammar_rule_assistant.run(
                sentence_body,
                user_input,
                ai_response_str,
                language=output_language,
                user_id=self._user_id, session=self._db_session
            )
            print(f"✅ [DEBUG] summarize_grammar_rule 输出: {_preview_for_log(grammar_summary, 400)}")
            
            # 处理新的格式：display_name + canonical
            def process_new_format_grammar(grammar_dict: dict):
                """处理新格式的语法规则（display_name + canonical）"""
                display_name = grammar_dict.get("display_name")
                canonical = grammar_dict.get("canonical", {})
                canonical_category = canonical.get("category")
                canonical_subtype = canonical.get("subtype")
                canonical_function = canonical.get("function")
                
                # 验证必要字段
                if not display_name or not canonical_category or not canonical_subtype:
                    print(f"⚠️ [DEBUG] 新格式语法规则缺少必要字段: display_name={display_name}, category={canonical_category}, subtype={canonical_subtype}")
                    return False
                
                print(f"✅ [DEBUG] 检测到新格式语法规则: display_name={display_name}, category={canonical_category}, subtype={canonical_subtype}")
                
                # 🔧 1. 先生成 canonical_key（用于查重）
                # 🔧 获取文章的实际语言（从数据库），而不是 session_state.current_language（可能是 UI 语言）
                from backend.data_managers.canonical_key_generator import generate_canonical_key
                article_language = None
                current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else sentence_body
                user_id = getattr(self.session_state, 'user_id', None) or self._user_id
                
                if current_sentence and hasattr(current_sentence, 'text_id') and user_id:
                    try:
                        from database_system.database_manager import DatabaseManager
                        from database_system.business_logic.models import OriginalText
                        db_manager = DatabaseManager('development')
                        session = db_manager.get_session()
                        try:
                            text_model = session.query(OriginalText).filter(
                                OriginalText.text_id == current_sentence.text_id,
                                OriginalText.user_id == user_id
                            ).first()
                            if text_model:
                                article_language = text_model.language
                                print(f"🔍 [DEBUG] 从数据库获取文章language用于生成canonical_key: {article_language} (text_id={current_sentence.text_id})")
                            else:
                                print(f"⚠️ [DEBUG] 文章不存在，无法获取language: text_id={current_sentence.text_id}, user_id={user_id}")
                        finally:
                            session.close()
                    except Exception as e:
                        print(f"⚠️ [DEBUG] 获取文章language失败: {e}")
                
                # 如果无法从数据库获取，使用默认值
                if not article_language:
                    article_language = "中文"
                    print(f"⚠️ [DEBUG] 无法获取文章language，使用默认值: {article_language}")
                
                try:
                    canonical_key = generate_canonical_key(
                        language=article_language,
                        category=canonical_category,
                        subtype=canonical_subtype
                    )
                    print(f"✅ [DEBUG] 生成 canonical_key: {canonical_key} (使用文章language: {article_language})")
                except Exception as e:
                    print(f"❌ [DEBUG] 生成 canonical_key 失败: {e}")
                    canonical_key = None
                
                # 如果 canonical_key 生成失败，使用组合 key 作为 fallback
                if not canonical_key:
                    canonical_key = f"{canonical_category}::{canonical_subtype}"
                    print(f"⚠️ [DEBUG] canonical_key 生成失败，使用 fallback: {canonical_key}")
                
                # 🔧 2. 添加到 GrammarSummary（使用新格式）
                # 注意：rule_summary 将在查重后生成（只有新语法才需要）
                self.session_state.add_grammar_summary(
                    canonical_category=canonical_category,
                    canonical_subtype=canonical_subtype,
                    canonical_function=canonical_function or "",
                    canonical_key=canonical_key
                )
                print(f"✅ [DEBUG] 添加新格式语法总结: display_name={display_name}, canonical_key={canonical_key}")
                
                # 临时存储 display_name（用于后续添加到数据库）
                # rule_summary 将在查重后生成
                if not hasattr(self.session_state, '_grammar_metadata'):
                    self.session_state._grammar_metadata = {}
                # 使用 canonical_key 作为 key（现在一定有值）
                metadata_key = canonical_key
                self.session_state._grammar_metadata[metadata_key] = {
                    'display_name': display_name,
                    'rule_summary': None  # 将在查重后生成
                }
                print(f"🔍 [DEBUG] 临时存储语法元数据: key={metadata_key}, display_name={display_name}")
                
                return True
            
            # 处理返回结果（支持单个对象或列表）
            grammar_list = []
            if isinstance(grammar_summary, dict):
                # 单个对象
                grammar_list = [grammar_summary]
            elif isinstance(grammar_summary, list) and len(grammar_summary) > 0:
                # 列表格式（支持多个语法知识点）
                grammar_list = grammar_summary
                print(f"✅ [DEBUG] 检测到多个语法知识点: {len(grammar_list)} 个")
            elif isinstance(grammar_summary, str):
                if grammar_summary.strip() == "":
                    print(f"⚠️ [DEBUG] AI 返回空字符串，表示没有新的语法规则")
                else:
                    print(f"⚠️ [DEBUG] AI 返回字符串（非空）: {_preview_for_log(grammar_summary, 400)}")
            else:
                print(f"⚠️ [DEBUG] grammar_summary 类型未知: {type(grammar_summary)}, 值: {_preview_for_log(grammar_summary, 400)}")
            
            # 处理每个语法知识点
            for grammar_item in grammar_list:
                if isinstance(grammar_item, dict):
                    # 检查是否是新格式
                    if "display_name" in grammar_item and "canonical" in grammar_item:
                        process_new_format_grammar(grammar_item)
                    else:
                        # 旧格式兼容（向后兼容）
                        grammar_name = grammar_item.get("grammar_rule_name", "Unknown")
                        grammar_explanation = grammar_item.get("grammar_rule_summary", "No explanation provided")
                        if grammar_name and grammar_name != "Unknown" and grammar_explanation and grammar_explanation != "No explanation provided":
                            print(f"⚠️ [DEBUG] 检测到旧格式语法规则，已弃用: {grammar_name}")
                        else:
                            print(f"⚠️ [DEBUG] 语法总结为空或无效: name={grammar_name}, explanation={grammar_explanation}")
                else:
                    print(f"⚠️ [DEBUG] 语法规则格式不支持: {type(grammar_item)}, 值: {_preview_for_log(grammar_item, 400)}")

        # 检查是否与词汇相关
        if self.session_state.check_relevant_decision and self.session_state.check_relevant_decision.vocab:
            print("✅ 词汇相关，开始总结词汇。")
            # 确保所有参数都不为 None
            sentence_body = effective_sentence_body
            user_input = self.session_state.current_input if self.session_state.current_input else user_question
            ai_response_str = self.session_state.current_response if self.session_state.current_response else ai_response
            
            raw_vocab_summary = self.summarize_vocab_rule_assistant.run(
                sentence_body,
                user_input,
                ai_response_str,
                is_non_whitespace=self.current_is_non_whitespace,
                user_id=self._user_id, session=self._db_session
            )

            # 🔧 修复：避免跨多轮累积过多 vocab，总是只针对当前轮的词汇进行处理
            # 支持两种返回形式：单个 dict 或 list[dict]
            # 并且优先聚焦于当前 selected_token 对应的词汇；如果过滤后结果为空，则回退为“接受本轮所有 vocab”
            self.session_state.summarized_results.clear()
            current_token_text = getattr(self.session_state.current_selected_token, "token_text", None)

            def _accept_vocab(vocab_str: str) -> bool:
                """根据当前选中的 token 文本过滤 vocab，避免一次性处理多个无关词。"""
                if not vocab_str:
                    return False
                if not current_token_text:
                    # 没有选中具体 token 时，接受本轮所有 vocab
                    return True
                # 宽松匹配：忽略大小写，允许屈折/派生形式（包含关系）
                v = str(vocab_str).strip()
                t = str(current_token_text).strip()
                v_lower = v.lower()
                t_lower = t.lower()
                return v_lower == t_lower or v_lower in t_lower or t_lower in v_lower

            # 统一成 list 形式处理
            vocab_items = []
            if isinstance(raw_vocab_summary, dict):
                vocab_items = [raw_vocab_summary]
            elif isinstance(raw_vocab_summary, list):
                vocab_items = raw_vocab_summary[:]

            # 🔧 如果 summarizer 完全没有返回任何 vocab，但当前 clearly 有选中的 token，
            # 则回退为：直接把当前选中的单词当作本轮的唯一 vocab
            if not vocab_items and current_token_text:
                print(f"🆕 [DEBUG] summarizer 未返回 vocab，回退使用当前选中单词: '{current_token_text}'")
                vocab_items = [{"vocab": current_token_text}]

            filtered_items = []
            seen = set()
            for item in vocab_items:
                vocab_str = item.get("vocab", "Unknown")
                if not _accept_vocab(vocab_str):
                    continue
                key = vocab_str.strip().lower()
                if key in seen:
                    # 🔧 去重：同一轮中同一个词只处理一次，避免重复添加 example
                    continue
                seen.add(key)
                filtered_items.append(vocab_str)

            # 如果根据当前 token 过滤后一个都没有，但确实有 vocab，总体退回“接受全部”
            if not filtered_items and vocab_items:
                filtered_items = []
                seen = set()
                for item in vocab_items:
                    vocab_str = item.get("vocab", "Unknown")
                    key = vocab_str.strip().lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    filtered_items.append(vocab_str)

            for vocab_str in filtered_items:
                self.session_state.add_vocab_summary(vocab_str)

        # 语法处理：检查相似度，为现有规则添加例句或添加新规则
        if DISABLE_GRAMMAR_FEATURES:
            print("⏸️ [MainAssistant] Grammar compare/new-rule flow disabled — skipping grammar pipeline")
            current_grammar_rules = []
            new_grammar_summaries = []
            article_language = None
        else:
            print("🔍 处理语法规则：检查相似度...")
            
            # 🔧 获取当前文章的language字段
            current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else quoted_sentence
            article_language = None
            user_id = getattr(self.session_state, 'user_id', None)
            
            if current_sentence and hasattr(current_sentence, 'text_id') and user_id:
                try:
                    from database_system.database_manager import DatabaseManager
                    from database_system.business_logic.models import OriginalText
                    db_manager = DatabaseManager('development')
                    session = db_manager.get_session()
                    try:
                        text_model = session.query(OriginalText).filter(
                            OriginalText.text_id == current_sentence.text_id,
                            OriginalText.user_id == user_id
                        ).first()
                        if text_model:
                            article_language = text_model.language
                            print(f"🔍 [DEBUG] 获取文章language: {article_language} (text_id={current_sentence.text_id})")
                        else:
                            print(f"⚠️ [DEBUG] 文章不存在: text_id={current_sentence.text_id}, user_id={user_id}")
                    finally:
                        session.close()
                except Exception as e:
                    print(f"⚠️ [DEBUG] 获取文章language失败: {e}")
            
            # 🔧 获取所有现有语法规则（包含language信息），而不是只获取名称
            current_grammar_rules = []
            if user_id:
                try:
                    from database_system.database_manager import DatabaseManager
                    from database_system.business_logic.models import GrammarRule
                    db_manager = DatabaseManager('development')
                    session = db_manager.get_session()
                    try:
                        # 🔧 直接查询数据库，只获取当前用户且相同语言的语法规则
                        query = session.query(GrammarRule).filter(
                            GrammarRule.user_id == user_id
                        )
                        # 🔧 如果文章有语言，只获取相同语言的规则
                        if article_language:
                            query = query.filter(GrammarRule.language == article_language)
                            print(f"📚 只获取相同语言的语法规则 (user_id={user_id}, language={article_language})")
                        else:
                            print(f"📚 文章无语言信息，获取所有语言的语法规则 (user_id={user_id})")
                        
                        grammar_models = query.all()
                        # 构建规则字典：{name, rule_id, language, canonical_key}
                        for rule_model in grammar_models:
                            current_grammar_rules.append({
                                'name': rule_model.rule_name,
                                'rule_id': rule_model.rule_id,
                                'language': rule_model.language,
                                'canonical_key': rule_model.canonical_key  # 新增：包含 canonical_key
                            })
                        print(f"📚 当前已有 {len(current_grammar_rules)} 个语法规则（包含language和canonical_key信息，user_id={user_id}）")
                    finally:
                        session.close()
                except Exception as e:
                    print(f"⚠️ [DEBUG] 从数据库获取语法规则失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 回退到文件系统管理器
                    current_grammar_rule_names = self.data_controller.grammar_manager.get_all_rules_name()
                    current_grammar_rules = [{'name': name, 'rule_id': None, 'language': None} for name in current_grammar_rule_names]
            else:
                # 没有user_id，使用文件系统管理器
                current_grammar_rule_names = self.data_controller.grammar_manager.get_all_rules_name()
                current_grammar_rules = [{'name': name, 'rule_id': None, 'language': None} for name in current_grammar_rule_names]
            
            print(f"📚 现有语法规则列表: {[r['name'] for r in current_grammar_rules]}")
            new_grammar_summaries = []
        
        # 🔧 查重逻辑：基于 canonical_key 进行对比
        # 🔧 同时检查 grammar_to_add 和已有语法列表，避免重复添加
        print("🔍 开始语法规则查重（基于 canonical_key）...")
        
        # 构建待查重的语法列表（包括已有语法和 grammar_to_add）
        all_existing_grammars = []
        
        # 1. 添加已有语法规则
        for existing_rule_info in current_grammar_rules:
            existing_canonical_key = existing_rule_info.get('canonical_key')
            if existing_canonical_key:  # 只添加有 canonical_key 的规则
                all_existing_grammars.append({
                    'canonical_key': existing_canonical_key,
                    'rule_id': existing_rule_info.get('rule_id'),
                    'name': existing_rule_info.get('name'),
                    'language': existing_rule_info.get('language'),
                    'source': 'existing'  # 标记来源
                })
        
        # 2. 添加 grammar_to_add 中的语法规则（避免同一轮对话中重复添加）
        if hasattr(self.session_state, 'grammar_to_add') and self.session_state.grammar_to_add:
            for grammar_to_add in self.session_state.grammar_to_add:
                if hasattr(grammar_to_add, 'canonical_key') and grammar_to_add.canonical_key:
                    all_existing_grammars.append({
                        'canonical_key': grammar_to_add.canonical_key,
                        'rule_id': None,  # grammar_to_add 中的规则还没有 rule_id
                        'name': grammar_to_add.display_name,
                        'language': article_language,  # 使用文章语言
                        'source': 'grammar_to_add'  # 标记来源
                    })
        
        print(f"🔍 [DEBUG] 查重列表包含: {len(all_existing_grammars)} 个语法规则（已有: {len([g for g in all_existing_grammars if g['source'] == 'existing'])}, grammar_to_add: {len([g for g in all_existing_grammars if g['source'] == 'grammar_to_add'])})")
        
        for result in self.session_state.summarized_results:
            if isinstance(result, GrammarSummary):
                # 新格式：使用 canonical_key 进行查重
                new_canonical_key = result.canonical_key
                print(f"🔍 检查语法规则: canonical_key={new_canonical_key} (文章language: {article_language})")
                
                if not new_canonical_key:
                    print(f"⚠️ [DEBUG] 新语法规则的 canonical_key 为空，跳过查重，直接添加为新规则")
                    new_grammar_summaries.append(result)
                    continue
                
                # 轮询所有语法列表（包括已有语法和 grammar_to_add），查找是否有相同的 canonical_key
                found_existing = False
                existing_rule_id = None
                existing_rule_name = None
                existing_source = None
                
                for existing_rule_info in all_existing_grammars:
                    existing_canonical_key = existing_rule_info.get('canonical_key')
                    existing_rule_id = existing_rule_info.get('rule_id')
                    existing_rule_name = existing_rule_info.get('name')
                    existing_rule_language = existing_rule_info.get('language')
                    existing_source = existing_rule_info.get('source')
                    
                    # 🔧 语言过滤：只对比相同语言的语法规则
                    if article_language and existing_rule_language:
                        if article_language != existing_rule_language:
                            print(f"🔍 [DEBUG] 跳过不同语言的语法规则: '{existing_rule_name}' (language={existing_rule_language}, source={existing_source}) vs 文章language={article_language}")
                            continue
                    
                    # 🔧 查重逻辑：如果 canonical_key 一致，则判断为"当前语法已存在"
                    if existing_canonical_key == new_canonical_key:
                        print(f"✅ [DEBUG] 找到相同 canonical_key 的语法规则: '{existing_rule_name}' (rule_id={existing_rule_id}, source={existing_source}, canonical_key={existing_canonical_key})")
                        found_existing = True
                        break
                
                if found_existing:
                    # 🔧 当前语法已存在（在已有语法或 grammar_to_add 中），不加入新语法
                    if existing_source == 'existing' and existing_rule_id:
                        # 如果是在已有语法中找到，进入添加句子为 grammar example 流程
                        print(f"✅ 语法规则已存在 (canonical_key={new_canonical_key})，将添加为 grammar example，不创建新规则")
                        
                        # 为现有语法规则添加新例句
                        current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else sentence_body
                        if current_sentence and existing_rule_id:
                            # 验证句子完整性
                            if hasattr(current_sentence, 'text_id') and hasattr(current_sentence, 'sentence_id'):
                                self._ensure_sentence_integrity(current_sentence, "现有语法 Example 调用")
                                print(f"🔍 [DEBUG] 调用grammar_example_explanation_assistant for '{existing_rule_name}' (rule_id={existing_rule_id})")
                                # 🔧 使用 UI 语言而不是文章语言
                                output_language = self.ui_language or self.session_state.current_language or "中文"
                                print(f"🔍 [DEBUG] 输出语言: {output_language} (UI语言: {self.ui_language}, 文章语言: {self.session_state.current_language})")
                                
                                # 获取 display_name 用于 grammar_example_explanation
                                display_name = ""
                                if hasattr(self.session_state, '_grammar_metadata') and self.session_state._grammar_metadata:
                                    metadata = self.session_state._grammar_metadata.get(new_canonical_key, {})
                                    display_name = metadata.get('display_name', existing_rule_name)
                                
                                example_explanation_raw = self.grammar_example_explanation_assistant.run(
                                    sentence=current_sentence,
                                    grammar=display_name or existing_rule_name,
                                    language=output_language,
                                    user_id=self._user_id, session=self._db_session
                                )
                                print(f"🔍 [DEBUG] example_explanation原始结果: {_preview_for_log(example_explanation_raw, 360)}")
                                
                                # 🔧 解析 JSON 字符串，提取 explanation 字段
                                example_explanation = None
                                if isinstance(example_explanation_raw, str):
                                    try:
                                        from backend.assistants.utility import parse_json_from_text
                                        parsed = parse_json_from_text(example_explanation_raw)
                                        if isinstance(parsed, dict) and "explanation" in parsed:
                                            example_explanation = parsed["explanation"]
                                        else:
                                            example_explanation = example_explanation_raw
                                    except Exception as e:
                                        print(f"⚠️ [DEBUG] 解析 grammar example_explanation JSON 失败: {e}，使用原始字符串")
                                        example_explanation = example_explanation_raw
                                elif isinstance(example_explanation_raw, dict) and "explanation" in example_explanation_raw:
                                    example_explanation = example_explanation_raw["explanation"]
                                else:
                                    example_explanation = str(example_explanation_raw) if example_explanation_raw else None
                                
                                print(f"🔍 [DEBUG] example_explanation解析后: {_preview_for_log(example_explanation, 360)}")
                                
                                try:
                                    print(f"🔍 [DEBUG] 尝试添加现有语法的grammar_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, rule_id={existing_rule_id}")
                                    print(f"🔍 [DEBUG] explanation_context: {_preview_for_log(example_explanation, 360)}")
                                    
                                    # 🔧 为现有语法创建grammar notation（在add_grammar_example之前）
                                    print(f"🔍 [DEBUG] ========== 开始为现有语法创建grammar notation ==========")
                                    print(f"🔍 [DEBUG] 当前句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                                    print(f"🔍 [DEBUG] 现有语法规则ID: {existing_rule_id}")
                                    print(f"🔍 [DEBUG] 现有语法规则名称: {existing_rule_name}")
                                    
                                    # 获取 token_indices（从 session_state 中的 selected_token）
                                    token_indices = self._get_token_indices_from_selection(current_sentence)
                                    print(f"🔍 [DEBUG] 提取的token_indices: {token_indices}")
                                    print(f"🔍 [DEBUG] token_indices类型: {type(token_indices)}")
                                    
                                    # 获取 user_id（用于 notation，需要转换为字符串）
                                    user_id_for_notation = getattr(self.session_state, 'user_id', None)
                                    if user_id_for_notation is None:
                                        user_id_for_notation = self._user_id
                                    # 确保 user_id 是字符串类型
                                    if isinstance(user_id_for_notation, int):
                                        user_id_for_notation = str(user_id_for_notation)
                                    
                                    # 调用 unified_notation_manager 创建 grammar notation
                                    from backend.data_managers.unified_notation_manager import get_unified_notation_manager
                                    notation_manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
                                    print(f"🔍 [DEBUG] 调用mark_notation参数:")
                                    print(f"  - notation_type: grammar")
                                    print(f"  - user_id: {user_id_for_notation}")
                                    print(f"  - text_id: {current_sentence.text_id}")
                                    print(f"  - sentence_id: {current_sentence.sentence_id}")
                                    print(f"  - grammar_id: {existing_rule_id}")
                                    print(f"  - marked_token_ids: {token_indices}")
                                    
                                    success = notation_manager.mark_notation(
                                        notation_type="grammar",
                                        user_id=user_id_for_notation,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        grammar_id=existing_rule_id,
                                        marked_token_ids=token_indices
                                    )
                                    
                                    print(f"🔍 [DEBUG] mark_notation返回结果: {success}")
                                    print(f"🔍 [DEBUG] 结果类型: {type(success)}")
                                    
                                    if success:
                                        # 🔧 使用实际的 user_id（整数）而不是字符串
                                        actual_user_id = getattr(self.session_state, 'user_id', None)
                                        self.session_state.add_created_grammar_notation(
                                            text_id=current_sentence.text_id,
                                            sentence_id=current_sentence.sentence_id,
                                            grammar_id=existing_rule_id,
                                            marked_token_ids=token_indices,
                                            user_id=actual_user_id
                                        )
                                        # 🔧 记录已有语法知识点的 notation（用于 toast）
                                        display_name_for_toast = display_name or existing_rule_name
                                        print(f"🔍 [DEBUG] 准备记录已有语法知识点到 existing_grammar_notations: grammar_id={existing_rule_id}, display_name={display_name_for_toast}, user_id={actual_user_id}")
                                        self.session_state.add_existing_grammar_notation(
                                            grammar_id=existing_rule_id,
                                            display_name=display_name_for_toast,
                                            user_id=actual_user_id
                                        )
                                        print(f"✅ [DEBUG] 成功创建grammar notation并添加到session_state（已有知识点）")
                                        print(f"🔍 [DEBUG] 当前 existing_grammar_notations 数量: {len(self.session_state.existing_grammar_notations)}")
                                        print(f"🔍 [DEBUG] existing_grammar_notations 内容: {self.session_state.existing_grammar_notations}")
                                    else:
                                        print(f"⚠️ [DEBUG] mark_notation返回False，但继续执行")
                                    
                                    # 添加 grammar example
                                    # 🔧 使用数据库管理器添加 grammar example（如果使用数据库）
                                    user_id = getattr(self.session_state, 'user_id', None)
                                    if user_id:
                                        try:
                                            from database_system.database_manager import DatabaseManager
                                            from backend.data_managers import GrammarRuleManagerDB
                                            from database_system.business_logic.models import OriginalText
                                            db_manager = DatabaseManager('development')
                                            session = db_manager.get_session()
                                            try:
                                                # 🔧 先检查text_id是否存在于数据库中且属于当前用户
                                                text_model = session.query(OriginalText).filter(
                                                    OriginalText.text_id == current_sentence.text_id,
                                                    OriginalText.user_id == user_id
                                                ).first()
                                                if not text_model:
                                                    print(f"⚠️ [DEBUG] 跳过添加grammar_example，因为text_id={current_sentence.text_id}不存在或不属于用户{user_id}")
                                                else:
                                                    grammar_db_manager = GrammarRuleManagerDB(session)
                                                    grammar_db_manager.add_grammar_example(
                                                        rule_id=existing_rule_id,
                                                        text_id=current_sentence.text_id,
                                                        sentence_id=current_sentence.sentence_id,
                                                        explanation_context=example_explanation
                                                    )
                                                    print(f"✅ [DEBUG] 现有语法的grammar_example已添加到数据库: rule_id={existing_rule_id}, text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                                            finally:
                                                session.close()
                                        except Exception as e:
                                            print(f"❌ [DEBUG] 使用数据库管理器创建grammar_example失败: {e}")
                                            import traceback
                                            traceback.print_exc()
                                            # 回退到文件系统管理器
                                            print(f"⚠️ [DEBUG] 回退到文件系统管理器")
                                            self.data_controller.add_grammar_example(
                                                rule_id=existing_rule_id,
                                                text_id=current_sentence.text_id,
                                                sentence_id=current_sentence.sentence_id,
                                                explanation_context=example_explanation
                                            )
                                            print(f"✅ [DEBUG] 现有语法的grammar_example添加成功（文件系统）")
                                    else:
                                        # 没有user_id，使用文件系统管理器
                                        self.data_controller.add_grammar_example(
                                            rule_id=existing_rule_id,
                                            text_id=current_sentence.text_id,
                                            sentence_id=current_sentence.sentence_id,
                                            explanation_context=example_explanation
                                        )
                                        print(f"✅ [DEBUG] 现有语法的grammar_example添加成功（文件系统）")
                                    print(f"✅ [DEBUG] 成功为现有语法规则添加grammar_example: rule_id={existing_rule_id}")
                                except Exception as e:
                                    print(f"❌ [DEBUG] 添加grammar_example失败: {e}")
                                    import traceback
                                    traceback.print_exc()
                            else:
                                print(f"⚠️ [DEBUG] 无法添加grammar example: current_sentence={current_sentence}, existing_rule_id={existing_rule_id}")
                    else:
                        # 如果是在 grammar_to_add 中找到，说明同一轮对话中已经准备添加，跳过
                        print(f"✅ 语法规则已在 grammar_to_add 中 (canonical_key={new_canonical_key})，跳过重复添加")
                    
                    # 不添加到 new_grammar_summaries
                    continue
                else:
                    # 🔧 canonical_key 不一致，进入添加新语法规则流程
                    print(f"🆕 新语法知识点：canonical_key='{new_canonical_key}'，将添加为新规则 (继承文章language: {article_language})")
                    new_grammar_summaries.append(result)
        
        # 将新语法添加到 grammar_to_add（只有查重通过的新语法才会到这里）
        if not DISABLE_GRAMMAR_FEATURES:
            if len(new_grammar_summaries) > MAX_KNOWLEDGE_ITEMS_PER_CHAT:
                print(f"⚠️ [MainAssistant] 新语法候选过多，仅保留前 {MAX_KNOWLEDGE_ITEMS_PER_CHAT} 个")
                new_grammar_summaries = new_grammar_summaries[:MAX_KNOWLEDGE_ITEMS_PER_CHAT]
            for grammar in new_grammar_summaries:
                if isinstance(grammar, GrammarSummary):
                    # 新格式：从 GrammarSummary 和临时存储中提取数据
                    canonical_key = grammar.canonical_key
                    display_name = ""
                    rule_summary = ""
                    
                    # 从临时存储中获取 display_name
                    if hasattr(self.session_state, '_grammar_metadata') and self.session_state._grammar_metadata:
                        # 尝试使用 canonical_key 查找
                        metadata = self.session_state._grammar_metadata.get(canonical_key, {})
                        if not metadata and canonical_key:
                            # 如果没找到，尝试使用组合 key
                            fallback_key = f"{grammar.canonical_category}::{grammar.canonical_subtype}"
                            metadata = self.session_state._grammar_metadata.get(fallback_key, {})
                        display_name = metadata.get('display_name', '')
                        rule_summary = metadata.get('rule_summary', None)  # 可能是 None，表示还未生成
                        print(f"🔍 [DEBUG] 从临时存储获取元数据: canonical_key={canonical_key}, display_name={display_name}, rule_summary={'已生成' if rule_summary else '未生成'}...")
                    
                    if not display_name:
                        # 如果没有找到，使用默认值
                        display_name = f"{grammar.canonical_category}::{grammar.canonical_subtype}"
                        print(f"⚠️ [DEBUG] 未找到 display_name，使用默认值: {display_name}")
                    
                    # 🔧 如果 rule_summary 还未生成，现在生成（只有新语法才需要）
                    if not rule_summary:
                        print(f"🔍 [DEBUG] rule_summary 未生成，现在调用 grammar_explanation_assistant 生成...")
                        # 获取用户引用的句子
                        sentence_body = effective_sentence_body
                        # 构建 grammar_dict 用于 grammar_explanation_assistant
                        grammar_dict = {
                            "display_name": display_name,
                            "canonical": {
                                "category": grammar.canonical_category,
                                "subtype": grammar.canonical_subtype,
                                "function": grammar.canonical_function
                            }
                        }
                        # 🔧 获取用户正在学习的语言（文章语言）- 从数据库获取实际语言
                        learning_language = None
                        current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else sentence_body
                        user_id = getattr(self.session_state, 'user_id', None) or self._user_id
                        
                        if current_sentence and hasattr(current_sentence, 'text_id') and user_id:
                            try:
                                from database_system.database_manager import DatabaseManager
                                from database_system.business_logic.models import OriginalText
                                db_manager = DatabaseManager('development')
                                session = db_manager.get_session()
                                try:
                                    text_model = session.query(OriginalText).filter(
                                        OriginalText.text_id == current_sentence.text_id,
                                        OriginalText.user_id == user_id
                                    ).first()
                                    if text_model:
                                        learning_language = text_model.language
                                        print(f"🔍 [DEBUG] 从数据库获取文章language用于grammar_explanation: {learning_language} (text_id={current_sentence.text_id})")
                                finally:
                                    session.close()
                            except Exception as e:
                                print(f"⚠️ [DEBUG] 获取文章language失败: {e}")
                        
                        # 如果无法从数据库获取，使用默认值
                        if not learning_language:
                            learning_language = self.session_state.current_language or "中文"
                            print(f"⚠️ [DEBUG] 无法获取文章language，使用默认值: {learning_language}")
                        
                        # 获取输出语言（UI语言）
                        output_language = self.ui_language or self.session_state.current_language or "中文"
                        print(f"🔍 [DEBUG] 学习语言: {learning_language}, 输出语言: {output_language}")
                        try:
                            explanation_result = self.grammar_explanation_assistant.run(
                                quoted_sentence=sentence_body,
                                grammar_summary=grammar_dict,
                                language=output_language,  # 输出语言（UI语言）
                                learning_language=learning_language,  # 用户正在学习的语言（文章语言）
                                user_id=self._user_id,
                                session=self._db_session
                            )
                            print(f"🔍 [DEBUG] grammar_explanation 结果: {type(explanation_result)}, 值: {explanation_result}")
                            
                            # 解析解释结果
                            if isinstance(explanation_result, dict):
                                rule_summary = explanation_result.get("grammar_explanation", "")
                            elif isinstance(explanation_result, str):
                                # 尝试解析 JSON 字符串
                                try:
                                    parsed = json.loads(explanation_result)
                                    rule_summary = parsed.get("grammar_explanation", "")
                                except:
                                    rule_summary = explanation_result
                            
                            if not rule_summary:
                                print(f"⚠️ [DEBUG] grammar_explanation 返回空，使用默认解释")
                                rule_summary = f"{display_name}的语法规则"
                            
                            print(f"✅ [DEBUG] 语法规则解释生成成功: {rule_summary[:50]}...")
                            
                            # 更新临时存储中的 rule_summary
                            if hasattr(self.session_state, '_grammar_metadata') and self.session_state._grammar_metadata:
                                if canonical_key in self.session_state._grammar_metadata:
                                    self.session_state._grammar_metadata[canonical_key]['rule_summary'] = rule_summary
                        except Exception as e:
                            print(f"❌ [DEBUG] grammar_explanation 调用失败: {e}")
                            import traceback
                            traceback.print_exc()
                            rule_summary = f"{display_name}的语法规则"
                    
                    if not rule_summary:
                        rule_summary = f"{display_name}的语法规则"
                        print(f"⚠️ [DEBUG] 未找到 rule_summary，使用默认值: {rule_summary}")
                    
                    print(f"🆕 添加新语法: display_name={display_name}, canonical_key={canonical_key}")
                    self.session_state.add_grammar_to_add(
                        canonical_category=grammar.canonical_category,
                        canonical_subtype=grammar.canonical_subtype,
                        canonical_function=grammar.canonical_function,
                        canonical_key=canonical_key,
                        display_name=display_name,
                        rule_summary=rule_summary
                    )
                else:
                    # 旧格式兼容（向后兼容）
                    print(f"🆕 添加新语法（旧格式）: {grammar.grammar_rule_name}")
                    self.session_state.add_grammar_to_add(
                        canonical_category="",
                        canonical_subtype="",
                        canonical_function="",
                        canonical_key="",
                        display_name=grammar.grammar_rule_name,
                        rule_summary=grammar.grammar_rule_summary
                    )

        print("grammar to add：", self.session_state.grammar_to_add)
        #add to data
        
        # 调试信息：打印summarized_results的内容
        print("🔍 [DEBUG] summarized_results 内容:")
        for i, result in enumerate(self.session_state.summarized_results):
            print(f"  {i}: {type(result)} - {result}")
        
        # 🔧 修复：优先使用数据库管理器获取当前用户的词汇列表
        user_id = getattr(self.session_state, 'user_id', None)
        current_vocab_list = []
        vocab_id_map = {}  # vocab_body -> vocab_id 映射
        
        if user_id:
            try:
                from database_system.database_manager import DatabaseManager
                from database_system.business_logic.models import VocabExpression
                db_manager = DatabaseManager('development')
                session = db_manager.get_session()
                try:
                    # 🔧 直接查询数据库，按 user_id 和 language 过滤
                    query = session.query(VocabExpression).filter(
                        VocabExpression.user_id == user_id
                    )
                    # 🔧 如果文章有语言，只获取相同语言的词汇
                    if article_language:
                        query = query.filter(VocabExpression.language == article_language)
                        print(f"🔍 [DEBUG] 只获取相同语言的词汇 (user_id={user_id}, language={article_language})")
                    else:
                        print(f"🔍 [DEBUG] 文章无语言信息，获取所有语言的词汇 (user_id={user_id})")
                    
                    vocab_models = query.all()
                    current_vocab_list = [vocab.vocab_body for vocab in vocab_models]
                    vocab_id_map = {vocab.vocab_body: vocab.vocab_id for vocab in vocab_models}
                    print(f"🔍 [DEBUG] 从数据库获取当前用户词汇列表 (user_id={user_id}): {len(current_vocab_list)} 个词汇")
                finally:
                    session.close()
            except Exception as e:
                print(f"⚠️ [DEBUG] 使用数据库管理器获取词汇列表失败: {e}")
                import traceback
                traceback.print_exc()
                # 回退到文件系统管理器
                current_vocab_list = self.data_controller.vocab_manager.get_all_vocab_body()
                print(f"🔍 [DEBUG] 回退到文件系统管理器，获取词汇列表: {len(current_vocab_list)} 个词汇")
        else:
            # 没有 user_id，使用文件系统管理器
            current_vocab_list = self.data_controller.vocab_manager.get_all_vocab_body()
            print(f"🔍 [DEBUG] 当前词汇列表 (文件系统): {len(current_vocab_list)} 个词汇")
        
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
                        # 🔧 修复：优先使用数据库管理器的 vocab_id_map，否则回退到文件系统管理器
                        if vocab in vocab_id_map:
                            existing_vocab_id = vocab_id_map[vocab]
                            print(f"🔍 [DEBUG] 从数据库获取 vocab_id: {existing_vocab_id} (vocab='{vocab}')")
                        else:
                            existing_vocab_id = self.data_controller.vocab_manager.get_id_by_vocab_body(vocab)
                            print(f"🔍 [DEBUG] 从文件系统获取 vocab_id: {existing_vocab_id} (vocab='{vocab}')")
                        current_sentence = self.session_state.current_sentence if self.session_state.current_sentence else quoted_sentence
                        # 验证句子完整性
                        self._ensure_sentence_integrity(current_sentence, "Vocab Explanation 调用")
                        # 为上下文解释优先使用“用户实际选择的词形”，避免因词形差异导致的"不在句中"提示
                        selected_token = self.session_state.current_selected_token
                        vocab_for_context = getattr(selected_token, 'token_text', None) or vocab
                        print(f"🔍 [DEBUG] 调用vocab_example_explanation_assistant for '{vocab_for_context}' (base='{vocab}')")
                        # 🔧 使用 UI 语言而不是文章语言
                        output_language = self.ui_language or self.session_state.current_language or "中文"
                        print(f"🔍 [DEBUG] 输出语言: {output_language} (UI语言: {self.ui_language}, 文章语言: {self.session_state.current_language})")
                        example_explanation_raw = self.vocab_example_explanation_assistant.run(
                            sentence=current_sentence,
                            vocab=vocab_for_context,
                            language=output_language,
                            user_id=self._user_id, session=self._db_session
                        )
                        print(f"🔍 [DEBUG] example_explanation原始结果: {_preview_for_log(example_explanation_raw, 360)}")
                        
                        # 🔧 解析 JSON 字符串，提取 explanation 字段
                        example_explanation = None
                        if isinstance(example_explanation_raw, str):
                            try:
                                from backend.assistants.utility import parse_json_from_text
                                parsed = parse_json_from_text(example_explanation_raw)
                                if isinstance(parsed, dict) and "explanation" in parsed:
                                    example_explanation = parsed["explanation"]
                                else:
                                    example_explanation = example_explanation_raw
                            except Exception as e:
                                print(f"⚠️ [DEBUG] 解析 example_explanation JSON 失败: {e}，使用原始字符串")
                                example_explanation = example_explanation_raw
                        elif isinstance(example_explanation_raw, dict) and "explanation" in example_explanation_raw:
                            example_explanation = example_explanation_raw["explanation"]
                        else:
                            example_explanation = str(example_explanation_raw) if example_explanation_raw else None
                        
                        print(f"🔍 [DEBUG] example_explanation解析后: {_preview_for_log(example_explanation, 360)}")
                        
                        # 检查text_id是否存在，如果不存在则跳过添加example
                        try:
                            # 🔧 获取 token_indices（优先使用保存的 selected_token，如果不存在则从 session_state 获取）
                            # 临时恢复 selected_token（如果它被清空了）
                            if not self.session_state.current_selected_token and saved_selected_token:
                                print(f"🔍 [DEBUG] 临时恢复 selected_token（在 handle_grammar_vocab_function 中）")
                                self.session_state.set_current_selected_token(saved_selected_token)
                            
                            token_indices = self._get_token_indices_from_selection(current_sentence)
                            print(f"🔍 [DEBUG] 尝试添加现有词汇的vocab_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, vocab_id={existing_vocab_id}, token_indices={token_indices}")
                            
                            # 🔧 修复：如果使用数据库管理器获取了 vocab_id，也应该使用数据库管理器添加 example
                            if user_id and vocab in vocab_id_map:
                                try:
                                    from database_system.database_manager import DatabaseManager
                                    from backend.data_managers import VocabManagerDB
                                    db_manager = DatabaseManager('development')
                                    session = db_manager.get_session()
                                    try:
                                        vocab_db_manager = VocabManagerDB(session)
                                        # 🔧 确保 token_indices 是列表格式
                                        final_token_indices = token_indices if isinstance(token_indices, list) else (list(token_indices) if token_indices else [])
                                        print(f"🔍 [DEBUG] 最终存储的 token_indices: {final_token_indices}")
                                        vocab_db_manager.add_vocab_example(
                                            vocab_id=existing_vocab_id,
                                            text_id=current_sentence.text_id,
                                            sentence_id=current_sentence.sentence_id,
                                            context_explanation=example_explanation,
                                            token_indices=final_token_indices
                                        )
                                        print(f"✅ [DEBUG] 现有词汇的vocab_example已添加到数据库: vocab_id={existing_vocab_id}, text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, token_indices={final_token_indices}")
                                    finally:
                                        session.close()
                                except Exception as e:
                                    print(f"❌ [DEBUG] 使用数据库管理器添加vocab_example失败: {e}")
                                    import traceback
                                    traceback.print_exc()
                                    # 回退到文件系统管理器
                                    print(f"⚠️ [DEBUG] 回退到文件系统管理器")
                                    self.data_controller.add_vocab_example(
                                        vocab_id=existing_vocab_id,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        context_explanation=example_explanation,
                                        token_indices=token_indices
                                    )
                                    print(f"✅ [DEBUG] 现有词汇的vocab_example添加成功（文件系统）")
                            else:
                                # 没有 user_id 或不在 vocab_id_map 中，使用文件系统管理器
                                self.data_controller.add_vocab_example(
                                    vocab_id=existing_vocab_id,
                                    text_id=current_sentence.text_id,
                                    sentence_id=current_sentence.sentence_id,
                                    context_explanation=example_explanation,
                                    token_indices=token_indices
                                )
                                print(f"✅ [DEBUG] 现有词汇的vocab_example添加成功（文件系统）")

                            # 🔧 新增：为现有词汇创建 vocab notation（用于前端实时显示绿色下划线）
                            try:
                                from backend.data_managers.unified_notation_manager import get_unified_notation_manager
                                notation_manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
                                token_id = token_indices[0] if isinstance(token_indices, list) and token_indices else None
                                word_token_id = None  # 新增：用于存储匹配到的 word_token_id
                                
                                # 🔧 如果 token_id 为空，尝试从句子中查找匹配的 token
                                if token_id is None and hasattr(current_sentence, 'tokens') and current_sentence.tokens:
                                    # 获取词汇名称（从 result.vocab 或从数据库查询）
                                    vocab_body = getattr(result, 'vocab', None)
                                    if not vocab_body:
                                        # 尝试从数据库获取词汇名称
                                        try:
                                            user_id = getattr(self.session_state, 'user_id', None)
                                            if user_id:
                                                from database_system.database_manager import DatabaseManager
                                                from database_system.business_logic.models import VocabExpression
                                                db_manager = DatabaseManager('development')
                                                session = db_manager.get_session()
                                                try:
                                                    vocab_model = session.query(VocabExpression).filter(
                                                        VocabExpression.vocab_id == existing_vocab_id,
                                                        VocabExpression.user_id == user_id
                                                    ).first()
                                                    if vocab_model:
                                                        vocab_body = vocab_model.vocab_body
                                                finally:
                                                    session.close()
                                        except Exception as e:
                                            print(f"⚠️ [DEBUG] 无法获取词汇名称: {e}")
                                    
                                    if vocab_body:
                                        # 🌐 优先尝试匹配 word token（仅用于非空格语言）
                                        word_token_id = self._match_vocab_to_word_token(vocab_body, current_sentence)
                                        
                                        # 如果匹配到 word token，使用 word token 的所有字符 token 作为 token_indices
                                        if word_token_id is not None:
                                            # 找到对应的 word token，获取其所有字符 token 的 sentence_token_id
                                            if NEW_STRUCTURE_AVAILABLE:
                                                enriched_sentence = self._ensure_sentence_has_word_tokens(current_sentence)
                                                word_token_source = enriched_sentence.word_tokens
                                            else:
                                                word_token_source = getattr(current_sentence, "word_tokens", None)

                                            if word_token_source:
                                                for wt in word_token_source:
                                                    if wt.word_token_id == word_token_id and hasattr(wt, 'token_ids') and wt.token_ids:
                                                        # 🔧 使用 word_token 的所有 token_ids（用于显示完整下划线）
                                                        token_indices = list(wt.token_ids)  # 更新 token_indices 为所有字符 token 的 IDs
                                                        token_id = wt.token_ids[0]  # 使用第一个字符 token 的 ID（用于向后兼容）
                                                        print(f"✅ [DEBUG] 匹配到 word_token '{wt.word_body}'，使用所有 token_ids: {token_indices} (word_token_id={word_token_id})")
                                                        break
                                        else:
                                            # 未匹配到 word token，回退到字符 token 匹配（现有逻辑）
                                            vocab_body_lower = vocab_body.lower().strip()
                                            import string
                                            def strip_punctuation(text: str) -> str:
                                                return text.strip(string.punctuation + '。，！？；：""''（）【】《》、')
                                            
                                            vocab_clean = strip_punctuation(vocab_body_lower)
                                            print(f"🔍 [DEBUG] 尝试从句子中查找匹配的token（现有词汇），vocab='{vocab_body}' (清理后='{vocab_clean}')")
                                            
                                            for token in current_sentence.tokens:
                                                if hasattr(token, 'token_type') and token.token_type == 'text':
                                                    if hasattr(token, 'token_body') and hasattr(token, 'sentence_token_id'):
                                                        token_clean = strip_punctuation(token.token_body.lower())
                                                        if token_clean == vocab_clean and token.sentence_token_id is not None:
                                                            token_id = token.sentence_token_id
                                                            print(f"✅ [DEBUG] 在句子中找到匹配的token（现有词汇）: '{token.token_body}' → sentence_token_id={token_id}")
                                                            break
                                
                                current_sentence = self._ensure_sentence_has_word_tokens(current_sentence)

                                # 获取user_id（优先使用session_state中的user_id）
                                user_id_for_notation = getattr(self.session_state, 'user_id', None) or "default_user"
                                print(f"🔍 [DEBUG] 创建vocab notation: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, token_id={token_id}, word_token_id={word_token_id}, vocab_id={existing_vocab_id}, user_id={user_id_for_notation}")
                                
                                if token_id is not None:
                                    v_ok = notation_manager.mark_notation(
                                        notation_type="vocab",
                                        user_id=user_id_for_notation,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        token_id=token_id,
                                        vocab_id=existing_vocab_id,
                                        word_token_id=word_token_id  # 新增：传递 word_token_id
                                    )
                                    print(f"✅ [DEBUG] vocab_notation创建结果: {v_ok}")
                                    if v_ok:
                                        # 记录到 session_state
                                        # 🔧 使用实际的 user_id（整数）而不是字符串
                                        actual_user_id = getattr(self.session_state, 'user_id', None)
                                        self.session_state.add_created_vocab_notation(
                                            text_id=current_sentence.text_id,
                                            sentence_id=current_sentence.sentence_id,
                                            token_id=token_id,
                                            vocab_id=existing_vocab_id,
                                            user_id=actual_user_id
                                        )
                                        # 🔧 记录已有词汇知识点的 notation（用于 toast）
                                        vocab_body = getattr(result, 'vocab', None) or vocab
                                        print(f"🔍 [DEBUG] 准备记录已有词汇知识点到 existing_vocab_notations: vocab_id={existing_vocab_id}, vocab_body={vocab_body}, user_id={actual_user_id}")
                                        self.session_state.add_existing_vocab_notation(
                                            vocab_id=existing_vocab_id,
                                            vocab_body=vocab_body,
                                            user_id=actual_user_id
                                        )
                                        print(f"✅ [DEBUG] 成功创建vocab notation并添加到session_state（已有知识点）")
                                        print(f"🔍 [DEBUG] 当前 existing_vocab_notations 数量: {len(self.session_state.existing_vocab_notations)}")
                                        print(f"🔍 [DEBUG] existing_vocab_notations 内容: {self.session_state.existing_vocab_notations}")
                                else:
                                    print("⚠️ [DEBUG] 无法创建vocab notation：token_id为空（已尝试从句子中查找但未找到匹配的token）")
                            except Exception as vn_err:
                                print(f"❌ [DEBUG] 创建vocab_notation时发生错误: {vn_err}")
                                import traceback
                                traceback.print_exc()
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
        remaining_vocab_slots = max(0, MAX_KNOWLEDGE_ITEMS_PER_CHAT - len(self.session_state.grammar_to_add))
        if len(new_vocab) > remaining_vocab_slots:
            print(f"⚠️ [MainAssistant] 新词汇候选过多，仅保留前 {remaining_vocab_slots} 个")
            new_vocab = new_vocab[:remaining_vocab_slots]
        for vocab in new_vocab:
            print(f"🔍 [DEBUG] 添加新词汇到vocab_to_add: {vocab.vocab}")
            self.session_state.add_vocab_to_add(vocab=vocab.vocab)
        
        print(f"🔍 [DEBUG] 最终vocab_to_add: {self.session_state.vocab_to_add}")

    def add_new_to_data(self):
        """
        将新语法和词汇添加到数据管理器中。
        """
        self._ma_log("========== 开始执行 add_new_to_data ==========")
        self._ma_log(f"🔍 [DEBUG] grammar_to_add 长度: {len(self.session_state.grammar_to_add) if self.session_state.grammar_to_add else 0}")
        self._ma_log(f"🔍 [DEBUG] vocab_to_add 长度: {len(self.session_state.vocab_to_add) if self.session_state.vocab_to_add else 0}")
        
        # 🔧 保存 selected_token 的引用（避免在后续处理中被清空）
        saved_selected_token = self.session_state.current_selected_token
        self._ma_log(f"🔍 [DEBUG] 保存 selected_token 引用: {saved_selected_token is not None}")
        if saved_selected_token:
            self._ma_log(f"🔍 [DEBUG] selected_token.token_text: '{getattr(saved_selected_token, 'token_text', None)}'")
            self._ma_log(f"🔍 [DEBUG] selected_token.token_indices: {getattr(saved_selected_token, 'token_indices', None)}")
        
        # 🔧 获取当前文章的language字段
        current_sentence = self.session_state.current_sentence
        article_language = None
        user_id = getattr(self.session_state, 'user_id', None)
        
        if current_sentence and hasattr(current_sentence, 'text_id') and user_id:
            try:
                from database_system.database_manager import DatabaseManager
                from database_system.business_logic.models import OriginalText
                db_manager = DatabaseManager('development')
                session = db_manager.get_session()
                try:
                    text_model = session.query(OriginalText).filter(
                        OriginalText.text_id == current_sentence.text_id,
                        OriginalText.user_id == user_id
                    ).first()
                    if text_model:
                        article_language = text_model.language
                        print(f"🔍 [DEBUG] 获取文章language: {article_language} (text_id={current_sentence.text_id})")
                    else:
                        print(f"⚠️ [DEBUG] 文章不存在: text_id={current_sentence.text_id}, user_id={user_id}")
                finally:
                    session.close()
            except Exception as e:
                print(f"⚠️ [DEBUG] 获取文章language失败: {e}")
        
        if DISABLE_GRAMMAR_FEATURES:
            print("⏸️ [MainAssistant] Grammar add/new-example disabled — skip grammar_to_add processing")
        elif self.session_state.grammar_to_add:
            print(f"🔍 [DEBUG] 处理grammar_to_add: {len(self.session_state.grammar_to_add)} 个语法规则")
            for grammar in self.session_state.grammar_to_add:
                print(f"🔍 [DEBUG] 处理新语法: display_name={grammar.display_name}, canonical_key={grammar.canonical_key}")
                
                # 🔧 直接使用数据库管理器创建语法规则（传递language参数和canonical字段）
                grammar_rule_id = None
                if user_id:
                    try:
                        from database_system.database_manager import DatabaseManager
                        from backend.data_managers import GrammarRuleManagerDB
                        db_manager = DatabaseManager('development')
                        session = db_manager.get_session()
                        try:
                            grammar_db_manager = GrammarRuleManagerDB(session)
                            grammar_dto = grammar_db_manager.add_new_rule(
                                name=grammar.display_name,  # 使用 display_name 作为 rule_name
                                explanation=grammar.rule_summary,  # 使用 rule_summary 作为 explanation
                                source="qa",
                                is_starred=False,
                                user_id=user_id,
                                language=article_language,  # 🔧 传递文章的language字段
                                display_name=grammar.display_name,  # 新增：传递 display_name
                                canonical_category=grammar.canonical_category,  # 新增：传递 canonical 字段
                                canonical_subtype=grammar.canonical_subtype,
                                canonical_function=grammar.canonical_function,
                                canonical_key=grammar.canonical_key
                            )
                            grammar_rule_id = grammar_dto.rule_id
                            print(f"✅ [DEBUG] 新语法规则已添加到数据库: rule_id={grammar_rule_id}, language={article_language}, canonical_key={grammar.canonical_key}")
                        finally:
                            session.close()
                    except Exception as e:
                        print(f"❌ [DEBUG] 使用数据库管理器创建语法规则失败: {e}")
                        import traceback
                        traceback.print_exc()
                        # 回退到文件系统管理器
                        print(f"⚠️ [DEBUG] 回退到文件系统管理器")
                        grammar_rule_id = self.data_controller.add_new_grammar_rule(
                            rule_name=grammar.display_name,
                            rule_explanation=grammar.rule_summary
                        )
                else:
                    # 没有user_id，使用文件系统管理器
                    grammar_rule_id = self.data_controller.add_new_grammar_rule(
                        rule_name=grammar.display_name,
                        rule_explanation=grammar.rule_summary
                    )
                    print(f"✅ [DEBUG] 新语法规则已添加到文件系统: rule_id={grammar_rule_id}")
                
                if grammar_rule_id is None:
                    print(f"❌ [DEBUG] 无法获取grammar_rule_id，跳过添加例句")
                    continue
                
                print(f"✅ [DEBUG] 新语法规则已添加: rule_id={grammar_rule_id}")
                
                # 为这个语法规则生成例句
                current_sentence = self.session_state.current_sentence
                if current_sentence:
                    # 验证句子完整性
                    self._ensure_sentence_integrity(current_sentence, "新语法 Explanation 调用")
                    print(f"🔍 [DEBUG] 调用grammar_example_explanation_assistant for '{grammar.display_name}'")
                    # 🔧 使用 UI 语言而不是文章语言
                    output_language = self.ui_language or self.session_state.current_language or "中文"
                    print(f"🔍 [DEBUG] 输出语言: {output_language} (UI语言: {self.ui_language}, 文章语言: {self.session_state.current_language})")
                    example_explanation_raw = self.grammar_example_explanation_assistant.run(
                        sentence=current_sentence,
                        grammar=grammar.display_name,  # 使用 display_name
                        language=output_language,
                        user_id=self._user_id, session=self._db_session
                    )
                    print(f"🔍 [DEBUG] grammar_example_explanation原始结果: {_preview_for_log(example_explanation_raw, 360)}")
                    
                    # 🔧 解析 JSON 字符串，提取 explanation 字段
                    example_explanation = None
                    if isinstance(example_explanation_raw, str):
                        try:
                            from backend.assistants.utility import parse_json_from_text
                            parsed = parse_json_from_text(example_explanation_raw)
                            if isinstance(parsed, dict) and "explanation" in parsed:
                                example_explanation = parsed["explanation"]
                            else:
                                example_explanation = example_explanation_raw
                        except Exception as e:
                            print(f"⚠️ [DEBUG] 解析 grammar example_explanation JSON 失败: {e}，使用原始字符串")
                            example_explanation = example_explanation_raw
                    elif isinstance(example_explanation_raw, dict) and "explanation" in example_explanation_raw:
                        example_explanation = example_explanation_raw["explanation"]
                    else:
                        example_explanation = str(example_explanation_raw) if example_explanation_raw else None
                    
                    print(f"🔍 [DEBUG] grammar_example_explanation解析后: {_preview_for_log(example_explanation, 360)}")
                    
                    # 添加语法例句
                    try:
                        # 🔧 直接使用创建时获取的grammar_rule_id
                        
                        print(f"🔍 [DEBUG] 尝试添加grammar_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, rule_id={grammar_rule_id}")
                        # 🔧 修复：如果使用数据库管理器创建了 grammar，也应该使用数据库管理器创建 example
                        user_id = getattr(self.session_state, 'user_id', None)
                        if user_id:
                            try:
                                from database_system.database_manager import DatabaseManager
                                from backend.data_managers import GrammarRuleManagerDB
                                from database_system.business_logic.models import OriginalText
                                db_manager = DatabaseManager('development')
                                session = db_manager.get_session()
                                try:
                                    # 🔧 先检查text_id是否存在于数据库中且属于当前用户
                                    text_model = session.query(OriginalText).filter(
                                        OriginalText.text_id == current_sentence.text_id,
                                        OriginalText.user_id == user_id
                                    ).first()
                                    if not text_model:
                                        print(f"⚠️ [DEBUG] 跳过添加grammar_example，因为text_id={current_sentence.text_id}不存在或不属于用户{user_id}")
                                        continue
                                    
                                    # 🔧 如果grammar_rule_id还没有获取，说明创建失败，跳过
                                    if grammar_rule_id is None:
                                        print(f"❌ [DEBUG] 无法获取grammar_rule_id，跳过添加例句")
                                        continue
                                    
                                    grammar_db_manager = GrammarRuleManagerDB(session)
                                    grammar_db_manager.add_grammar_example(
                                        rule_id=grammar_rule_id,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        explanation_context=example_explanation
                                    )
                                    print(f"✅ [DEBUG] grammar_example已添加到数据库: rule_id={grammar_rule_id}, text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                                finally:
                                    session.close()
                            except Exception as e:
                                print(f"❌ [DEBUG] 使用数据库管理器创建grammar_example失败: {e}")
                                import traceback
                                traceback.print_exc()
                                # 回退到文件系统管理器
                                print(f"⚠️ [DEBUG] 回退到文件系统管理器")
                                if grammar_rule_id in self.data_controller.grammar_manager.grammar_bundles:
                                    self.data_controller.add_grammar_example(
                                        rule_id=grammar_rule_id,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        explanation_context=example_explanation
                                    )
                                    print(f"✅ [DEBUG] grammar_example添加成功（文件系统）")
                                else:
                                    print(f"⚠️ [DEBUG] rule_id={grammar_rule_id} 不在 global_dc 中，跳过添加到文件系统")
                        else:
                            # 没有user_id，使用文件系统管理器
                            self.data_controller.add_grammar_example(
                                rule_id=grammar_rule_id,
                                text_id=current_sentence.text_id,
                                sentence_id=current_sentence.sentence_id,
                                explanation_context=example_explanation
                            )
                            print(f"✅ [DEBUG] grammar_example添加成功（文件系统）")
                        
                        # 🔧 新增：创建grammar notation
                        try:
                            print(f"🔍 [DEBUG] ========== 开始创建新语法的grammar notation ==========")
                            print(f"🔍 [DEBUG] 当前句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                            print(f"🔍 [DEBUG] 语法规则ID: {grammar_rule_id}")
                            print(f"🔍 [DEBUG] 语法规则名称: {grammar.display_name}")
                            
                            # 获取 token_indices（从 session_state 中的 selected_token）
                            token_indices = self._get_token_indices_from_selection(current_sentence)
                            print(f"🔍 [DEBUG] 提取的token_indices: {token_indices}")
                            print(f"🔍 [DEBUG] token_indices类型: {type(token_indices)}")
                            print(f"🔍 [DEBUG] token_indices长度: {len(token_indices) if token_indices else 0}")
                            
                            # 使用unified_notation_manager创建grammar notation（使用数据库）
                            from backend.data_managers.unified_notation_manager import get_unified_notation_manager
                            notation_manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
                            print(f"🔍 [DEBUG] notation_manager创建成功: {type(notation_manager)}")
                            
                            # 获取user_id（优先使用session_state中的user_id）
                            user_id_for_notation = getattr(self.session_state, 'user_id', None) or "default_user"
                            
                            print(f"🔍 [DEBUG] 调用mark_notation参数:")
                            print(f"  - notation_type: grammar")
                            print(f"  - user_id: {user_id_for_notation}")
                            print(f"  - text_id: {current_sentence.text_id}")
                            print(f"  - sentence_id: {current_sentence.sentence_id}")
                            print(f"  - grammar_id: {grammar_rule_id}")
                            print(f"  - marked_token_ids: {token_indices}")
                            
                            success = notation_manager.mark_notation(
                                notation_type="grammar",
                                user_id=user_id_for_notation,
                                text_id=current_sentence.text_id,
                                sentence_id=current_sentence.sentence_id,
                                grammar_id=grammar_rule_id,
                                marked_token_ids=token_indices
                            )
                            
                            print(f"🔍 [DEBUG] mark_notation返回结果: {success}")
                            print(f"🔍 [DEBUG] 结果类型: {type(success)}")
                            
                            if success:
                                print(f"✅ [DEBUG] grammar_notation创建成功")
                                # 记录到 session_state 以便返回给前端
                                # 🔧 使用实际的 user_id（整数）而不是字符串
                                actual_user_id = getattr(self.session_state, 'user_id', None)
                                self.session_state.add_created_grammar_notation(
                                    text_id=current_sentence.text_id,
                                    sentence_id=current_sentence.sentence_id,
                                    grammar_id=grammar_rule_id,
                                    marked_token_ids=token_indices,
                                    user_id=actual_user_id
                                )
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
                    # 🔧 使用 UI 语言而不是文章语言
                    output_language = self.ui_language or self.session_state.current_language or "中文"
                    print(f"🔍 [DEBUG] 输出语言: {output_language} (UI语言: {self.ui_language}, 文章语言: {self.session_state.current_language})")
                    vocab_explanation = self.vocab_explanation_assistant.run(
                        sentence=current_sentence,
                        vocab=vocab.vocab,
                        language=output_language,
                        user_id=self._user_id, session=self._db_session
                    )
                    print(f"🔍 [DEBUG] vocab_explanation结果: {vocab_explanation}")
                    # 解析JSON响应
                    if isinstance(vocab_explanation, dict):
                        # 如果已经是字典，直接提取 explanation 字段
                        explanation_text = vocab_explanation.get("explanation", "No explanation provided")
                    elif isinstance(vocab_explanation, str):
                        # 如果是字符串，尝试解析 JSON
                        try:
                            import json
                            # 尝试解析可能是字典格式的字符串（如 "{'explanation': '...'}" 或 '{"explanation": "..."}'）
                            # 先尝试直接解析 JSON
                            explanation_data = json.loads(vocab_explanation)
                            explanation_text = explanation_data.get("explanation", "No explanation provided")
                        except json.JSONDecodeError:
                            # 如果不是标准 JSON，尝试处理 Python 字典格式的字符串
                            try:
                                # 处理单引号格式的字典字符串
                                import ast
                                explanation_data = ast.literal_eval(vocab_explanation)
                                if isinstance(explanation_data, dict):
                                    explanation_text = explanation_data.get("explanation", "No explanation provided")
                                else:
                                    explanation_text = vocab_explanation
                            except:
                                explanation_text = vocab_explanation
                    else:
                        # 其他类型，转换为字符串
                        explanation_text = str(vocab_explanation)
                else:
                    explanation_text = "No explanation provided"
                
                print(f"🔍 [DEBUG] 添加新词汇到数据库: {vocab.vocab}")
                # 🔧 直接使用数据库管理器创建词汇（传递language参数）
                vocab_id = None
                if user_id:
                    try:
                        from database_system.database_manager import DatabaseManager
                        from backend.data_managers import VocabManagerDB
                        db_manager = DatabaseManager('development')
                        session = db_manager.get_session()
                        try:
                            vocab_db_manager = VocabManagerDB(session)
                            vocab_dto = vocab_db_manager.add_new_vocab(
                                vocab_body=vocab.vocab,
                                explanation=explanation_text,
                                source="qa",
                                is_starred=False,
                                user_id=user_id,
                                language=article_language  # 🔧 传递文章的language字段
                            )
                            vocab_id = vocab_dto.vocab_id
                            print(f"✅ [DEBUG] 新词汇已添加到数据库: vocab_id={vocab_id}, language={article_language}")
                        finally:
                            session.close()
                    except Exception as e:
                        print(f"❌ [DEBUG] 使用数据库管理器创建词汇失败: {e}")
                        # 回退到文件系统管理器
                        print(f"⚠️ [DEBUG] 回退到文件系统管理器")
                        vocab_id = self.data_controller.add_new_vocab(vocab_body=vocab.vocab, explanation=explanation_text)
                else:
                    # 没有user_id，使用文件系统管理器
                    vocab_id = self.data_controller.add_new_vocab(vocab_body=vocab.vocab, explanation=explanation_text)
                    print(f"✅ [DEBUG] 新词汇已添加到文件系统: vocab_id={vocab_id}")
                
                # 生成词汇例句解释
                if current_sentence:
                    # 为上下文解释优先使用“用户实际选择的词形”
                    selected_token = self.session_state.current_selected_token
                    vocab_for_context = getattr(selected_token, 'token_text', None) or vocab.vocab
                    print(f"🔍 [DEBUG] 调用vocab_example_explanation_assistant for '{vocab_for_context}' (base='{vocab.vocab}')")
                    # 🔧 使用 UI 语言而不是文章语言
                    output_language = self.ui_language or self.session_state.current_language or "中文"
                    print(f"🔍 [DEBUG] 输出语言: {output_language} (UI语言: {self.ui_language}, 文章语言: {self.session_state.current_language})")
                    example_explanation_raw = self.vocab_example_explanation_assistant.run(
                        sentence=current_sentence,
                        vocab=vocab_for_context,
                        language=output_language
                    )
                    print(f"🔍 [DEBUG] example_explanation原始结果: {_preview_for_log(example_explanation_raw, 360)}")
                    
                    # 🔧 解析 JSON 字符串，提取 explanation 字段
                    example_explanation = None
                    if isinstance(example_explanation_raw, str):
                        try:
                            from backend.assistants.utility import parse_json_from_text
                            parsed = parse_json_from_text(example_explanation_raw)
                            if isinstance(parsed, dict) and "explanation" in parsed:
                                example_explanation = parsed["explanation"]
                            else:
                                example_explanation = example_explanation_raw
                        except Exception as e:
                            print(f"⚠️ [DEBUG] 解析 example_explanation JSON 失败: {e}，使用原始字符串")
                            example_explanation = example_explanation_raw
                    elif isinstance(example_explanation_raw, dict) and "explanation" in example_explanation_raw:
                        example_explanation = example_explanation_raw["explanation"]
                    else:
                        example_explanation = str(example_explanation_raw) if example_explanation_raw else None
                    
                    print(f"🔍 [DEBUG] example_explanation解析后: {_preview_for_log(example_explanation, 360)}")
                    
                    # 检查text_id是否存在，如果不存在则跳过添加example
                    try:
                        # 🔧 先检查text_id是否存在于数据库中且属于当前用户
                        user_id = getattr(self.session_state, 'user_id', None)
                        if user_id:
                            from database_system.database_manager import DatabaseManager
                            from database_system.business_logic.models import OriginalText
                            db_manager = DatabaseManager('development')
                            session = db_manager.get_session()
                            try:
                                text_model = session.query(OriginalText).filter(
                                    OriginalText.text_id == current_sentence.text_id,
                                    OriginalText.user_id == user_id
                                ).first()
                                if not text_model:
                                    print(f"⚠️ [DEBUG] 跳过添加vocab_example，因为text_id={current_sentence.text_id}不存在或不属于用户{user_id}")
                                    print(f"🔍 [DEBUG] 句子信息: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}")
                                    continue
                            finally:
                                session.close()
                        
                        # 🔧 如果vocab_id还没有获取，说明创建失败，跳过
                        if vocab_id is None:
                            print(f"❌ [DEBUG] 无法获取vocab_id，跳过添加例句")
                            continue
                        
                        # 🔧 获取 token_indices（优先使用保存的 selected_token，如果不存在则从 session_state 获取）
                        # 临时恢复 selected_token（如果它被清空了）
                        if not self.session_state.current_selected_token and saved_selected_token:
                            print(f"🔍 [DEBUG] 临时恢复 selected_token（在 add_new_to_data 中）")
                            self.session_state.set_current_selected_token(saved_selected_token)
                        
                        token_indices = self._get_token_indices_from_selection(current_sentence)
                        print(f"🔍 [DEBUG] 尝试添加vocab_example: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, vocab_id={vocab_id}, token_indices={token_indices}")
                        print(f"🔍 [DEBUG] token_indices 类型: {type(token_indices)}, 值: {token_indices}")
                        
                        # 🔧 修复：如果使用数据库管理器创建了 vocab，也应该使用数据库管理器创建 example
                        if user_id:
                            try:
                                from database_system.database_manager import DatabaseManager
                                from backend.data_managers import VocabManagerDB
                                db_manager = DatabaseManager('development')
                                session = db_manager.get_session()
                                try:
                                    vocab_db_manager = VocabManagerDB(session)
                                    # 🔧 确保 token_indices 是列表格式
                                    final_token_indices = token_indices if isinstance(token_indices, list) else (list(token_indices) if token_indices else [])
                                    print(f"🔍 [DEBUG] 最终存储的 token_indices: {final_token_indices}")
                                    vocab_db_manager.add_vocab_example(
                                        vocab_id=vocab_id,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        context_explanation=example_explanation,
                                        token_indices=final_token_indices
                                    )
                                    print(f"✅ [DEBUG] vocab_example 已添加到数据库: vocab_id={vocab_id}, text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, token_indices={final_token_indices}")
                                finally:
                                    session.close()
                            except Exception as e:
                                print(f"❌ [DEBUG] 使用数据库管理器创建vocab_example失败: {e}")
                                import traceback
                                traceback.print_exc()
                                # 回退到文件系统管理器
                                print(f"⚠️ [DEBUG] 回退到文件系统管理器")
                                # 🔧 注意：如果 vocab 在数据库中，但不在 global_dc 中，这里会失败
                                # 所以需要先检查 vocab_id 是否在 global_dc 中
                                if vocab_id in self.data_controller.vocab_manager.vocab_bundles:
                                    self.data_controller.add_vocab_example(
                                        vocab_id=vocab_id,
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        context_explanation=example_explanation,
                                        token_indices=token_indices
                                    )
                                else:
                                    print(f"⚠️ [DEBUG] vocab_id={vocab_id} 不在 global_dc 中，跳过添加到文件系统")
                        else:
                            # 没有user_id，使用文件系统管理器
                            self.data_controller.add_vocab_example(
                                vocab_id=vocab_id,
                                text_id=current_sentence.text_id,
                                sentence_id=current_sentence.sentence_id,
                                context_explanation=example_explanation,
                                token_indices=token_indices
                            )
                        print(f"✅ [DEBUG] vocab_example添加成功")

                        # 🔧 新增：为新词汇创建 vocab notation（用于前端实时显示绿色下划线，使用数据库）
                        try:
                            from backend.data_managers.unified_notation_manager import get_unified_notation_manager
                            notation_manager = get_unified_notation_manager(use_database=True, use_legacy_compatibility=True)
                            # 🔧 确保使用和 vocab_example 相同的 token_indices
                            token_id = token_indices[0] if isinstance(token_indices, list) and len(token_indices) > 0 else None
                            word_token_id = None  # 新增：用于存储匹配到的 word_token_id
                            print(f"🔍 [DEBUG] 创建 vocab notation 使用的 token_id: {token_id} (来自 token_indices={token_indices})")
                            
                            # 🌐 优先尝试匹配 word token（仅用于非空格语言）
                            # 即使 token_id 不为空，也要检查是否应该使用 word_token
                            vocab_body = vocab.vocab
                            word_token_id = self._match_vocab_to_word_token(vocab_body, current_sentence)
                            
                            # 如果匹配到 word token，使用 word token 的所有字符 token 作为 token_indices
                            if word_token_id is not None:
                                # 🔧 确保 current_sentence 有 word_tokens 数据
                                current_sentence = self._ensure_sentence_has_word_tokens(current_sentence)
                                # 找到对应的 word token，获取其所有字符 token 的 sentence_token_id
                                if NEW_STRUCTURE_AVAILABLE and isinstance(current_sentence, NewSentence):
                                    if current_sentence.word_tokens is None:
                                        print(f"⚠️ [DEBUG] word_token_id={word_token_id} 但 current_sentence.word_tokens 为 None，跳过 word token 迭代")
                                    else:
                                        for wt in current_sentence.word_tokens:
                                            if wt.word_token_id == word_token_id and hasattr(wt, 'token_ids') and wt.token_ids:
                                                # 🔧 使用 word_token 的所有 token_ids 作为 token_indices（用于显示完整下划线）
                                                token_indices = list(wt.token_ids)  # 使用所有字符 token 的 IDs
                                                token_id = wt.token_ids[0]  # 使用第一个字符 token 的 ID（用于向后兼容）
                                                print(f"✅ [DEBUG] 匹配到 word_token '{wt.word_body}'，使用所有 token_ids: {token_indices} (word_token_id={word_token_id})")
                                                break
                            else:
                                # 未匹配到 word token，如果 token_id 为空，尝试从句子中查找匹配的 token
                                if token_id is None and hasattr(current_sentence, 'tokens') and current_sentence.tokens:
                                    # 回退到字符 token 匹配（现有逻辑）
                                    vocab_body_lower = vocab_body.lower().strip()
                                    import string
                                    def strip_punctuation(text: str) -> str:
                                        return text.strip(string.punctuation + '。，！？；：""''（）【】《》、')
                                    
                                    vocab_clean = strip_punctuation(vocab_body_lower)
                                    print(f"🔍 [DEBUG] 尝试从句子中查找匹配的token，vocab='{vocab.vocab}' (清理后='{vocab_clean}')")
                                    
                                    for token in current_sentence.tokens:
                                        if hasattr(token, 'token_type') and token.token_type == 'text':
                                            if hasattr(token, 'token_body') and hasattr(token, 'sentence_token_id'):
                                                token_clean = strip_punctuation(token.token_body.lower())
                                                if token_clean == vocab_clean and token.sentence_token_id is not None:
                                                    token_id = token.sentence_token_id
                                                    print(f"✅ [DEBUG] 在句子中找到匹配的token: '{token.token_body}' → sentence_token_id={token_id}")
                                                    break
                            
                            # 获取user_id（优先使用session_state中的user_id）
                            current_sentence = self._ensure_sentence_has_word_tokens(current_sentence)
                            user_id_for_notation = getattr(self.session_state, 'user_id', None) or "default_user"
                            print(f"🔍 [DEBUG] 创建新词汇的vocab notation: text_id={current_sentence.text_id}, sentence_id={current_sentence.sentence_id}, token_id={token_id}, word_token_id={word_token_id}, vocab_id={vocab_id}, user_id={user_id_for_notation}")
                            
                            if token_id is not None:
                                v_ok = notation_manager.mark_notation(
                                    notation_type="vocab",
                                    user_id=user_id_for_notation,
                                    text_id=current_sentence.text_id,
                                    sentence_id=current_sentence.sentence_id,
                                    token_id=token_id,
                                    vocab_id=vocab_id,
                                    word_token_id=word_token_id  # 新增：传递 word_token_id
                                )
                                print(f"✅ [DEBUG] 新词汇 vocab_notation创建结果: {v_ok}")
                                if v_ok:
                                    # 记录到 session_state
                                    # 🔧 使用实际的 user_id（整数）而不是字符串
                                    actual_user_id = getattr(self.session_state, 'user_id', None)
                                    self.session_state.add_created_vocab_notation(
                                        text_id=current_sentence.text_id,
                                        sentence_id=current_sentence.sentence_id,
                                        token_id=token_id,
                                        vocab_id=vocab_id,
                                        user_id=actual_user_id
                                    )
                            else:
                                print("⚠️ [DEBUG] 无法创建新词汇 vocab notation：token_id为空（已尝试从句子中查找但未找到匹配的token）")
                        except Exception as vn_err:
                            print(f"❌ [DEBUG] 创建新词汇 vocab_notation时发生错误: {vn_err}")
                            import traceback
                            traceback.print_exc()
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
    