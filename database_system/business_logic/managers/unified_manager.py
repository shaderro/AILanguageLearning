"""
统一数据管理器 - 仿照 DatabaseManager 模式
"""
from sqlalchemy.orm import Session
from .vocab_manager import VocabManager
from .grammar_manager import GrammarManager
from .text_manager import TextManager
from .token_manager import TokenManager
from .asked_token_manager import AskedTokenManager
from .stats_manager import StatsManager


class UnifiedDataManager:
    """统一数据管理器 - 提供所有功能的统一入口"""
    
    def __init__(self, session: Session):
        self.session = session
        self.vocab = VocabManager(session)
        self.grammar = GrammarManager(session)
        self.text = TextManager(session)
        self.token = TokenManager(session)
        self.asked_token = AskedTokenManager(session)
        self.stats = StatsManager(session)
    
    def close(self):
        """关闭会话"""
        self.session.close()
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()
    
    def get_session(self) -> Session:
        """获取当前会话"""
        return self.session
