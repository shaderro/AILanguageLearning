"""
语法规则适配器 - Models ↔ DTO 转换

职责：
1. 将数据库 ORM Models 转换为领域 DTO（供 AI 逻辑使用）
2. 将领域 DTO 转换为 ORM Models（供数据库存储）
3. 处理字段映射、枚举转换、默认值等

使用场景：
- 从数据库读取数据后，转为 DTO 返回给上层
- 接收上层 DTO 数据，转为 Models 存入数据库

字段映射关系：
- Model.rule_name ↔ DTO.name
- Model.rule_summary ↔ DTO.explanation
"""
from typing import Optional, List
from database_system.business_logic.models import (
    GrammarRule as GrammarModel,
    GrammarExample as GrammarExampleModel,
    SourceType as ModelSourceType,
    LearnStatus as ModelLearnStatus
)
from backend.data_managers.data_classes_new import (
    GrammarRule as GrammarDTO,
    GrammarExample as GrammarExampleDTO
)


class GrammarExampleAdapter:
    """语法例句适配器"""
    
    @staticmethod
    def model_to_dto(model: GrammarExampleModel) -> GrammarExampleDTO:
        """
        ORM Model → DTO
        从数据库读取后转换为领域对象
        """
        return GrammarExampleDTO(
            rule_id=model.rule_id,
            text_id=model.text_id,
            sentence_id=model.sentence_id,
            explanation_context=model.explanation_context or ""
        )
    
    @staticmethod
    def dto_to_model(dto: GrammarExampleDTO, rule_id: Optional[int] = None) -> GrammarExampleModel:
        """
        DTO → ORM Model
        准备存入数据库
        """
        return GrammarExampleModel(
            rule_id=rule_id or dto.rule_id,
            text_id=dto.text_id,
            sentence_id=dto.sentence_id,
            explanation_context=dto.explanation_context
        )


class GrammarAdapter:
    """语法规则适配器"""
    
    @staticmethod
    def _convert_source_to_dto(model_source: ModelSourceType) -> str:
        """
        枚举转换：Model SourceType → DTO 字符串
        Model: SourceType.AUTO → DTO: "auto"
        """
        return model_source.value.lower()
    
    @staticmethod
    def _convert_source_to_model(dto_source: str) -> ModelSourceType:
        """
        枚举转换：DTO 字符串 → Model SourceType
        DTO: "auto" → Model: SourceType.AUTO
        容错处理：未知值默认为 AUTO
        """
        try:
            return ModelSourceType(dto_source.upper())
        except (ValueError, AttributeError):
            return ModelSourceType.AUTO
    
    @staticmethod
    def _convert_learn_status_to_dto(model_status: ModelLearnStatus) -> str:
        """
        枚举转换：Model LearnStatus → DTO 字符串
        Model: LearnStatus.NOT_MASTERED → DTO: "not_mastered"
        """
        return model_status.value.lower()
    
    @staticmethod
    def _convert_learn_status_to_model(dto_status: str) -> ModelLearnStatus:
        """
        枚举转换：DTO 字符串 → Model LearnStatus
        DTO: "not_mastered" → Model: LearnStatus.NOT_MASTERED
        容错处理：未知值默认为 NOT_MASTERED
        """
        try:
            return ModelLearnStatus(dto_status.lower())
        except (ValueError, AttributeError):
            return ModelLearnStatus.NOT_MASTERED
    
    @staticmethod
    def model_to_dto(model: GrammarModel, include_examples: bool = True) -> GrammarDTO:
        """
        ORM Model → DTO
        
        参数:
            model: 数据库 ORM 对象
            include_examples: 是否包含例句（默认包含）
        
        返回:
            GrammarDTO: 领域数据对象
        
        使用场景:
            - 从数据库查询语法规则后，返回给 AI 逻辑层
            - API 接口返回数据给前端
            
        注意字段映射:
            - Model.rule_name → DTO.name
            - Model.rule_summary → DTO.explanation
        """
        # 转换例句（如果需要）
        examples = []
        if include_examples and model.examples:
            examples = [
                GrammarExampleAdapter.model_to_dto(ex)
                for ex in model.examples
            ]
        
        return GrammarDTO(
            rule_id=model.rule_id,
            name=model.rule_name,  # 注意字段映射（旧字段，用于唯一约束等）
            explanation=model.rule_summary,  # 注意字段映射（旧字段，用于摘要存储）
            # 新字段：展示名 & canonical 信息
            display_name=model.display_name or model.rule_name,
            canonical_category=model.canonical_category,
            canonical_subtype=model.canonical_subtype,
            canonical_function=model.canonical_function,
            canonical_key=model.canonical_key,
            language=model.language,
            source=GrammarAdapter._convert_source_to_dto(model.source),
            is_starred=model.is_starred,
            learn_status=GrammarAdapter._convert_learn_status_to_dto(model.learn_status) if model.learn_status else "not_mastered",
            examples=examples,
        )
    
    @staticmethod
    def dto_to_model(dto: GrammarDTO, rule_id: Optional[int] = None) -> GrammarModel:
        """
        DTO → ORM Model
        
        参数:
            dto: 领域数据对象
            rule_id: 可选的 rule_id（用于更新场景）
        
        返回:
            GrammarModel: 数据库 ORM 对象
        
        使用场景:
            - 接收前端/AI 层的数据，准备存入数据库
            - 创建或更新语法规则
        
        注意:
            - 不包含例句的转换（例句需单独处理）
            - rule_id 为 None 时表示新建，有值时表示更新
            
        注意字段映射:
            - DTO.name → Model.rule_name
            - DTO.explanation → Model.rule_summary
        """
        model = GrammarModel(
            rule_name=dto.name,  # 注意字段映射（旧字段）
            rule_summary=dto.explanation,  # 注意字段映射（旧字段）
            # 新字段：优先使用显式的 display_name，否则回退为 name
            display_name=getattr(dto, "display_name", None) or dto.name,
            canonical_category=getattr(dto, "canonical_category", None),
            canonical_subtype=getattr(dto, "canonical_subtype", None),
            canonical_function=getattr(dto, "canonical_function", None),
            canonical_key=getattr(dto, "canonical_key", None),
            language=dto.language,
            source=GrammarAdapter._convert_source_to_model(dto.source),
            is_starred=dto.is_starred,
            learn_status=GrammarAdapter._convert_learn_status_to_model(
                getattr(dto, "learn_status", "not_mastered")
            ),
        )
        
        # 如果提供了 rule_id，设置它（用于更新场景）
        if rule_id is not None:
            model.rule_id = rule_id
        
        return model
    
    @staticmethod
    def models_to_dtos(models: List[GrammarModel], include_examples: bool = False) -> List[GrammarDTO]:
        """
        批量转换：Models → DTOs
        
        参数:
            models: ORM Model 列表
            include_examples: 是否包含例句（批量查询时通常不包含，以提升性能）
        
        使用场景:
            - 列表查询、搜索结果返回
        """
        return [
            GrammarAdapter.model_to_dto(model, include_examples=include_examples)
            for model in models
        ]


