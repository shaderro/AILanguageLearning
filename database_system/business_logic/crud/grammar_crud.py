"""
语法规则相关 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..models import GrammarRule, GrammarExample, SourceType, LearnStatus


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
    
    def _coerce_learn_status(self, value) -> LearnStatus:
        """转换学习状态"""
        if isinstance(value, LearnStatus):
            return value
        if value is None:
            return LearnStatus.NOT_MASTERED
        if isinstance(value, str):
            if value == 'mastered':
                return LearnStatus.MASTERED
            elif value == 'not_mastered':
                return LearnStatus.NOT_MASTERED
        try:
            return LearnStatus(value)
        except Exception:
            return LearnStatus.NOT_MASTERED
    
    def create(
        self,
        rule_name: str,
        rule_summary: str,
        source: str = "auto",
        is_starred: bool = False,
        user_id: int = None,
        language: str = None,
        display_name: Optional[str] = None,
        canonical_category: Optional[str] = None,
        canonical_subtype: Optional[str] = None,
        canonical_function: Optional[str] = None,
        canonical_key: Optional[str] = None,
    ) -> GrammarRule:
        """创建语法规则（支持可选的 display_name / canonical_* 字段）
        
        兼容策略：
        - 如果未提供 display_name，则默认使用 rule_name（保持旧行为）
        - canonical_* 与 canonical_key 默认为 None，仅在新逻辑中写入
        """
        # 旧逻辑：默认 display_name = rule_name（便于前端展示）
        if display_name is None:
            display_name = rule_name

        rule = GrammarRule(
            rule_name=rule_name,
            rule_summary=rule_summary,
            language=language,
            # 新字段：仅在新规则创建时会显式传入，旧调用保持默认 None
            display_name=display_name,
            canonical_category=canonical_category,
            canonical_subtype=canonical_subtype,
            canonical_function=canonical_function,
            canonical_key=canonical_key,
            source=self._coerce_source(source),
            is_starred=is_starred,
            user_id=user_id,
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule
    
    def get_or_create(
        self,
        rule_name: str,
        rule_summary: str,
        source: str = "auto",
        is_starred: bool = False,
        user_id: int = None,
        language: str = None,
        display_name: Optional[str] = None,
        canonical_category: Optional[str] = None,
        canonical_subtype: Optional[str] = None,
        canonical_function: Optional[str] = None,
        canonical_key: Optional[str] = None,
    ) -> GrammarRule:
        """获取或创建语法规则（如果已存在则返回现有记录，不存在则创建）
        
        ⚠️ 重要：
        - 对于已存在的旧规则，不会自动回填 / 修改 canonical_* 字段，保持为 NULL
        - 只有在创建新规则时，才会写入 display_name / canonical_* / canonical_key
        """
        # 🔧 如果user_id为None，直接创建（向后兼容）
        if user_id is None:
            return self.create(
                rule_name,
                rule_summary,
                source,
                is_starred,
                user_id,
                language,
                display_name=display_name,
                canonical_category=canonical_category,
                canonical_subtype=canonical_subtype,
                canonical_function=canonical_function,
                canonical_key=canonical_key,
            )
        
        # 🔧 查找已存在的语法规则（按user_id和rule_name）
        existing = self.session.query(GrammarRule).filter(
            GrammarRule.rule_name == rule_name,
            GrammarRule.user_id == user_id
        ).first()
        if existing:
            # 🔧 如果已存在，更新language字段（如果提供了language且现有记录的language为None）
            if language and existing.language is None:
                existing.language = language
                self.session.commit()
                self.session.refresh(existing)
                print(f"🔍 [DEBUG] 更新已存在语法规则的language: {rule_name} -> {language}")
            return existing
        # 🔧 不存在则创建新语法规则
        return self.create(
            rule_name,
            rule_summary,
            source,
            is_starred,
            user_id,
            language,
            display_name=display_name,
            canonical_category=canonical_category,
            canonical_subtype=canonical_subtype,
            canonical_function=canonical_function,
            canonical_key=canonical_key,
        )
    
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
                elif key == "learn_status":
                    value = self._coerce_learn_status(value)
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
        """创建语法例句（带查重逻辑，避免重复创建）"""
        existing = self.session.query(GrammarExample).filter(
            GrammarExample.rule_id == rule_id,
            GrammarExample.text_id == text_id,
            GrammarExample.sentence_id == sentence_id,
        ).first()
        if existing:
            if explanation_context and not existing.explanation_context:
                existing.explanation_context = explanation_context
                self.session.commit()
                self.session.refresh(existing)
            print(
                f"🔍 [GrammarCRUD] 发现已存在的 example: "
                f"rule_id={rule_id}, text_id={text_id}, sentence_id={sentence_id}"
            )
            return existing

        example = GrammarExample(
            rule_id=rule_id,
            text_id=text_id,
            sentence_id=sentence_id,
            explanation_context=explanation_context,
        )
        self.session.add(example)
        self.session.commit()
        self.session.refresh(example)
        print(
            f"✅ [GrammarCRUD] 创建新 example: "
            f"rule_id={rule_id}, text_id={text_id}, sentence_id={sentence_id}"
        )
        return example
