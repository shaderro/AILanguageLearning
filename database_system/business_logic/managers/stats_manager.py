"""
统计管理器 - 高级业务逻辑封装
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..data_access_layer import StatsDataAccessLayer


class StatsManager:
    """统计管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = StatsDataAccessLayer(session)
    
    def get_vocab_stats(self) -> Dict[str, Any]:
        """获取词汇统计"""
        return self.dal.get_vocab_stats()
    
    def get_grammar_stats(self) -> Dict[str, Any]:
        """获取语法规则统计"""
        return self.dal.get_grammar_stats()
    
    def get_learning_progress(self) -> Dict[str, Any]:
        """获取学习进度统计"""
        return self.dal.get_learning_progress()
    
    def get_asked_token_stats(self) -> Dict[str, Any]:
        """获取已提问token统计"""
        return self.dal.get_asked_token_stats()
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        vocab_stats = self.get_vocab_stats()
        grammar_stats = self.get_grammar_stats()
        asked_token_stats = self.get_asked_token_stats()
        learning_progress = self.get_learning_progress()
        
        return {
            "vocabulary": vocab_stats,
            "grammar": grammar_stats,
            "asked_tokens": asked_token_stats,
            "learning_progress": learning_progress,
            "summary": {
                "total_vocab": vocab_stats.get("total", 0),
                "total_grammar": grammar_stats.get("total", 0),
                "total_texts": learning_progress.get("texts", 0),
                "total_sentences": learning_progress.get("sentences", 0),
                "total_asked_tokens": asked_token_stats.get("total_asked_tokens", 0)
            }
        }
