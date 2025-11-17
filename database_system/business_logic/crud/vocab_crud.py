"""
词汇相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models import VocabExpression, VocabExpressionExample, SourceType, LearnStatus


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
    
    def _coerce_learn_status(self, value) -> LearnStatus:
        """转换学习状态"""
        if isinstance(value, LearnStatus):
            return value
        if value is None:
            return LearnStatus.NOT_MASTERED
        if isinstance(value, str):
            if value == 'mastered':
                return LearnStatus.MASTERED
            elif value == 'not_mastered':
                return LearnStatus.NOT_MASTERED
        try:
            return LearnStatus(value)
        except Exception:
            return LearnStatus.NOT_MASTERED
    
    def create(self, vocab_body: str, explanation: str, 
               source: str = "auto", is_starred: bool = False, user_id: int = None, 
               language: str = None) -> VocabExpression:
        """创建词汇"""
        vocab = VocabExpression(
            vocab_body=vocab_body,
            explanation=explanation,
            language=language,
            source=self._coerce_source(source),
            is_starred=is_starred,
            user_id=user_id
        )
        self.session.add(vocab)
        self.session.commit()
        self.session.refresh(vocab)
        return vocab
    
    def get_or_create(self, vocab_body: str, explanation: str,
                      source: str = "auto", is_starred: bool = False, user_id: int = None,
                      language: str = None) -> VocabExpression:
        """获取或创建词汇（如果已存在则返回现有记录，不存在则创建）"""
        # 🔧 如果user_id为None，直接创建（向后兼容）
        if user_id is None:
            return self.create(vocab_body, explanation, source, is_starred, user_id, language)
        
        # 🔧 查找已存在的词汇（按user_id和vocab_body）
        existing = self.session.query(VocabExpression).filter(
            VocabExpression.vocab_body == vocab_body,
            VocabExpression.user_id == user_id
        ).first()
        if existing:
            # 🔧 如果已存在，更新language字段（如果提供了language且现有记录的language为None）
            if language and existing.language is None:
                existing.language = language
                self.session.commit()
                self.session.refresh(existing)
                print(f"🔍 [DEBUG] 更新已存在词汇的language: {vocab_body} -> {language}")
            return existing
        # 🔧 不存在则创建新词汇
        return self.create(vocab_body, explanation, source, is_starred, user_id, language)
    
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
                elif key == "learn_status":
                    value = self._coerce_learn_status(value)
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
        """
        创建词汇例句（带查重逻辑，避免重复创建）
        
        如果已存在相同的 example（基于 vocab_id, text_id, sentence_id, token_indices），
        则返回现有的 example，否则创建新的。
        """
        # 🔧 查重：检查是否已存在相同的 example
        # 先基于 (vocab_id, text_id, sentence_id) 查询
        existing_examples = self.session.query(VocabExpressionExample).filter(
            VocabExpressionExample.vocab_id == vocab_id,
            VocabExpressionExample.text_id == text_id,
            VocabExpressionExample.sentence_id == sentence_id
        ).all()
        
        # 如果有匹配的记录，比较 token_indices
        normalized_token_indices = sorted(token_indices or [])
        for existing in existing_examples:
            existing_indices = sorted(existing.token_indices or [])
            # 如果 token_indices 相同（或都为空），认为是重复的
            if existing_indices == normalized_token_indices:
                print(f"🔍 [VocabCRUD] 发现已存在的 example: vocab_id={vocab_id}, text_id={text_id}, sentence_id={sentence_id}, token_indices={normalized_token_indices}")
                return existing
        
        # 如果没有找到重复的，创建新的
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
        print(f"✅ [VocabCRUD] 创建新 example: vocab_id={vocab_id}, text_id={text_id}, sentence_id={sentence_id}, token_indices={normalized_token_indices}")
        return example
