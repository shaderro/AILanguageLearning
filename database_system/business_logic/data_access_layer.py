"""
数据访问层 (DAL) - 统一接口，支持 JSON → DB 逐步迁移
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import VocabExpression, VocabExpressionExample, GrammarRule
from .crud import (
    get_vocab_by_id, get_vocab_by_body, get_all_vocabs, create_vocab,
    get_grammar_rule_by_id, get_grammar_rule_by_name, get_all_grammar_rules,
    create_vocab_example
)

class VocabDataAccessLayer:
    """词汇数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_vocab(self, vocab_id: int) -> Optional[VocabExpression]:
        """根据ID获取词汇"""
        return get_vocab_by_id(self.session, vocab_id)
    
    def find_vocab_by_body(self, vocab_body: str) -> Optional[VocabExpression]:
        """根据词汇内容查找"""
        return get_vocab_by_body(self.session, vocab_body)
    
    def list_all_vocabs(self, skip: int = 0, limit: int = 100) -> List[VocabExpression]:
        """列出所有词汇"""
        return get_all_vocabs(self.session, skip, limit)
    
    def add_vocab(self, vocab_body: str, explanation: str, 
                  source: str = "auto", is_starred: bool = False) -> VocabExpression:
        """添加新词汇"""
        return create_vocab(self.session, vocab_body, explanation, source, is_starred)
    
    def get_vocab_with_examples(self, vocab_id: int) -> Optional[Dict[str, Any]]:
        """获取词汇及其例句"""
        vocab = self.get_vocab(vocab_id)
        if not vocab:
            return None
        
        return {
            "vocab_id": vocab.vocab_id,
            "vocab_body": vocab.vocab_body,
            "explanation": vocab.explanation,
            "source": vocab.source.value,
            "is_starred": vocab.is_starred,
            "examples": [
                {
                    "example_id": ex.example_id,
                    "text_id": ex.text_id,
                    "sentence_id": ex.sentence_id,
                    "context_explanation": ex.context_explanation,
                    "token_indices": ex.token_indices
                }
                for ex in vocab.examples
            ]
        }


class GrammarDataAccessLayer:
    """语法规则数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_grammar(self, rule_id: int) -> Optional[GrammarRule]:
        return get_grammar_rule_by_id(self.session, rule_id)
    
    def find_grammar_by_name(self, rule_name: str) -> Optional[GrammarRule]:
        return get_grammar_rule_by_name(self.session, rule_name)
    
    def list_all_grammar_rules(self, skip: int = 0, limit: int = 100) -> List[GrammarRule]:
        return get_all_grammar_rules(self.session, skip, limit)


class DataAccessManager:
    """数据访问管理器 - 统一入口"""
    
    def __init__(self, session: Session):
        self.session = session
        self.vocab = VocabDataAccessLayer(session)
        self.grammar = GrammarDataAccessLayer(session)
    
    def close(self):
        self.session.close() 