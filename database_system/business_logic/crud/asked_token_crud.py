"""
已提问Token相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from ..models import AskedToken


class AskedTokenCRUD:
    """已提问Token CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, text_id: int, 
               sentence_id: int, sentence_token_id: int) -> AskedToken:
        """创建已提问token记录"""
        asked_token = AskedToken(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=sentence_token_id
        )
        self.session.add(asked_token)
        self.session.commit()
        self.session.refresh(asked_token)
        return asked_token
    
    def get(self, user_id: str, text_id: int, 
            sentence_id: int, sentence_token_id: int) -> Optional[AskedToken]:
        """获取指定的已提问token记录"""
        return self.session.query(AskedToken).filter(
            and_(
                AskedToken.user_id == user_id,
                AskedToken.text_id == text_id,
                AskedToken.sentence_id == sentence_id,
                AskedToken.sentence_token_id == sentence_token_id
            )
        ).first()
    
    def get_for_article(self, text_id: int) -> List[AskedToken]:
        """获取指定文章的所有已提问token记录"""
        return self.session.query(AskedToken).filter(
            AskedToken.text_id == text_id
        ).all()
    
    def get_for_user_article(self, user_id: str, text_id: int) -> List[AskedToken]:
        """获取指定用户在指定文章的已提问token记录"""
        return self.session.query(AskedToken).filter(
            and_(
                AskedToken.user_id == user_id,
                AskedToken.text_id == text_id
            )
        ).all()
    
    def delete(self, user_id: str, text_id: int, 
               sentence_id: int, sentence_token_id: int) -> bool:
        """删除已提问token记录"""
        asked_token = self.get(user_id, text_id, sentence_id, sentence_token_id)
        if asked_token:
            self.session.delete(asked_token)
            self.session.commit()
            return True
        return False
