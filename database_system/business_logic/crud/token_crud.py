"""
词汇标记相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from ..models import Token


class TokenCRUD:
    """词汇标记 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, text_id: int, sentence_id: int, token_body: str,
               token_type: str, **kwargs) -> Token:
        """创建词汇标记"""
        token = Token(
            text_id=text_id,
            sentence_id=sentence_id,
            token_body=token_body,
            token_type=token_type,
            **kwargs
        )
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)
        return token
    
    def get_tokens_by_sentence(self, text_id: int, sentence_id: int) -> List[Token]:
        """获取句子的所有词汇标记"""
        return self.session.query(Token).filter(
            and_(Token.text_id == text_id, Token.sentence_id == sentence_id)
        ).all()
    
    def get_tokens_by_vocab(self, vocab_id: int) -> List[Token]:
        """获取关联到特定词汇的所有标记"""
        return self.session.query(Token).filter(
            Token.linked_vocab_id == vocab_id
        ).all()