# ==================== 使用示例（注释） ====================
"""
### 示例 1: 从数据库读取后转为 DTO

```python
from database_system.business_logic.managers import GrammarManager
from backend.adapters import GrammarAdapter

# 1. 从数据库查询（返回 Model）
grammar_manager = GrammarManager(session)
grammar_model = grammar_manager.get_grammar_rule(rule_id=1)

# 2. 转换为 DTO（供 AI 逻辑使用）
grammar_dto = GrammarAdapter.model_to_dto(grammar_model, include_examples=True)

# 3. 现在可以将 grammar_dto 传递给 AI 逻辑或返回给前端
return grammar_dto
```

### 示例 2: 接收 DTO 后存入数据库

```python
from backend.adapters import GrammarAdapter
from database_system.business_logic.managers import GrammarManager

# 1. 接收前端/AI 层的 DTO
grammar_dto = GrammarDTO(
    rule_id=0,  # 新建时为0或不设置
    name="德语定冠词变格",
    explanation="德语定冠词根据格、性、数变化",
    source="manual",
    is_starred=False,
    examples=[]
)

# 2. 转换为 Model
grammar_model = GrammarAdapter.dto_to_model(grammar_dto)

# 3. 存入数据库（通过 Manager）
grammar_manager = GrammarManager(session)
# 注意：这里需要直接操作 session，或者 Manager 提供接受 Model 的方法
session.add(grammar_model)
session.commit()
```

### 示例 3: 在 data_manager 中使用

```python
# backend/data_managers/grammar_rule_manager_db.py

from backend.adapters import GrammarAdapter
from database_system.business_logic.managers import GrammarManager as DBGrammarManager

class GrammarRuleManager:
    def __init__(self, session):
        self.session = session
        self.db_manager = DBGrammarManager(session)
    
    def get_rule(self, rule_id: int) -> GrammarDTO:
        \"\"\"获取语法规则（返回 DTO）\"\"\"
        # 1. 从数据库获取 Model
        grammar_model = self.db_manager.get_grammar_rule(rule_id)
        if not grammar_model:
            return None
        
        # 2. 转换为 DTO 返回
        return GrammarAdapter.model_to_dto(grammar_model, include_examples=True)
    
    def add_rule(self, name: str, explanation: str, 
                 source: str = "auto") -> GrammarDTO:
        \"\"\"添加语法规则（返回 DTO）\"\"\"
        # 1. 通过数据库 Manager 创建（返回 Model）
        grammar_model = self.db_manager.add_grammar_rule(
            rule_name=name,
            rule_summary=explanation,
            source=source
        )
        
        # 2. 转换为 DTO 返回
        return GrammarAdapter.model_to_dto(grammar_model)
```
"""

