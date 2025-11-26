"""
文章相关 CRUD 操作
"""
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from ..models import OriginalText, Sentence


class TextCRUD:
    """文章 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_text(self, text_title: str, user_id: int = None, language: str = None, processing_status: str = 'completed') -> OriginalText:
        """创建文章"""
        text = OriginalText(text_title=text_title, user_id=user_id, language=language, processing_status=processing_status)
        self.session.add(text)
        self.session.commit()
        self.session.refresh(text)
        return text
    
    def get_text_by_id(self, text_id: int) -> Optional[OriginalText]:
        """根据ID获取文章（预加载sentences、tokens和word_tokens关系）"""
        from sqlalchemy.orm import selectinload
        return self.session.query(OriginalText).options(
            joinedload(OriginalText.sentences).selectinload(Sentence.tokens),
            joinedload(OriginalText.sentences).selectinload(Sentence.word_tokens)
        ).filter(
            OriginalText.text_id == text_id
        ).first()
    
    def get_all_texts(self, user_id: int = None) -> List[OriginalText]:
        """获取所有文章（可选用户过滤）"""
        query = self.session.query(OriginalText)
        if user_id is not None:
            query = query.filter(OriginalText.user_id == user_id)
        return query.all()
    
    def search_texts(self, keyword: str, user_id: int = None) -> List[OriginalText]:
        """搜索文章（可选用户过滤）"""
        query = self.session.query(OriginalText).filter(
            OriginalText.text_title.contains(keyword)
        )
        if user_id is not None:
            query = query.filter(OriginalText.user_id == user_id)
        return query.all()
    
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
        """获取文章的所有句子（预加载tokens和word_tokens关系）"""
        from sqlalchemy.orm import selectinload
        return self.session.query(Sentence).options(
            selectinload(Sentence.tokens),
            selectinload(Sentence.word_tokens)
        ).filter(
            Sentence.text_id == text_id
        ).all()
    
    def get_sentence_by_id(self, text_id: int, sentence_id: int) -> Optional[Sentence]:
        """根据ID获取句子（预加载tokens和word_tokens关系）"""
        from sqlalchemy import and_
        from sqlalchemy.orm import selectinload
        return self.session.query(Sentence).options(
            selectinload(Sentence.tokens),
            selectinload(Sentence.word_tokens)
        ).filter(
            and_(Sentence.text_id == text_id, Sentence.sentence_id == sentence_id)
        ).first()
    
    def update_text(self, text_id: int, text_title: str = None, language: str = None, processing_status: str = None) -> Optional[OriginalText]:
        """更新文章"""
        text = self.get_text_by_id(text_id)
        if not text:
            return None
        
        if text_title is not None:
            text.text_title = text_title
        if language is not None:
            text.language = language
        if processing_status is not None:
            text.processing_status = processing_status
        
        self.session.commit()
        self.session.refresh(text)
        return text
    
    def delete_text(self, text_id: int) -> bool:
        """删除文章（级联删除相关句子、tokens等）"""
        text = self.get_text_by_id(text_id)
        if not text:
            return False
        
        self.session.delete(text)
        self.session.commit()
        return True
