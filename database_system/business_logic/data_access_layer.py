"""
数据访问层 (DAL) - 统一管理器模式，支持 JSON → DB 逐步迁移
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import VocabExpression, GrammarRule, User
from .crud import (
    VocabCRUD, GrammarCRUD, TextCRUD, TokenCRUD, 
    AskedTokenCRUD, StatsCRUD, UserCRUD
)
from .crud.notation_crud import VocabNotationCRUD, GrammarNotationCRUD


class VocabDataAccessLayer:
    """词汇数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = VocabCRUD(session)
    
    def get_vocab(self, vocab_id: int) -> Optional[VocabExpression]:
        """根据ID获取词汇"""
        return self._crud.get_by_id(vocab_id)
    
    def find_vocab_by_body(self, vocab_body: str) -> Optional[VocabExpression]:
        """根据词汇内容查找"""
        return self._crud.get_by_body(vocab_body)
    
    def list_all_vocabs(self, skip: int = 0, limit: int = 100) -> List[VocabExpression]:
        """列出所有词汇"""
        return self._crud.get_all(skip, limit)
    
    def add_vocab(self, vocab_body: str, explanation: str, 
                  source: str = "auto", is_starred: bool = False, user_id: int = None,
                  language: str = None) -> VocabExpression:
        """添加新词汇（如果已存在则返回现有记录）"""
        # 🔧 使用 get_or_create 逻辑：如果已存在则返回，不存在则创建
        return self._crud.get_or_create(vocab_body, explanation, source, is_starred, user_id, language)
    
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
    
    def search_vocabs(self, keyword: str) -> List[VocabExpression]:
        """搜索词汇"""
        return self._crud.search(keyword)
    
    def get_starred_vocabs(self) -> List[VocabExpression]:
        """获取收藏的词汇"""
        return self._crud.get_starred()
    
    def update_vocab(self, vocab_id: int, **kwargs) -> Optional[VocabExpression]:
        """更新词汇"""
        return self._crud.update(vocab_id, **kwargs)
    
    def delete_vocab(self, vocab_id: int) -> bool:
        """删除词汇"""
        return self._crud.delete(vocab_id)


class GrammarDataAccessLayer:
    """语法规则数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = GrammarCRUD(session)
    
    def get_grammar(self, rule_id: int) -> Optional[GrammarRule]:
        """根据ID获取语法规则"""
        return self._crud.get_by_id(rule_id)
    
    def find_grammar_by_name(self, rule_name: str) -> Optional[GrammarRule]:
        """根据名称查找语法规则"""
        return self._crud.get_by_name(rule_name)
    
    def list_all_grammar_rules(self, skip: int = 0, limit: int = 100) -> List[GrammarRule]:
        """列出所有语法规则"""
        return self._crud.get_all(skip, limit)
    
    def add_grammar_rule(self, rule_name: str, rule_summary: str,
                        source: str = "auto", is_starred: bool = False, user_id: int = None,
                        language: str = None) -> GrammarRule:
        """添加新语法规则（如果已存在则返回现有记录）"""
        # 🔧 使用 get_or_create 逻辑：如果已存在则返回，不存在则创建
        return self._crud.get_or_create(rule_name, rule_summary, source, is_starred, user_id, language)
    
    def search_grammar_rules(self, keyword: str) -> List[GrammarRule]:
        """搜索语法规则"""
        return self._crud.search(keyword)
    
    def get_starred_grammar_rules(self) -> List[GrammarRule]:
        """获取收藏的语法规则"""
        return self._crud.get_starred()
    
    def update_grammar_rule(self, rule_id: int, **kwargs) -> Optional[GrammarRule]:
        """更新语法规则"""
        return self._crud.update(rule_id, **kwargs)
    
    def delete_grammar_rule(self, rule_id: int) -> bool:
        """删除语法规则"""
        return self._crud.delete(rule_id)


class TextDataAccessLayer:
    """文章数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = TextCRUD(session)
    
    def create_text(self, text_title: str, user_id: int = None, language: str = None, processing_status: str = 'completed'):
        """创建文章"""
        return self._crud.create_text(text_title, user_id, language, processing_status)
    
    def get_text_by_id(self, text_id: int):
        """根据ID获取文章"""
        return self._crud.get_text_by_id(text_id)
    
    def get_all_texts(self, user_id: int = None):
        """获取所有文章（可选用户过滤）"""
        return self._crud.get_all_texts(user_id=user_id)
    
    def search_texts(self, keyword: str, user_id: int = None):
        """搜索文章（可选用户过滤）"""
        return self._crud.search_texts(keyword, user_id=user_id)
    
    def create_sentence(
        self,
        text_id: int,
        sentence_id: int,
        sentence_body: str,
        difficulty_level: Optional[str] = None,
        paragraph_id: Optional[int] = None,
        is_new_paragraph: Optional[bool] = None,
    ):
        """创建句子（支持段落信息）"""
        return self._crud.create_sentence(
            text_id,
            sentence_id,
            sentence_body,
            difficulty_level=difficulty_level,
            paragraph_id=paragraph_id,
            is_new_paragraph=is_new_paragraph,
        )
    
    def get_sentences_by_text(self, text_id: int):
        """获取文章的所有句子"""
        return self._crud.get_sentences_by_text(text_id)
    
    def get_sentence_by_id(self, text_id: int, sentence_id: int):
        """根据ID获取句子"""
        return self._crud.get_sentence_by_id(text_id, sentence_id)
    
    def update_text(self, text_id: int, text_title: str = None, language: str = None, processing_status: str = None):
        """更新文章"""
        return self._crud.update_text(text_id, text_title, language, processing_status)
    
    def delete_text(self, text_id: int) -> bool:
        """删除文章"""
        return self._crud.delete_text(text_id)


