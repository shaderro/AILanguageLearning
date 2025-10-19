"""
已提问Token管理器 - 高级业务逻辑封装
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..data_access_layer import AskedTokenDataAccessLayer
from ..models import AskedToken


class AskedTokenManager:
    """已提问Token管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = AskedTokenDataAccessLayer(session)
    
    def mark_token_as_asked(self, user_id: str, text_id: int, 
                           sentence_id: int, sentence_token_id: Optional[int] = None,
                           type: str = 'token') -> AskedToken:
        """
        标记token或sentence为已提问
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            type: 标记类型，'token' 或 'sentence'，默认 'token'
        """
        return self.dal.create_asked_token(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def is_token_asked(self, user_id: str, text_id: int, 
                      sentence_id: int, sentence_token_id: Optional[int] = None,
                      type: Optional[str] = None) -> bool:
        """
        检查token或sentence是否已被提问
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            type: 标记类型（可选）
        """
        return self.dal.get_asked_token(user_id, text_id, sentence_id, sentence_token_id, type) is not None
    
    def get_asked_tokens_for_article(self, text_id: int) -> List[AskedToken]:
        """获取文章的所有已提问token"""
        return self.dal.get_asked_tokens_for_article(text_id)
    
    def get_asked_tokens_for_user_article(self, user_id: str, text_id: int) -> List[AskedToken]:
        """获取用户在文章中的已提问token"""
        return self.dal.get_asked_tokens_for_user_article(user_id, text_id)
    
    def unmark_token_as_asked(self, user_id: str, text_id: int, 
                             sentence_id: int, sentence_token_id: Optional[int] = None,
                             type: Optional[str] = None) -> bool:
        """
        取消标记token或sentence为已提问
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            type: 标记类型（可选）
        """
        return self.dal.delete_asked_token(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """获取用户学习进度"""
        # 获取用户的所有已提问token
        asked_tokens = self.session.query(AskedToken).filter(
            AskedToken.user_id == user_id
        ).all()
        
        # 按文章分组统计
        article_stats = {}
        for token in asked_tokens:
            text_id = token.text_id
            if text_id not in article_stats:
                article_stats[text_id] = 0
            article_stats[text_id] += 1
        
        return {
            "user_id": user_id,
            "total_asked_tokens": len(asked_tokens),
            "articles_processed": len(article_stats),
            "article_stats": article_stats
        }
    
    def get_asked_token_stats(self) -> Dict[str, int]:
        """获取已提问token统计"""
        return self.dal.get_asked_token_stats()
