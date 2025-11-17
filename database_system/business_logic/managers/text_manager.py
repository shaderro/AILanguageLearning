"""
文章管理器 - 高级业务逻辑封装
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..data_access_layer import TextDataAccessLayer
from ..models import OriginalText, Sentence


class TextManager:
    """文章管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = TextDataAccessLayer(session)
    
    def create_text(self, text_title: str, user_id: int = None, language: str = None) -> OriginalText:
        """创建文章"""
        return self.dal.create_text(text_title, user_id, language)
    
    def get_text(self, text_id: int) -> Optional[OriginalText]:
        """获取文章"""
        return self.dal.get_text_by_id(text_id)
    
    def list_texts(self, user_id: int = None) -> List[OriginalText]:
        """列出所有文章（可选用户过滤）"""
        return self.dal.get_all_texts(user_id=user_id)
    
    def search_texts(self, keyword: str, user_id: int = None) -> List[OriginalText]:
        """搜索文章（可选用户过滤）"""
        return self.dal.search_texts(keyword, user_id=user_id)
    
    def create_sentence(self, text_id: int, sentence_id: int, sentence_body: str,
                       difficulty_level: Optional[str] = None) -> Sentence:
        """创建句子"""
        return self.dal.create_sentence(text_id, sentence_id, sentence_body, difficulty_level)
    
    def get_sentences(self, text_id: int) -> List[Sentence]:
        """获取文章的所有句子"""
        return self.dal.get_sentences_by_text(text_id)
    
    def get_sentence(self, text_id: int, sentence_id: int) -> Optional[Sentence]:
        """获取句子"""
        return self.dal.get_sentence_by_id(text_id, sentence_id)
    
    def get_text_with_sentences(self, text_id: int) -> Optional[Dict[str, Any]]:
        """获取文章及其句子"""
        text = self.get_text(text_id)
        if not text:
            return None
        
        sentences = self.get_sentences(text_id)
        return {
            "text_id": text.text_id,
            "text_title": text.text_title,
            "sentences": [
                {
                    "sentence_id": s.sentence_id,
                    "sentence_body": s.sentence_body,
                    "sentence_difficulty_level": s.sentence_difficulty_level
                }
                for s in sentences
            ]
        }
    
    def get_text_stats(self, user_id: int = None) -> Dict[str, int]:
        """获取文章统计（可选用户过滤）"""
        texts = self.list_texts(user_id=user_id)
        total_texts = len(texts)
        total_sentences = sum(len(self.get_sentences(t.text_id)) for t in texts)
        
        return {
            "total_texts": total_texts,
            "total_sentences": total_sentences
        }
