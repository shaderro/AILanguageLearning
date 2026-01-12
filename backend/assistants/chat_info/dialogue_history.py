from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence
from assistants.sub_assistants.summarize_dialogue_history import SummarizeDialogueHistoryAssistant
from assistants.chat_info.selected_token import SelectedToken
import json
import chardet
from typing import Union, Optional
from datetime import datetime

# 类型别名，支持新旧两种句子类型
SentenceType = Union[Sentence, NewSentence]

class DialogueHistory:
    def __init__(self, max_turns):
        self.max_turns = max_turns
        self.messages_history = []
        self.summary = str()
        # 尝试创建总结助手，如果没有 OPENAI_API_KEY 则设为 None
        try:
            self.summarize_dialogue_assistant = SummarizeDialogueHistoryAssistant()
        except ValueError as e:
            # OPENAI_API_KEY 未设置，禁用总结功能
            self.summarize_dialogue_assistant = None
            print(f"[WARN] 对话历史总结功能已禁用: {e}")

    def add_message(self, user_input: str, ai_response: str, quoted_sentence: SentenceType, selected_token: Optional[SelectedToken] = None):
        """
        添加对话消息到历史记录，支持新旧两种数据结构和选择的token
        
        Args:
            user_input: 用户输入
            ai_response: AI响应
            quoted_sentence: 引用的句子
            selected_token: 用户选择的token（可选）
        """
        message_data = {
            "user": user_input,
            "ai": ai_response,
            "quote": quoted_sentence
        }
        
        # 如果提供了selected_token，添加到消息中
        if selected_token:
            message_data["selected_token"] = selected_token.to_dict()
        
        self.messages_history.append(message_data)
        self.keep_in_max_turns()

    def _summarize_and_clear(self):
        summary = self.summarize_dialogue_history()
        self.summary = summary
        self.messages_history.clear()
        pass

    def message_history_to_string(self) -> str:
        return "\n".join(
            f"User: {msg['user']}\nAI: {msg['ai']}\nQuote: {msg['quote'].sentence_body}"
            for msg in self.messages_history
        )
    
    def summarize_dialogue_history(self) -> str:
        dialogue_history_str = self.message_history_to_string()
        if not dialogue_history_str:
            return "No dialogue history to summarize."
        
        # 如果没有总结助手（缺少 OPENAI_API_KEY），返回简单总结
        if self.summarize_dialogue_assistant is None:
            print("[INFO] 对话历史总结功能未启用（缺少 OPENAI_API_KEY），跳过 AI 总结")
            return f"对话历史包含 {len(self.messages_history)} 条消息（总结功能未启用，需要 OPENAI_API_KEY）"
        
        print("Summarizing dialogue history...")
        quoted_sentence = self.messages_history[-1]['quote'].sentence_body if self.messages_history else ""
        print("Quoted sentence for summary:", quoted_sentence)
        summary = self.summarize_dialogue_assistant.run(dialogue_history_str, self.messages_history[-1]['quote'], verbose=True)
        if isinstance(summary, str):
            print("Summary is: \n" + summary)
            return summary
        elif isinstance(summary, list) and summary:
            return summary[0].get("summary", "No summary available.")
        else:
            return "No summary available."

    def keep_in_max_turns(self):
        self._summarize_and_clear() if len(self.messages_history) > self.max_turns else None

    def save_to_file(self, path: str):
        # 按text_id组织数据，支持新旧数据结构
        organized_data = {"texts": {}}
        
        for msg in self.messages_history:
            text_id = str(msg["quote"].text_id)
            sentence_id = msg["quote"].sentence_id
            
            # 初始化text结构
            if text_id not in organized_data["texts"]:
                organized_data["texts"][text_id] = {
                    "text_title": f"Text {text_id}",  # 可以从text_manager获取真实标题
                    "current_summary": self.summary,
                    "messages": [],
                    "max_turns": self.max_turns
                }
            
            # 构建quote数据，适配新旧数据结构
            quote_data = {
                "text_id": msg["quote"].text_id,
                "sentence_id": msg["quote"].sentence_id,
                "sentence_body": msg["quote"].sentence_body,
                "grammar_annotations": msg["quote"].grammar_annotations,
                "vocab_annotations": msg["quote"].vocab_annotations,
            }
            
            # 如果是新数据结构，添加额外信息
            if hasattr(msg["quote"], 'sentence_difficulty_level'):
                quote_data["sentence_difficulty_level"] = msg["quote"].sentence_difficulty_level
            
            if hasattr(msg["quote"], 'tokens') and msg["quote"].tokens:
                quote_data["tokens"] = [
                    {
                        "token_body": token.token_body,
                        "token_type": token.token_type,
                        "difficulty_level": token.difficulty_level,
                        "global_token_id": token.global_token_id,
                        "sentence_token_id": token.sentence_token_id,
                        "pos_tag": token.pos_tag,
                        "lemma": token.lemma,
                        "is_grammar_marker": token.is_grammar_marker,
                        "linked_vocab_id": token.linked_vocab_id
                    }
                    for token in msg["quote"].tokens
                ]
            
            # 添加消息
            organized_data["texts"][text_id]["messages"].append({
                "user": msg["user"],
                "ai": msg["ai"],
                "sentence_id": sentence_id,
                "quote": quote_data,
                "timestamp": datetime.now().isoformat(),
                "data_type": "new" if hasattr(msg["quote"], 'sentence_difficulty_level') else "old"
            })
        
        # 如果没有消息，保存空结构
        if not organized_data["texts"]:
            organized_data = {
                "summary": self.summary,
                "messages": []
            }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(organized_data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str):
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"The file at path {path} does not exist.")
        if not os.path.isfile(path):
            raise ValueError(f"The path {path} is not a file.")

        with open(path, 'rb') as f:
            raw_data = f.read()

        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] or 'utf-8'

        try:
            content = raw_data.decode(encoding).strip()
        except UnicodeDecodeError as e:
            print(f"❗️无法用 {encoding} 解码文件 {path}：{e}")
            raise e

        if not content:
            print(f"[Warning] File {path} is empty. Starting with empty record.")
            return

        data = json.loads(content)
        self.messages_history = []
        
        # 处理新的组织格式
        if isinstance(data, dict) and "texts" in data:
            for text_id_str, text_data in data["texts"].items():
                self.summary = text_data.get("current_summary", "")
                for msg in text_data.get("messages", []):
                    quote_data = msg["quote"]
                    data_type = msg.get("data_type", "old")
                    
                    if data_type == "new" and "tokens" in quote_data:
                        # 创建新数据结构句子
                        from data_managers.data_classes_new import Token
                        tokens = [
                            Token(
                                token_body=token_data["token_body"],
                                token_type=token_data["token_type"],
                                difficulty_level=token_data.get("difficulty_level"),
                                global_token_id=token_data.get("global_token_id"),
                                sentence_token_id=token_data.get("sentence_token_id"),
                                pos_tag=token_data.get("pos_tag"),
                                lemma=token_data.get("lemma"),
                                is_grammar_marker=token_data.get("is_grammar_marker", False),
                                linked_vocab_id=token_data.get("linked_vocab_id")
                            )
                            for token_data in quote_data["tokens"]
                        ]
                        
                        sentence = NewSentence(
                            text_id=quote_data["text_id"],
                            sentence_id=quote_data["sentence_id"],
                            sentence_body=quote_data["sentence_body"],
                            grammar_annotations=tuple(quote_data["grammar_annotations"]),
                            vocab_annotations=tuple(quote_data["vocab_annotations"]),
                            sentence_difficulty_level=quote_data.get("sentence_difficulty_level"),
                            tokens=tuple(tokens)
                        )
                    else:
                        # 创建旧数据结构句子
                        sentence = Sentence(
                            text_id=quote_data["text_id"],
                            sentence_id=quote_data["sentence_id"],
                            sentence_body=quote_data["sentence_body"],
                            grammar_annotations=tuple(quote_data["grammar_annotations"]),
                            vocab_annotations=tuple(quote_data["vocab_annotations"])
                        )
                    
                    self.messages_history.append({
                        "user": msg["user"],
                        "ai": msg["ai"],
                        "quote": sentence
                    })
        
        # 兼容旧的格式
        elif isinstance(data, dict) and "messages" in data:
            self.summary = data.get("summary", "")
            self.messages_history = [
                {
                    "user": item["user"],
                    "ai": item["ai"],
                    "quote": Sentence(
                        text_id=item["quote"]["text_id"],
                        sentence_id=item["quote"]["sentence_id"],
                        sentence_body=item["quote"]["sentence_body"],
                        grammar_annotations=tuple(item["quote"]["grammar_annotations"]),
                        vocab_annotations=tuple(item["quote"]["vocab_annotations"])
                    )
                }
                for item in data.get("messages", [])
            ]
        else:
            print(f"[Warning] Unknown data format in {path}. Starting with empty history.")
            self.summary = ""
            self.messages_history = []

    def get_dialogue_analytics(self) -> dict:
        """获取对话分析数据，支持新旧数据结构"""
        analytics = {
            "total_messages": len(self.messages_history),
            "summary": self.summary,
            "data_types": {"old": 0, "new": 0},
            "difficulty_levels": {},
            "token_statistics": {},
            "learning_progress": {}
        }
        
        for msg in self.messages_history:
            sentence = msg["quote"]
            
            # 统计数据结构类型
            if hasattr(sentence, 'sentence_difficulty_level'):
                analytics["data_types"]["new"] += 1
                
                # 统计难度级别
                difficulty = sentence.sentence_difficulty_level
                if difficulty not in analytics["difficulty_levels"]:
                    analytics["difficulty_levels"][difficulty] = 0
                analytics["difficulty_levels"][difficulty] += 1
                
                # 统计token信息
                if hasattr(sentence, 'tokens') and sentence.tokens:
                    if "total_tokens" not in analytics["token_statistics"]:
                        analytics["token_statistics"]["total_tokens"] = 0
                    analytics["token_statistics"]["total_tokens"] += len(sentence.tokens)
                    
                    # 统计困难词汇
                    hard_tokens = [t.token_body for t in sentence.tokens 
                                 if hasattr(t, 'difficulty_level') and t.difficulty_level == "hard"]
                    if hard_tokens:
                        if "hard_tokens" not in analytics["token_statistics"]:
                            analytics["token_statistics"]["hard_tokens"] = []
                        analytics["token_statistics"]["hard_tokens"].extend(hard_tokens)
            else:
                analytics["data_types"]["old"] += 1
        
        # 计算学习进度
        analytics["learning_progress"] = {
            "engagement_level": "high" if len(self.messages_history) > 10 else "medium" if len(self.messages_history) > 5 else "low",
            "new_structure_usage_ratio": analytics["data_types"]["new"] / len(self.messages_history) if self.messages_history else 0
        }
        
        return analytics

    def get_new_structure_messages(self) -> list:
        """获取使用新数据结构的消息列表"""
        return [msg for msg in self.messages_history 
                if hasattr(msg["quote"], 'sentence_difficulty_level')]

    def get_old_structure_messages(self) -> list:
        """获取使用旧数据结构的消息列表"""
        return [msg for msg in self.messages_history 
                if not hasattr(msg["quote"], 'sentence_difficulty_level')]

    def get_messages_by_difficulty(self, difficulty: str) -> list:
        """根据难度级别获取消息列表"""
        return [msg for msg in self.messages_history 
                if hasattr(msg["quote"], 'sentence_difficulty_level') and 
                msg["quote"].sentence_difficulty_level == difficulty]

    def get_hard_tokens_summary(self) -> dict:
        """获取困难词汇总结"""
        hard_tokens_summary = {}
        
        for msg in self.messages_history:
            sentence = msg["quote"]
            if hasattr(sentence, 'tokens') and sentence.tokens:
                hard_tokens = [t.token_body for t in sentence.tokens 
                             if hasattr(t, 'difficulty_level') and t.difficulty_level == "hard"]
                
                for token in hard_tokens:
                    if token not in hard_tokens_summary:
                        hard_tokens_summary[token] = {
                            "count": 0,
                            "contexts": []
                        }
                    hard_tokens_summary[token]["count"] += 1
                    hard_tokens_summary[token]["contexts"].append({
                        "sentence": sentence.sentence_body,
                        "user_question": msg["user"],
                        "ai_response": msg["ai"]
                    })
        
        return hard_tokens_summary

