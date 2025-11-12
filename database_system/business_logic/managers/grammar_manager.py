"""
语法规则管理器 - 高级业务逻辑封装
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..data_access_layer import GrammarDataAccessLayer
from ..models import GrammarRule


class GrammarManager:
    """语法规则管理器 - 提供高级业务逻辑"""
    
    def __init__(self, session: Session):
        self.session = session
        self.dal = GrammarDataAccessLayer(session)
    
    def get_grammar_rule(self, rule_id: int) -> Optional[GrammarRule]:
        """获取语法规则"""
        return self.dal.get_grammar(rule_id)
    
    def find_grammar_by_name(self, rule_name: str) -> Optional[GrammarRule]:
        """根据名称查找语法规则"""
        return self.dal.find_grammar_by_name(rule_name)
    
    def list_grammar_rules(self, skip: int = 0, limit: int = 100, starred_only: bool = False) -> List[GrammarRule]:
        """列出语法规则"""
        if starred_only:
            return self.dal.get_starred_grammar_rules()
        return self.dal.list_all_grammar_rules(skip, limit)
    
    def add_grammar_rule(self, rule_name: str, rule_summary: str,
                        source: str = "auto", is_starred: bool = False, user_id: int = None) -> GrammarRule:
        """添加语法规则"""
        return self.dal.add_grammar_rule(rule_name, rule_summary, source, is_starred, user_id)
    
    def search_grammar_rules(self, keyword: str) -> List[GrammarRule]:
        """搜索语法规则"""
        return self.dal.search_grammar_rules(keyword)
    
    def toggle_star(self, rule_id: int) -> bool:
        """切换收藏状态"""
        rule = self.get_grammar_rule(rule_id)
        if rule:
            new_starred = not rule.is_starred
            self.dal.update_grammar_rule(rule_id, is_starred=new_starred)
            return new_starred
        return False
    
    def update_grammar_rule(self, rule_id: int, **kwargs) -> Optional[GrammarRule]:
        """更新语法规则"""
        return self.dal.update_grammar_rule(rule_id, **kwargs)
    
    def delete_grammar_rule(self, rule_id: int) -> bool:
        """删除语法规则"""
        return self.dal.delete_grammar_rule(rule_id)
    
    def get_grammar_stats(self) -> Dict[str, int]:
        """获取语法规则统计"""
        rules = self.dal.list_all_grammar_rules(0, 10000)  # 获取所有用于统计
        total = len(rules)
        starred = len([r for r in rules if r.is_starred])
        auto = len([r for r in rules if r.source.value == "auto"])
        manual = len([r for r in rules if r.source.value == "manual"])
        
        return {
            "total": total,
            "starred": starred,
            "auto": auto,
            "manual": manual
        }
