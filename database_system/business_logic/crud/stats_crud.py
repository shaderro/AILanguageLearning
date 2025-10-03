"""
统计查询相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import Dict
from ..models import VocabExpression, GrammarRule, OriginalText, Sentence, AskedToken, SourceType


class StatsCRUD:
    """统计查询 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_vocab_stats(self) -> Dict:
        """获取词汇统计信息"""
        total_vocabs = self.session.query(VocabExpression).count()
        starred_vocabs = self.session.query(VocabExpression).filter(
            VocabExpression.is_starred == True
        ).count()
        auto_vocabs = self.session.query(VocabExpression).filter(
            VocabExpression.source == SourceType.AUTO
        ).count()
        manual_vocabs = self.session.query(VocabExpression).filter(
            VocabExpression.source == SourceType.MANUAL
        ).count()
        
        return {
            "total": total_vocabs,
            "starred": starred_vocabs,
            "auto": auto_vocabs,
            "manual": manual_vocabs
        }
    
    def get_grammar_stats(self) -> Dict:
        """获取语法规则统计信息"""
        total_rules = self.session.query(GrammarRule).count()
        starred_rules = self.session.query(GrammarRule).filter(
            GrammarRule.is_starred == True
        ).count()
        auto_rules = self.session.query(GrammarRule).filter(
            GrammarRule.source == SourceType.AUTO
        ).count()
        manual_rules = self.session.query(GrammarRule).filter(
            GrammarRule.source == SourceType.MANUAL
        ).count()
        
        return {
            "total": total_rules,
            "starred": starred_rules,
            "auto": auto_rules,
            "manual": manual_rules
        }
    
    def get_learning_progress(self) -> Dict:
        """获取学习进度统计"""
        vocab_stats = self.get_vocab_stats()
        grammar_stats = self.get_grammar_stats()
        
        total_texts = self.session.query(OriginalText).count()
        total_sentences = self.session.query(Sentence).count()
        
        return {
            "vocab": vocab_stats,
            "grammar": grammar_stats,
            "texts": total_texts,
            "sentences": total_sentences,
        }
    
    def get_asked_token_stats(self) -> Dict:
        """获取已提问token统计信息"""
        total_asked = self.session.query(AskedToken).count()
        unique_users = self.session.query(AskedToken.user_id).distinct().count()
        unique_articles = self.session.query(AskedToken.text_id).distinct().count()
        
        return {
            "total_asked_tokens": total_asked,
            "unique_users": unique_users,
            "unique_articles": unique_articles
        }
