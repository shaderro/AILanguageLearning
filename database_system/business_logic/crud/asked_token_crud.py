"""
已提问Token相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models import AskedToken, AskedTokenType


class AskedTokenCRUD:
    """已提问Token CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, text_id: int, 
               sentence_id: int, sentence_token_id: Optional[int] = None,
               type: str = 'token') -> AskedToken:
        """
        创建已提问token记录
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（当 type='token' 时必须提供）
            type: 标记类型 'token' 或 'sentence'，默认 'token'
        
        注意：向后兼容逻辑
        - 如果 type 未指定但 sentence_token_id 不为空，则默认 type='token'
        - 如果 type='sentence'，sentence_token_id 可以为 None
        """
        # 向后兼容：如果 type 未明确指定且 sentence_token_id 不为空，默认为 'token'
        if type is None and sentence_token_id is not None:
            type = 'token'
        
        # 转换字符串类型为枚举
        asked_type = AskedTokenType.TOKEN if type == 'token' else AskedTokenType.SENTENCE
        
        asked_token = AskedToken(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=sentence_token_id,
            type=asked_type
        )
        self.session.add(asked_token)
        self.session.commit()
        self.session.refresh(asked_token)
        return asked_token
    
    def get(self, user_id: str, text_id: int, 
            sentence_id: int, sentence_token_id: Optional[int] = None,
            type: Optional[str] = None) -> Optional[AskedToken]:
        """
        获取指定的已提问token记录
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选，查询 token 类型时需要）
            type: 标记类型（可选，'token' 或 'sentence'）
        """
        conditions = [
            AskedToken.user_id == user_id,
            AskedToken.text_id == text_id,
            AskedToken.sentence_id == sentence_id
        ]
        
        if sentence_token_id is not None:
            conditions.append(AskedToken.sentence_token_id == sentence_token_id)
        
        if type is not None:
            asked_type = AskedTokenType.TOKEN if type == 'token' else AskedTokenType.SENTENCE
            conditions.append(AskedToken.type == asked_type)
        
        return self.session.query(AskedToken).filter(and_(*conditions)).first()
    
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
               sentence_id: int, sentence_token_id: Optional[int] = None,
               type: Optional[str] = None) -> bool:
        """
        删除已提问token记录
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            type: 标记类型（可选）
        """
        asked_token = self.get(user_id, text_id, sentence_id, sentence_token_id, type)
        if asked_token:
            self.session.delete(asked_token)
            self.session.commit()
            return True
        return False
