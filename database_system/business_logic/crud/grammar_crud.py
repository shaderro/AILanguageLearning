"""
语法规则相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models import GrammarRule, GrammarExample, SourceType


class GrammarCRUD:
    """语法规则 CRUD 操作"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _coerce_source(self, value: Optional[str]) -> SourceType:
        """转换源类型"""
        if isinstance(value, SourceType):
            return value
        if value is None:
            return SourceType.AUTO
        try:
            return SourceType(value)
        except Exception:
            return SourceType.AUTO
    
    def create(self, rule_name: str, rule_summary: str,
               source: str = "auto", is_starred: bool = False) -> GrammarRule:
        """创建语法规则"""
        rule = GrammarRule(
            rule_name=rule_name,
            rule_summary=rule_summary,
            source=self._coerce_source(source),
            is_starred=is_starred
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule
    
    def get_or_create(self, rule_name: str, rule_summary: str,
                      source: str = "auto", is_starred: bool = False) -> GrammarRule:
        """获取或创建语法规则"""
        existing = self.session.query(GrammarRule).filter(
            GrammarRule.rule_name == rule_name
        ).first()
        if existing:
            return existing
        return self.create(rule_name, rule_summary, source, is_starred)
    
    def get_by_id(self, rule_id: int) -> Optional[GrammarRule]:
        """根据ID获取语法规则"""
        return self.session.query(GrammarRule).filter(
            GrammarRule.rule_id == rule_id
        ).first()
    
    def get_by_name(self, rule_name: str) -> Optional[GrammarRule]:
        """根据名称获取语法规则"""
        return self.session.query(GrammarRule).filter(
            GrammarRule.rule_name == rule_name
        ).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[GrammarRule]:
        """获取所有语法规则"""
        return self.session.query(GrammarRule).offset(skip).limit(limit).all()
    
    def get_starred(self) -> List[GrammarRule]:
        """获取收藏的语法规则"""
        return self.session.query(GrammarRule).filter(
            GrammarRule.is_starred == True
        ).all()
    
    def search(self, keyword: str) -> List[GrammarRule]:
        """搜索语法规则"""
        return self.session.query(GrammarRule).filter(
            or_(
                GrammarRule.rule_name.contains(keyword),
                GrammarRule.rule_summary.contains(keyword)
            )
        ).all()
    
    def update(self, rule_id: int, **kwargs) -> Optional[GrammarRule]:
        """更新语法规则"""
        rule = self.get_by_id(rule_id)
        if rule:
            for key, value in kwargs.items():
                if key == "source":
                    value = self._coerce_source(value)
                if hasattr(rule, key):
                    setattr(rule, key, value)
            self.session.commit()
            self.session.refresh(rule)
        return rule
    
    def delete(self, rule_id: int) -> bool:
        """删除语法规则"""
        rule = self.get_by_id(rule_id)
        if rule:
            self.session.delete(rule)
            self.session.commit()
            return True
        return False
    
    def create_example(self, *, rule_id: int, text_id: int,
                      sentence_id: int, explanation_context: Optional[str] = None) -> GrammarExample:
        """创建语法例句"""
        example = GrammarExample(
            rule_id=rule_id,
            text_id=text_id,
            sentence_id=sentence_id,
            explanation_context=explanation_context,
        )
        self.session.add(example)
        self.session.commit()
        self.session.refresh(example)
        return example
