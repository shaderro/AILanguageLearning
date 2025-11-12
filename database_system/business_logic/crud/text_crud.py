"""
文章相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import OriginalText, Sentence


class TextCRUD:
    """文章 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_text(self, text_title: str, user_id: int = None) -> OriginalText:
        """创建文章"""
        text = OriginalText(text_title=text_title, user_id=user_id)
        self.session.add(text)
        self.session.commit()
        self.session.refresh(text)
        return text
    
    def get_text_by_id(self, text_id: int) -> Optional[OriginalText]:
        """根据ID获取文章"""
        return self.session.query(OriginalText).filter(
            OriginalText.text_id == text_id
        ).first()
    
    def get_all_texts(self) -> List[OriginalText]:
        """获取所有文章"""
        return self.session.query(OriginalText).all()
    
    def search_texts(self, keyword: str) -> List[OriginalText]:
        """搜索文章"""
        return self.session.query(OriginalText).filter(
            OriginalText.text_title.contains(keyword)
        ).all()
    
    def create_sentence(self, text_id: int, sentence_id: int, sentence_body: str,
                       difficulty_level: Optional[str] = None) -> Sentence:
        """创建句子"""
        sentence = Sentence(
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_body=sentence_body,
            sentence_difficulty_level=difficulty_level
        )
        self.session.add(sentence)
        self.session.commit()
        return sentence
    
    def get_sentences_by_text(self, text_id: int) -> List[Sentence]:
        """获取文章的所有句子"""
        return self.session.query(Sentence).filter(
            Sentence.text_id == text_id
        ).all()
    
    def get_sentence_by_id(self, text_id: int, sentence_id: int) -> Optional[Sentence]:
        """根据ID获取句子"""
        from sqlalchemy import and_
        return self.session.query(Sentence).filter(
            and_(Sentence.text_id == text_id, Sentence.sentence_id == sentence_id)
        ).first()
