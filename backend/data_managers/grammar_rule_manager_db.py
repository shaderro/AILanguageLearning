"""
GrammarRuleManager - 基于数据库的实现

职责：
1. 对外提供统一的 DTO 接口（data_classes_new.py）
2. 内部调用数据库业务层 Manager
3. 使用 Adapter 进行 Model ↔ DTO 转换
4. 处理业务逻辑和错误

使用场景：
- AI Assistants 调用
- FastAPI 接口调用
- 任何需要语法规则数据的地方

示例：
    from sqlalchemy.orm import Session
    from backend.data_managers import GrammarRuleManagerDB
    
    session = get_session()
    grammar_manager = GrammarRuleManagerDB(session)
    
    # 获取语法规则
    rule = grammar_manager.get_rule_by_id(1)
    
    # 添加语法规则
    new_rule = grammar_manager.add_new_rule("定冠词变格", "德语定冠词根据格、性、数变化")
    
    # 搜索语法规则
    results = grammar_manager.search_rules("定冠词")
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from backend.data_managers.data_classes_new import (
    GrammarRule as GrammarDTO,
    GrammarExample as GrammarExampleDTO
)
from backend.adapters.grammar_adapter import GrammarAdapter, GrammarExampleAdapter
from database_system.business_logic.managers import GrammarManager as DBGrammarManager


class GrammarRuleManager:
    """
    语法规则管理器 - 数据库版本
    
    设计原则：
    - 对外统一返回 DTO（领域对象）
    - 内部使用数据库 Manager 操作
    - 通过 Adapter 转换 Model ↔ DTO
    
    注意字段映射：
    - DTO.name ↔ Model.rule_name
    - DTO.explanation ↔ Model.rule_summary
    """
    
    def __init__(self, session: Session):
        """
        初始化语法规则管理器
        
        参数:
            session: SQLAlchemy Session（数据库会话）
        """
        self.session = session
        self.db_manager = DBGrammarManager(session)
    
    def get_rule_by_id(self, rule_id: int) -> Optional[GrammarDTO]:
        """
        根据ID获取语法规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            GrammarDTO: 语法规则数据对象（包含例句）
            None: 规则不存在
            
        使用示例:
            rule = grammar_manager.get_rule_by_id(1)
            if rule:
                print(f"{rule.name}: {rule.explanation}")
        """
        grammar_model = self.db_manager.get_grammar_rule(rule_id)
        if not grammar_model:
            return None
        
        return GrammarAdapter.model_to_dto(grammar_model, include_examples=True)
    
    def get_rule_by_name(self, rule_name: str) -> Optional[GrammarDTO]:
        """
        根据规则名称查找
        
        参数:
            rule_name: 规则名称（如 "德语定冠词变格"）
            
        返回:
            GrammarDTO: 语法规则数据对象
            None: 规则不存在
        """
        grammar_model = self.db_manager.find_grammar_by_name(rule_name)
        if not grammar_model:
            return None
        
        return GrammarAdapter.model_to_dto(grammar_model, include_examples=True)
    
    def add_new_rule(self, name: str, explanation: str, 
                     source: str = "qa", is_starred: bool = False, user_id: int = None) -> GrammarDTO:
        """
        添加新语法规则
        
        参数:
            name: 规则名称
            explanation: 规则解释
            source: 来源（"auto", "qa", "manual"），默认 "qa"
            is_starred: 是否收藏，默认 False
            user_id: 用户ID（必填，用于数据隔离）
            
        返回:
            GrammarDTO: 新创建的语法规则数据对象
            
        使用示例:
            new_rule = grammar_manager.add_new_rule(
                name="德语定冠词变格",
                explanation="德语定冠词根据格、性、数变化",
                source="manual",
                is_starred=True,
                user_id=1
            )
            print(f"创建规则ID: {new_rule.rule_id}")
        """
        grammar_model = self.db_manager.add_grammar_rule(
            rule_name=name,  # 注意字段映射
            rule_summary=explanation,  # 注意字段映射
            source=source,
            is_starred=is_starred,
            user_id=user_id
        )
        
        return GrammarAdapter.model_to_dto(grammar_model)
    
    def get_all_rules(self, skip: int = 0, limit: int = 100, 
                      starred_only: bool = False) -> List[GrammarDTO]:
        """
        获取所有语法规则（分页）
        
        参数:
            skip: 跳过的记录数（用于分页）
            limit: 返回的最大记录数
            starred_only: 是否只返回收藏的规则
            
        返回:
            List[GrammarDTO]: 语法规则列表（不包含例句，提升性能）
            
        使用示例:
            # 获取前20个规则
            rules = grammar_manager.get_all_rules(skip=0, limit=20)
            
            # 获取收藏的规则
            starred = grammar_manager.get_all_rules(starred_only=True)
        """
        grammar_models = self.db_manager.list_grammar_rules(
            skip=skip, 
            limit=limit, 
            starred_only=starred_only
        )
        
        # 批量转换，不包含例句以提升性能
        return GrammarAdapter.models_to_dtos(grammar_models, include_examples=False)
    
    def get_all_rules_name(self) -> List[str]:
        """
        获取所有语法规则的名称（用于快速查找）
        
        返回:
            List[str]: 规则名称列表
            
        使用示例:
            rule_names = grammar_manager.get_all_rules_name()
            if "定冠词变格" in rule_names:
                print("规则已存在")
        """
        rules = self.get_all_rules(limit=10000)  # 获取所有
        return [rule.name for rule in rules]
    
    def search_rules(self, keyword: str) -> List[GrammarDTO]:
        """
        搜索语法规则（根据名称或解释）
        
        参数:
            keyword: 搜索关键词
            
        返回:
            List[GrammarDTO]: 匹配的规则列表
            
        使用示例:
            results = grammar_manager.search_rules("定冠词")
            for rule in results:
                print(f"{rule.name}: {rule.explanation}")
        """
        grammar_models = self.db_manager.search_grammar_rules(keyword)
        return GrammarAdapter.models_to_dtos(grammar_models, include_examples=False)
    
    def update_rule(self, rule_id: int, **kwargs) -> Optional[GrammarDTO]:
        """
        更新语法规则
        
        参数:
            rule_id: 规则ID
            **kwargs: 要更新的字段
                - name: 规则名称（注意：会映射到 rule_name）
                - explanation: 规则解释（注意：会映射到 rule_summary）
                - source: 来源
                - is_starred: 是否收藏
            
        返回:
            GrammarDTO: 更新后的规则
            None: 规则不存在
            
        使用示例:
            updated = grammar_manager.update_rule(
                rule_id=1,
                explanation="新的解释",
                is_starred=True
            )
        """
        # 处理字段名称映射
        update_data = {}
        for key, value in kwargs.items():
            if key == 'name':
                update_data['rule_name'] = value
            elif key == 'explanation':
                update_data['rule_summary'] = value
            else:
                update_data[key] = value
        
        grammar_model = self.db_manager.update_grammar_rule(rule_id, **update_data)
        if not grammar_model:
            return None
        
        return GrammarAdapter.model_to_dto(grammar_model)
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除语法规则
        
        参数:
            rule_id: 规则ID
            
        返回:
            bool: 是否删除成功
            
        使用示例:
            success = grammar_manager.delete_rule(1)
            if success:
                print("删除成功")
        """
        return self.db_manager.delete_grammar_rule(rule_id)
    
    def toggle_star(self, rule_id: int) -> bool:
        """
        切换语法规则的收藏状态
        
        参数:
            rule_id: 规则ID
            
        返回:
            bool: 切换后的收藏状态（True=已收藏, False=未收藏）
            
        使用示例:
            is_starred = grammar_manager.toggle_star(1)
            print(f"收藏状态: {'已收藏' if is_starred else '未收藏'}")
        """
        return self.db_manager.toggle_star(rule_id)
    
    def get_id_by_rule_name(self, rule_name: str) -> Optional[int]:
        """
        根据规则名称获取ID
        
        参数:
            rule_name: 规则名称
            
        返回:
            int: 规则ID
            None: 规则不存在
            
        使用示例:
            rule_id = grammar_manager.get_id_by_rule_name("定冠词变格")
            if rule_id:
                print(f"规则ID: {rule_id}")
        """
        rule = self.get_rule_by_name(rule_name)
        return rule.rule_id if rule else None
    
    def add_grammar_example(self, rule_id: int, text_id: int, 
                           sentence_id: int, explanation_context: str) -> GrammarExampleDTO:
        """
        为语法规则添加例句
        
        参数:
            rule_id: 规则ID
            text_id: 文章ID
            sentence_id: 句子ID
            explanation_context: 上下文解释
            
        返回:
            GrammarExampleDTO: 新创建的例句
            
        使用示例:
            example = grammar_manager.add_grammar_example(
                rule_id=1,
                text_id=1,
                sentence_id=5,
                explanation_context="在这个句子中..."
            )
        """
        # 通过数据库 Manager 的公开方法创建例句
        from database_system.business_logic.crud import GrammarCRUD
        grammar_crud = GrammarCRUD(self.session)
        example_model = grammar_crud.create_example(
            rule_id=rule_id,
            text_id=text_id,
            sentence_id=sentence_id,
            explanation_context=explanation_context
        )
        
        return GrammarExampleAdapter.model_to_dto(example_model)
    
    def get_examples_by_rule_id(self, rule_id: int) -> List[GrammarExampleDTO]:
        """
        获取语法规则的所有例句
        
        参数:
            rule_id: 规则ID
            
        返回:
            List[GrammarExampleDTO]: 例句列表
            
        使用示例:
            examples = grammar_manager.get_examples_by_rule_id(1)
            for ex in examples:
                print(f"文章{ex.text_id}, 句子{ex.sentence_id}")
        """
        rule = self.get_rule_by_id(rule_id)
        return rule.examples if rule else []
    
    def get_rule_with_examples(self, rule_id: int) -> Optional[GrammarDTO]:
        """
        获取语法规则及其例句（完整信息）
        
        参数:
            rule_id: 规则ID
            
        返回:
            GrammarDTO: 包含完整例句的规则对象
            None: 规则不存在
            
        使用示例:
            rule = grammar_manager.get_rule_with_examples(1)
            if rule:
                print(f"规则: {rule.name}")
                print(f"例句数量: {len(rule.examples)}")
        """
        return self.get_rule_by_id(rule_id)  # 已经包含例句
    
    def get_grammar_stats(self) -> dict:
        """
        获取语法规则统计信息
        
        返回:
            dict: 统计信息
                - total: 总规则数
                - starred: 收藏规则数
                - auto: 自动生成的规则数
                - manual: 手动添加的规则数
                
        使用示例:
            stats = grammar_manager.get_grammar_stats()
            print(f"总规则: {stats['total']}")
            print(f"收藏规则: {stats['starred']}")
        """
        rules = self.get_all_rules(limit=10000)  # 获取所有用于统计
        total = len(rules)
        starred = len([r for r in rules if r.is_starred])
        auto = len([r for r in rules if r.source == "auto"])
        manual = len([r for r in rules if r.source == "manual"])
        qa = len([r for r in rules if r.source == "qa"])
        
        return {
            "total": total,
            "starred": starred,
            "auto": auto,
            "manual": manual,
            "qa": qa
        }
    
    def get_new_rule_id(self) -> int:
        """
        获取新规则ID（兼容旧版本）
        
        注意：数据库版本中，ID 由数据库自动生成，此方法仅用于兼容
        """
        # 数据库会自动生成ID，这里返回下一个可能的ID（仅供参考）
        stats = self.get_grammar_stats()
        return stats.get('total', 0) + 1

