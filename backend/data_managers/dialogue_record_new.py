from typing import Dict, List, Tuple, Optional, Union
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence
from assistants.chat_info.selected_token import SelectedToken
import json
import chardet
import os
from datetime import datetime

# 类型别名，支持新旧两种句子类型
SentenceType = Union[Sentence, NewSentence]

class DialogueRecordBySentenceNew:
    def __init__(self):
        self.records: Dict[Tuple[int, int], List[Dict[str, Optional[str]]]] = {}
        #Tuple[text_id, sentence_id], List[Dict[user question, Optional[ai response ]]]
        self.messages_history: List[Dict] = []
        self.max_turns: int = 100  # 默认保留最近100条消息

    def add_user_message(self, sentence: SentenceType, user_input: str, selected_token: Optional[SelectedToken] = None):
        key = (sentence.text_id, sentence.sentence_id)
        if key not in self.records:
            self.records[key] = []
        
        # 创建消息记录，包含selected_token信息
        message_record = {
            "user_input": user_input,
            "ai_response": None,
            "selected_token": selected_token.to_dict() if selected_token else None
        }
        
        self.records[key].append(message_record)

    def add_ai_response(self, sentence: SentenceType, ai_response: str):
        key = (sentence.text_id, sentence.sentence_id)
        if key in self.records and self.records[key]:
            # 补充到最近一条没有 AI 回复的记录中
            for turn in reversed(self.records[key]):
                if isinstance(turn, dict) and turn.get("ai_response") is None:
                    turn["ai_response"] = ai_response
                    return
        # 如果没有找到，就直接加一个完整条目
        self.records.setdefault(key, []).append({
            "user_input": "[Missing user input]",
            "ai_response": ai_response,
            "selected_token": None
        })

    def get_records_by_sentence(self, sentence: SentenceType) -> List[Dict[str, Optional[str]]]:
        return self.records.get((sentence.text_id, sentence.sentence_id), [])
    
    def to_dict_list(self) -> List[Dict]:
        result = []
        for (text_id, sentence_id), turns in self.records.items():
            for turn in turns:
                for user_question, ai_response in turn.items():
                    result.append({
                        "text_id": text_id,
                        "sentence_id": sentence_id,
                        "user_question": user_question,
                        "ai_response": ai_response,
                        "is_learning_related": True,
                        "timestamp": datetime.now().isoformat()
                    })
        return result
    
    def to_organized_dict(self) -> Dict:
        """转换为按text_id和sentence_id组织的字典格式，支持新数据结构"""
        organized = {"texts": {}}
        
        for (text_id, sentence_id), turns in self.records.items():
            text_id_str = str(text_id)
            sentence_id_str = str(sentence_id)
            
            # 初始化text结构
            if text_id_str not in organized["texts"]:
                organized["texts"][text_id_str] = {
                    "text_title": f"Text {text_id}",  # 可以从text_manager获取真实标题
                    "sentences": {}
                }
            
            # 初始化sentence结构
            if sentence_id_str not in organized["texts"][text_id_str]["sentences"]:
                organized["texts"][text_id_str]["sentences"][sentence_id_str] = []
            
            # 添加对话记录
            for turn in turns:
                for user_question, ai_response in turn.items():
                    organized["texts"][text_id_str]["sentences"][sentence_id_str].append({
                        "user_question": user_question,
                        "ai_response": ai_response,
                        "timestamp": datetime.now().isoformat(),
                        "is_learning_related": True
                    })
        
        return organized
    
    def save_all_to_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_organized_dict(), f, ensure_ascii=False, indent=2)

    def save_filtered_to_file(self, path: str, only_learning_related: bool = True):
        filtered = [m for m in self.to_dict_list() if m["is_learning_related"] == only_learning_related]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str):
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

        try:
            data = json.loads(content)
            self.records = {}
            
            # 处理新的组织格式
            if isinstance(data, dict) and "texts" in data:
                for text_id_str, text_data in data["texts"].items():
                    text_id = int(text_id_str)
                    for sentence_id_str, sentence_dialogues in text_data.get("sentences", {}).items():
                        sentence_id = int(sentence_id_str)
                        key = (text_id, sentence_id)
                        if key not in self.records:
                            self.records[key] = []
                        
                        for dialogue in sentence_dialogues:
                            self.records[key].append({
                                dialogue.get("user_question", ""): dialogue.get("ai_response", "")
                            })
            
            # 兼容旧的列表格式
            elif isinstance(data, list):
                for item in data:
                    text_id = item.get("text_id")
                    sentence_id = item.get("sentence_id")
                    if text_id is not None and sentence_id is not None:
                        key = (text_id, sentence_id)
                        if key not in self.records:
                            self.records[key] = []
                        self.records[key].append({
                            item.get("user_question", ""): item.get("ai_response", "")
                        })
            else:
                print(f"[Warning] Unknown data format in {path}. Starting with empty record.")
                
        except FileNotFoundError:
            print(f"[Warning] File not found: {path}. Starting with empty dialogue history.")
            self.records = {}
        except json.JSONDecodeError:
            print(f"[Error] Failed to parse JSON from '{path}'.")

    def print_records_by_sentence(self, sentence: SentenceType):
        print(f"\n📚 对话记录 - 第 {sentence.text_id} 篇 第 {sentence.sentence_id} 句：{sentence.sentence_body}")
        
        # 如果是新数据结构，显示额外信息
        if hasattr(sentence, 'sentence_difficulty_level') and sentence.sentence_difficulty_level:
            print(f"📊 难度级别: {sentence.sentence_difficulty_level}")
        
        if hasattr(sentence, 'tokens') and sentence.tokens:
            print(f"🔤 Token数量: {len(sentence.tokens)}")
            # 显示前几个tokens
            token_preview = [(t.token_body, t.token_type, t.difficulty_level) for t in sentence.tokens[:5]]
            print(f"🔤 Token预览: {token_preview}")
        
        for turn in self.get_records_by_sentence(sentence):
            for user_question, ai_response in turn.items():
                print(f"👤 User: {user_question}")
                print(f"🤖 AI: {ai_response or '(waiting...)'}\n")

    def get_sentence_info(self, sentence: SentenceType) -> Dict:
        """获取句子的详细信息，适配新旧数据结构"""
        info = {
            "text_id": sentence.text_id,
            "sentence_id": sentence.sentence_id,
            "sentence_body": sentence.sentence_body,
            "dialogue_count": len(self.get_records_by_sentence(sentence))
        }
        
        # 新数据结构特有信息
        if hasattr(sentence, 'sentence_difficulty_level'):
            info["difficulty_level"] = sentence.sentence_difficulty_level
        
        if hasattr(sentence, 'tokens') and sentence.tokens:
            info["token_count"] = len(sentence.tokens)
            info["grammar_tokens"] = [t.token_body for t in sentence.tokens if hasattr(t, 'is_grammar_marker') and t.is_grammar_marker]
            info["hard_tokens"] = [t.token_body for t in sentence.tokens if hasattr(t, 'difficulty_level') and t.difficulty_level == "hard"]
            info["easy_tokens"] = [t.token_body for t in sentence.tokens if hasattr(t, 'difficulty_level') and t.difficulty_level == "easy"]
        
        if hasattr(sentence, 'grammar_annotations'):
            info["grammar_annotations"] = sentence.grammar_annotations
        
        if hasattr(sentence, 'vocab_annotations'):
            info["vocab_annotations"] = sentence.vocab_annotations
        
        return info

    def get_tokens_info(self, sentence: SentenceType) -> Dict:
        """获取句子的token详细信息，仅适用于新数据结构"""
        if not hasattr(sentence, 'tokens') or not sentence.tokens:
            return {"error": "No tokens available"}
        
        tokens_info = {
            "total_tokens": len(sentence.tokens),
            "text_tokens": [],
            "punctuation_tokens": [],
            "space_tokens": [],
            "grammar_markers": [],
            "hard_tokens": [],
            "easy_tokens": [],
            "pos_tags": {}
        }
        
        for token in sentence.tokens:
            # 按类型分类
            if token.token_type == "text":
                tokens_info["text_tokens"].append(token.token_body)
            elif token.token_type == "punctuation":
                tokens_info["punctuation_tokens"].append(token.token_body)
            elif token.token_type == "space":
                tokens_info["space_tokens"].append(token.token_body)
            
            # 按难度分类
            if hasattr(token, 'difficulty_level'):
                if token.difficulty_level == "hard":
                    tokens_info["hard_tokens"].append(token.token_body)
                elif token.difficulty_level == "easy":
                    tokens_info["easy_tokens"].append(token.token_body)
            
            # 语法标记
            if hasattr(token, 'is_grammar_marker') and token.is_grammar_marker:
                tokens_info["grammar_markers"].append(token.token_body)
            
            # 词性标注统计
            if hasattr(token, 'pos_tag') and token.pos_tag:
                if token.pos_tag not in tokens_info["pos_tags"]:
                    tokens_info["pos_tags"][token.pos_tag] = []
                tokens_info["pos_tags"][token.pos_tag].append(token.token_body)
        
        return tokens_info

    def get_learning_analytics(self, sentence: SentenceType) -> Dict:
        """获取学习分析数据，适用于新数据结构"""
        analytics = {
            "sentence_id": f"{sentence.text_id}_{sentence.sentence_id}",
            "difficulty_assessment": {},
            "learning_progress": {},
            "recommendations": []
        }
        
        # 难度评估
        if hasattr(sentence, 'sentence_difficulty_level'):
            analytics["difficulty_assessment"]["overall"] = sentence.sentence_difficulty_level
        
        if hasattr(sentence, 'tokens') and sentence.tokens:
            hard_count = len([t for t in sentence.tokens if hasattr(t, 'difficulty_level') and t.difficulty_level == "hard"])
            easy_count = len([t for t in sentence.tokens if hasattr(t, 'difficulty_level') and t.difficulty_level == "easy"])
            total_tokens = len(sentence.tokens)
            
            analytics["difficulty_assessment"]["hard_tokens_ratio"] = hard_count / total_tokens if total_tokens > 0 else 0
            analytics["difficulty_assessment"]["easy_tokens_ratio"] = easy_count / total_tokens if total_tokens > 0 else 0
            analytics["difficulty_assessment"]["complexity_score"] = (hard_count * 2 + easy_count) / (total_tokens * 2) if total_tokens > 0 else 0
        
        # 学习进度
        dialogue_count = len(self.get_records_by_sentence(sentence))
        analytics["learning_progress"]["interaction_count"] = dialogue_count
        analytics["learning_progress"]["engagement_level"] = "high" if dialogue_count > 5 else "medium" if dialogue_count > 2 else "low"
        
        # 学习建议
        if hasattr(sentence, 'tokens') and sentence.tokens:
            hard_tokens = [t.token_body for t in sentence.tokens if hasattr(t, 'difficulty_level') and t.difficulty_level == "hard"]
            if hard_tokens:
                analytics["recommendations"].append(f"重点关注困难词汇: {', '.join(hard_tokens[:3])}")
            
            grammar_tokens = [t.token_body for t in sentence.tokens if hasattr(t, 'is_grammar_marker') and t.is_grammar_marker]
            if grammar_tokens:
                analytics["recommendations"].append(f"注意语法结构: {', '.join(grammar_tokens[:3])}")
        
        return analytics 