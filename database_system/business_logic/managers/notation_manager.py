"""
Notation 管理器 - 业务逻辑层
支持 VocabNotation 和 GrammarNotation 的统一管理
"""
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from ..data_access_layer import DataAccessLayer
from ..models import VocabNotation, GrammarNotation


class NotationManager:
    """Notation 统一管理器"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = DataAccessLayer(session)
    
    # ==================== VocabNotation 操作 ====================
    
    def create_vocab_notation(self, user_id: str, text_id: int, sentence_id: int, 
                             token_id: int, vocab_id: Optional[int] = None) -> Optional[VocabNotation]:
        """创建词汇标注"""
        try:
            # 检查是否已存在
            existing = self.dal.vocab_notation_crud.get_by_location(
                user_id, text_id, sentence_id, token_id
            )
            if existing:
                print(f"[INFO] [NotationManager] VocabNotation already exists: {text_id}:{sentence_id}:{token_id}")
                return existing
            
            notation = self.dal.vocab_notation_crud.create(
                user_id=user_id,
                text_id=text_id,
                sentence_id=sentence_id,
                token_id=token_id,
                vocab_id=vocab_id
            )
            print(f"[OK] [NotationManager] VocabNotation created: {text_id}:{sentence_id}:{token_id}")
            return notation
        except Exception as e:
            print(f"[ERROR] [NotationManager] Failed to create VocabNotation: {e}")
            return None
    
    def get_vocab_notations_for_text(self, text_id: int, 
                                     user_id: Optional[str] = None) -> List[VocabNotation]:
        """获取文章的所有词汇标注"""
        return self.dal.vocab_notation_crud.get_by_text(text_id, user_id)
    
    def get_vocab_notations_for_sentence(self, text_id: int, sentence_id: int, 
                                         user_id: Optional[str] = None) -> List[VocabNotation]:
        """获取句子的所有词汇标注"""
        return self.dal.vocab_notation_crud.get_by_sentence(text_id, sentence_id, user_id)
    
    def get_vocab_notation_keys(self, text_id: int, 
                                user_id: Optional[str] = None) -> Set[str]:
        """获取词汇标注的 key 集合（格式：text_id:sentence_id:token_id）"""
        notations = self.get_vocab_notations_for_text(text_id, user_id)
        return {f"{n.text_id}:{n.sentence_id}:{n.token_id}" for n in notations}
    
    def vocab_notation_exists(self, user_id: str, text_id: int, 
                             sentence_id: int, token_id: int) -> bool:
        """检查词汇标注是否存在"""
        return self.dal.vocab_notation_crud.exists(user_id, text_id, sentence_id, token_id)
    
    def delete_vocab_notation(self, user_id: str, text_id: int, 
                             sentence_id: int, token_id: int) -> bool:
        """删除词汇标注"""
        return self.dal.vocab_notation_crud.delete(user_id, text_id, sentence_id, token_id)
    
    # ==================== GrammarNotation 操作 ====================
    
    def create_grammar_notation(self, user_id: str, text_id: int, sentence_id: int, 
                               grammar_id: Optional[int] = None, 
                               marked_token_ids: Optional[List[int]] = None) -> Optional[GrammarNotation]:
        """创建语法标注"""
        try:
            # 检查是否已存在
            existing = self.dal.grammar_notation_crud.get_by_location(
                user_id, text_id, sentence_id
            )
            if existing:
                print(f"[INFO] [NotationManager] GrammarNotation already exists: {text_id}:{sentence_id}")
                return existing
            
            notation = self.dal.grammar_notation_crud.create(
                user_id=user_id,
                text_id=text_id,
                sentence_id=sentence_id,
                grammar_id=grammar_id,
                marked_token_ids=marked_token_ids or []
            )
            print(f"[OK] [NotationManager] GrammarNotation created: {text_id}:{sentence_id}")
            return notation
        except Exception as e:
            print(f"[ERROR] [NotationManager] Failed to create GrammarNotation: {e}")
            return None
    
    def get_grammar_notations_for_text(self, text_id: int, 
                                       user_id: Optional[str] = None) -> List[GrammarNotation]:
        """获取文章的所有语法标注"""
        return self.dal.grammar_notation_crud.get_by_text(text_id, user_id)
    
    def get_grammar_notation_for_sentence(self, text_id: int, sentence_id: int, 
                                          user_id: Optional[str] = None) -> Optional[GrammarNotation]:
        """获取句子的语法标注"""
        return self.dal.grammar_notation_crud.get_by_sentence(text_id, sentence_id, user_id)
    
    def get_grammar_notation_keys(self, text_id: int, 
                                  user_id: Optional[str] = None) -> Set[str]:
        """获取语法标注的 key 集合（格式：text_id:sentence_id）"""
        notations = self.get_grammar_notations_for_text(text_id, user_id)
        return {f"{n.text_id}:{n.sentence_id}" for n in notations}
    
    def grammar_notation_exists(self, user_id: str, text_id: int, 
                                sentence_id: int) -> bool:
        """检查语法标注是否存在"""
        return self.dal.grammar_notation_crud.exists(user_id, text_id, sentence_id)
    
    def delete_grammar_notation(self, user_id: str, text_id: int, 
                                sentence_id: int) -> bool:
        """删除语法标注"""
        return self.dal.grammar_notation_crud.delete(user_id, text_id, sentence_id)

