"""
词汇相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models import VocabExpression, VocabExpressionExample, SourceType


class VocabCRUD:
    """词汇 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _coerce_source(self, value: Optional[str]) -> SourceType:
        """转换源类型"""
        if isinstance(value, SourceType):
            return value
        if value is None:
            return SourceType.AUTO
        try:
            return SourceType(value)
        except Exception:
            return SourceType.AUTO
    
    def create(self, vocab_body: str, explanation: str, 
               source: str = "auto", is_starred: bool = False) -> VocabExpression:
        """创建词汇"""
        vocab = VocabExpression(
            vocab_body=vocab_body,
            explanation=explanation,
            source=self._coerce_source(source),
            is_starred=is_starred
        )
        self.session.add(vocab)
        self.session.commit()
        self.session.refresh(vocab)
        return vocab
    
    def get_or_create(self, vocab_body: str, explanation: str,
                      source: str = "auto", is_starred: bool = False) -> VocabExpression:
        """获取或创建词汇"""
        existing = self.session.query(VocabExpression).filter(
            VocabExpression.vocab_body == vocab_body
        ).first()
        if existing:
            return existing
        return self.create(vocab_body, explanation, source, is_starred)
    
    def get_by_id(self, vocab_id: int) -> Optional[VocabExpression]:
        """根据ID获取词汇"""
        return self.session.query(VocabExpression).filter(
            VocabExpression.vocab_id == vocab_id
        ).first()
    
    def get_by_body(self, vocab_body: str) -> Optional[VocabExpression]:
        """根据词汇内容获取"""
        return self.session.query(VocabExpression).filter(
            VocabExpression.vocab_body == vocab_body
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[VocabExpression]:
        """获取所有词汇"""
        return self.session.query(VocabExpression).offset(skip).limit(limit).all()
    
    def get_starred(self) -> List[VocabExpression]:
        """获取收藏的词汇"""
        return self.session.query(VocabExpression).filter(
            VocabExpression.is_starred == True
        ).all()
    
    def search(self, keyword: str) -> List[VocabExpression]:
        """搜索词汇"""
        return self.session.query(VocabExpression).filter(
            or_(
                VocabExpression.vocab_body.contains(keyword),
                VocabExpression.explanation.contains(keyword)
            )
        ).all()
    
    def update(self, vocab_id: int, **kwargs) -> Optional[VocabExpression]:
        """更新词汇"""
        vocab = self.get_by_id(vocab_id)
        if vocab:
            for key, value in kwargs.items():
                if key == "source":
                    value = self._coerce_source(value)
                if hasattr(vocab, key):
                    setattr(vocab, key, value)
            self.session.commit()
            self.session.refresh(vocab)
        return vocab
    
    def delete(self, vocab_id: int) -> bool:
        """删除词汇"""
        vocab = self.get_by_id(vocab_id)
        if vocab:
            self.session.delete(vocab)
            self.session.commit()
            return True
        return False
    
    def create_example(self, *, vocab_id: int, text_id: int,
                      sentence_id: int, context_explanation: Optional[str] = None,
                      token_indices: Optional[list] = None) -> VocabExpressionExample:
        """创建词汇例句"""
        example = VocabExpressionExample(
            vocab_id=vocab_id,
            text_id=text_id,
            sentence_id=sentence_id,
            context_explanation=context_explanation,
            token_indices=token_indices or [],
        )
        self.session.add(example)
        self.session.commit()
        self.session.refresh(example)
        return example