class TokenDataAccessLayer:
    """词汇标记数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = TokenCRUD(session)
    
    def create_token(self, text_id: int, sentence_id: int, token_body: str,
                    token_type: str, **kwargs):
        """创建词汇标记"""
        return self._crud.create(text_id, sentence_id, token_body, token_type, **kwargs)
    
    def get_tokens_by_sentence(self, text_id: int, sentence_id: int):
        """获取句子的所有词汇标记"""
        return self._crud.get_tokens_by_sentence(text_id, sentence_id)
    
    def get_tokens_by_vocab(self, vocab_id: int):
        """获取关联到特定词汇的所有标记"""
        return self._crud.get_tokens_by_vocab(vocab_id)


class AskedTokenDataAccessLayer:
    """已提问Token数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = AskedTokenCRUD(session)
    
    def create_asked_token(self, user_id: str, text_id: int, 
                          sentence_id: int, sentence_token_id: Optional[int] = None,
                          type: str = 'token'):
        """
        创建已提问token记录
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            type: 标记类型，'token' 或 'sentence'，默认 'token'
        """
        return self._crud.create(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def get_asked_token(self, user_id: str, text_id: int, 
                        sentence_id: int, sentence_token_id: Optional[int] = None,
                        type: Optional[str] = None):
        """
        获取指定的已提问token记录
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            type: 标记类型（可选）
        """
        return self._crud.get(user_id, text_id, sentence_id, sentence_token_id, type)
    
    def get_asked_tokens_for_article(self, text_id: int):
        """获取指定文章的所有已提问token记录"""
        return self._crud.get_for_article(text_id)
    
    def get_asked_tokens_for_user_article(self, user_id: str, text_id: int):
        """获取指定用户在指定文章的已提问token记录"""
        return self._crud.get_for_user_article(user_id, text_id)
    
    def delete_asked_token(self, user_id: str, text_id: int, 
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
        return self._crud.delete(user_id, text_id, sentence_id, sentence_token_id, type)


class StatsDataAccessLayer:
    """统计查询数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = StatsCRUD(session)
    
    def get_vocab_stats(self) -> Dict:
        """获取词汇统计信息"""
        return self._crud.get_vocab_stats()
    
    def get_grammar_stats(self) -> Dict:
        """获取语法规则统计信息"""
        return self._crud.get_grammar_stats()
    
    def get_learning_progress(self) -> Dict:
        """获取学习进度统计"""
        return self._crud.get_learning_progress()
    
    def get_asked_token_stats(self) -> Dict:
        """获取已提问token统计信息"""
        return self._crud.get_asked_token_stats()


class DataAccessManager:
    """数据访问管理器 - 统一入口，仿照 DatabaseManager 模式"""
    
    def __init__(self, session: Session):
        self.session = session
        self.vocab = VocabDataAccessLayer(session)
        self.grammar = GrammarDataAccessLayer(session)
        self.text = TextDataAccessLayer(session)
        self.token = TokenDataAccessLayer(session)
        self.asked_token = AskedTokenDataAccessLayer(session)
        self.stats = StatsDataAccessLayer(session)
        # 新增：Notation CRUD
        self.vocab_notation_crud = VocabNotationCRUD(session)
        self.grammar_notation_crud = GrammarNotationCRUD(session)
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()


class UserDataAccessLayer:
    """用户数据访问层"""
    
    def __init__(self, session: Session):
        self.session = session
        self._crud = UserCRUD(session)
    
    def get_user(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self._crud.get_by_id(user_id)
    
    def create_user(self, password: str) -> User:
        """创建新用户"""
        return self._crud.create(password)
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """列出所有用户"""
        return self._crud.get_all(skip, limit)
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        return self._crud.update(user_id, **kwargs)
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        return self._crud.delete(user_id)