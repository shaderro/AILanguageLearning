"""
Notation CRUD 操作 - VocabNotation 和 GrammarNotation
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import VocabNotation, GrammarNotation


class VocabNotationCRUD:
    """词汇标注 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, text_id: int, sentence_id: int, 
               token_id: int, vocab_id: Optional[int] = None,
               word_token_id: Optional[int] = None) -> VocabNotation:
        """创建词汇标注"""
        notation = VocabNotation(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            token_id=token_id,
            vocab_id=vocab_id,
            word_token_id=word_token_id  # 新增：用于非空格语言的 word token 级别标注
        )
        self.session.add(notation)
        self.session.commit()
        self.session.refresh(notation)
        return notation
    
    def get_by_location(self, user_id: str, text_id: int, sentence_id: int, 
                        token_id: int) -> Optional[VocabNotation]:
        """根据位置获取词汇标注"""
        return self.session.query(VocabNotation).filter(
            VocabNotation.user_id == user_id,
            VocabNotation.text_id == text_id,
            VocabNotation.sentence_id == sentence_id,
            VocabNotation.token_id == token_id
        ).first()
    
    def get_by_text(self, text_id: int, user_id = None) -> List[VocabNotation]:
        """获取文章的所有词汇标注"""
        print(f"[VocabNotationCRUD] get_by_text called: text_id={text_id}, user_id={user_id}, user_id_type={type(user_id)}")
        query = self.session.query(VocabNotation).filter(
            VocabNotation.text_id == text_id
        )
        if user_id is not None:
            print(f"[VocabNotationCRUD] Adding user_id filter: {user_id}")
            query = query.filter(VocabNotation.user_id == user_id)
        
        results = query.all()
        print(f"[VocabNotationCRUD] Found {len(results)} notations")
        return results
    
    def get_by_sentence(self, text_id: int, sentence_id: int, 
                        user_id: Optional[str] = None) -> List[VocabNotation]:
        """获取句子的所有词汇标注"""
        query = self.session.query(VocabNotation).filter(
            VocabNotation.text_id == text_id,
            VocabNotation.sentence_id == sentence_id
        )
        if user_id:
            query = query.filter(VocabNotation.user_id == user_id)
        return query.all()
    
    def exists(self, user_id: str, text_id: int, sentence_id: int, 
               token_id: int) -> bool:
        """检查标注是否存在"""
        return self.session.query(VocabNotation).filter(
            VocabNotation.user_id == user_id,
            VocabNotation.text_id == text_id,
            VocabNotation.sentence_id == sentence_id,
            VocabNotation.token_id == token_id
        ).count() > 0
    
    def delete(self, user_id: str, text_id: int, sentence_id: int, 
               token_id: int) -> bool:
        """删除词汇标注"""
        notation = self.get_by_location(user_id, text_id, sentence_id, token_id)
        if not notation:
            return False
        
        self.session.delete(notation)
        self.session.commit()
        return True


class GrammarNotationCRUD:
    """语法标注 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, text_id: int, sentence_id: int, 
               grammar_id: Optional[int] = None, 
               marked_token_ids: Optional[List[int]] = None) -> GrammarNotation:
        """创建语法标注"""
        notation = GrammarNotation(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            grammar_id=grammar_id,
            marked_token_ids=marked_token_ids or []
        )
        self.session.add(notation)
        self.session.commit()
        self.session.refresh(notation)
        return notation
    
    def get_by_location(self, user_id: str, text_id: int, 
                        sentence_id: int) -> Optional[GrammarNotation]:
        """根据位置获取语法标注"""
        return self.session.query(GrammarNotation).filter(
            GrammarNotation.user_id == user_id,
            GrammarNotation.text_id == text_id,
            GrammarNotation.sentence_id == sentence_id
        ).first()
    
    def get_by_text(self, text_id: int, user_id = None) -> List[GrammarNotation]:
        """获取文章的所有语法标注"""
        query = self.session.query(GrammarNotation).filter(
            GrammarNotation.text_id == text_id
        )
        if user_id is not None:
            query = query.filter(GrammarNotation.user_id == user_id)
        return query.all()
    
    def get_by_sentence(self, text_id: int, sentence_id: int, 
                        user_id: Optional[str] = None) -> List[GrammarNotation]:
        """获取句子的所有语法标注（支持多个语法知识点）"""
        query = self.session.query(GrammarNotation).filter(
            GrammarNotation.text_id == text_id,
            GrammarNotation.sentence_id == sentence_id
        )
        if user_id:
            query = query.filter(GrammarNotation.user_id == user_id)
        return query.all()  # 🔧 修复：返回所有匹配的 notations，而不是只返回第一个
    
    def exists(self, user_id: str, text_id: int, sentence_id: int, grammar_id: Optional[int] = None) -> bool:
        """检查标注是否存在（支持按 grammar_id 检查，以支持同一句子有多个语法知识点）"""
        query = self.session.query(GrammarNotation).filter(
            GrammarNotation.user_id == user_id,
            GrammarNotation.text_id == text_id,
            GrammarNotation.sentence_id == sentence_id
        )
        # 🔧 如果提供了 grammar_id，也加入过滤条件（支持多个语法知识点）
        if grammar_id is not None:
            query = query.filter(GrammarNotation.grammar_id == grammar_id)
        return query.count() > 0
    
    def delete(self, user_id: str, text_id: int, sentence_id: int) -> bool:
        """删除语法标注"""
        notation = self.get_by_location(user_id, text_id, sentence_id)
        if not notation:
            return False
        
        self.session.delete(notation)
        self.session.commit()
        return True

