"""
词汇管理器 - 高级业务逻辑封装
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..data_access_layer import VocabDataAccessLayer
from ..models import VocabExpression


class VocabManager:
    """词汇管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = VocabDataAccessLayer(session)
    
    def get_vocab(self, vocab_id: int) -> Optional[VocabExpression]:
        """获取词汇"""
        return self.dal.get_vocab(vocab_id)
    
    def find_vocab_by_body(self, vocab_body: str) -> Optional[VocabExpression]:
        """根据内容查找词汇"""
        return self.dal.find_vocab_by_body(vocab_body)
    
    def list_vocabs(self, skip: int = 0, limit: int = 100, starred_only: bool = False) -> List[VocabExpression]:
        """列出词汇"""
        if starred_only:
            return self.dal.get_starred_vocabs()
        return self.dal.list_all_vocabs(skip, limit)
    
    def add_vocab(self, vocab_body: str, explanation: str, 
                  source: str = "auto", is_starred: bool = False, user_id: int = None,
                  language: str = None) -> VocabExpression:
        """添加词汇"""
        return self.dal.add_vocab(vocab_body, explanation, source, is_starred, user_id, language)
    
    def search_vocabs(self, keyword: str) -> List[VocabExpression]:
        """搜索词汇"""
        return self.dal.search_vocabs(keyword)
    
    def toggle_star(self, vocab_id: int) -> bool:
        """切换收藏状态"""
        vocab = self.get_vocab(vocab_id)
        if vocab:
            new_starred = not vocab.is_starred
            self.dal.update_vocab(vocab_id, is_starred=new_starred)
            return new_starred
        return False
    
    def get_vocab_with_examples(self, vocab_id: int) -> Optional[Dict[str, Any]]:
        """获取词汇及其例句"""
        return self.dal.get_vocab_with_examples(vocab_id)
    
    def update_vocab(self, vocab_id: int, **kwargs) -> Optional[VocabExpression]:
        """更新词汇"""
        return self.dal.update_vocab(vocab_id, **kwargs)
    
    def delete_vocab(self, vocab_id: int) -> bool:
        """删除词汇"""
        return self.dal.delete_vocab(vocab_id)
    
    def get_vocab_stats(self) -> Dict[str, int]:
        """获取词汇统计"""
        vocabs = self.dal.list_all_vocabs(0, 10000)  # 获取所有用于统计
        total = len(vocabs)
        starred = len([v for v in vocabs if v.is_starred])
        auto = len([v for v in vocabs if v.source.value == "auto"])
        manual = len([v for v in vocabs if v.source.value == "manual"])
        
        return {
            "total": total,
            "starred": starred,
            "auto": auto,
            "manual": manual
        }
    
    def add_vocab_example(self, vocab_id: int, text_id: int, 
                         sentence_id: int, context_explanation: str,
                         token_indices: Optional[List[int]] = None):
        """
        添加词汇例句
        
        参数:
            vocab_id: 词汇ID
            text_id: 文章ID
            sentence_id: 句子ID
            context_explanation: 上下文解释
            token_indices: 关联的token索引列表
            
        返回:
            VocabExpressionExample: 新创建的例句
        """
        from ..crud import VocabCRUD
        vocab_crud = VocabCRUD(self.session)
        return vocab_crud.create_example(
            vocab_id=vocab_id,
            text_id=text_id,
            sentence_id=sentence_id,
            context_explanation=context_explanation,
            token_indices=token_indices or []
        )
