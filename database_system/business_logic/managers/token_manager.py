"""
词汇标记管理器 - 高级业务逻辑封装
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..data_access_layer import TokenDataAccessLayer
from ..models import Token


class TokenManager:
    """词汇标记管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = TokenDataAccessLayer(session)
    
    def create_token(self, text_id: int, sentence_id: int, token_body: str,
                    token_type: str, **kwargs) -> Token:
        """创建词汇标记"""
        return self.dal.create_token(text_id, sentence_id, token_body, token_type, **kwargs)
    
    def get_tokens_by_sentence(self, text_id: int, sentence_id: int) -> List[Token]:
        """获取句子的所有词汇标记"""
        return self.dal.get_tokens_by_sentence(text_id, sentence_id)
    
    def get_tokens_by_vocab(self, vocab_id: int) -> List[Token]:
        """获取关联到特定词汇的所有标记"""
        return self.dal.get_tokens_by_vocab(vocab_id)
    
    def link_token_to_vocab(self, token_id: int, vocab_id: int) -> bool:
        """将标记关联到词汇"""
        # 这里需要先获取token，然后更新其linked_vocab_id
        # 由于没有直接的get_by_id方法，这里简化处理
        try:
            token = self.session.query(Token).filter(Token.token_id == token_id).first()
            if token:
                token.linked_vocab_id = vocab_id
                self.session.commit()
                return True
        except Exception:
            pass
        return False
    
    def unlink_token_from_vocab(self, token_id: int) -> bool:
        """取消标记与词汇的关联"""
        try:
            token = self.session.query(Token).filter(Token.token_id == token_id).first()
            if token:
                token.linked_vocab_id = None
                self.session.commit()
                return True
        except Exception:
            pass
        return False
    
    def get_token_stats(self) -> Dict[str, int]:
        """获取标记统计"""
        # 这里需要直接查询数据库获取统计信息
        try:
            total_tokens = self.session.query(Token).count()
            linked_tokens = self.session.query(Token).filter(Token.linked_vocab_id.isnot(None)).count()
            unlinked_tokens = total_tokens - linked_tokens
            
            return {
                "total_tokens": total_tokens,
                "linked_tokens": linked_tokens,
                "unlinked_tokens": unlinked_tokens
            }
        except Exception:
            return {
                "total_tokens": 0,
                "linked_tokens": 0,
                "unlinked_tokens": 0
            }
