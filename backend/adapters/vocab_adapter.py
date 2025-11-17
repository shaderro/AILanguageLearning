"""
词汇适配器 - Models ↔ DTO 转换

职责：
1. 将数据库 ORM Models 转换为领域 DTO（供 AI 逻辑使用）
2. 将领域 DTO 转换为 ORM Models（供数据库存储）
3. 处理字段映射、枚举转换、默认值等

使用场景：
- 从数据库读取数据后，转为 DTO 返回给上层
- 接收上层 DTO 数据，转为 Models 存入数据库
"""
from typing import Optional, List
from database_system.business_logic.models import (
    VocabExpression as VocabModel,
    VocabExpressionExample as VocabExampleModel,
    SourceType as ModelSourceType,
    LearnStatus as ModelLearnStatus
)
from backend.data_managers.data_classes_new import (
    VocabExpression as VocabDTO,
    VocabExpressionExample as VocabExampleDTO
)


class VocabExampleAdapter:
    """词汇例句适配器"""
    
    @staticmethod
    def model_to_dto(model: VocabExampleModel) -> VocabExampleDTO:
        """
        ORM Model → DTO
        从数据库读取后转换为领域对象
        """
        return VocabExampleDTO(
            vocab_id=model.vocab_id,
            text_id=model.text_id,
            sentence_id=model.sentence_id,
            context_explanation=model.context_explanation or "",
            token_indices=model.token_indices or []
        )
    
    @staticmethod
    def dto_to_model(dto: VocabExampleDTO, vocab_id: Optional[int] = None) -> VocabExampleModel:
        """
        DTO → ORM Model
        准备存入数据库
        """
        return VocabExampleModel(
            vocab_id=vocab_id or dto.vocab_id,
            text_id=dto.text_id,
            sentence_id=dto.sentence_id,
            context_explanation=dto.context_explanation,
            token_indices=dto.token_indices
        )


class VocabAdapter:
    """词汇适配器"""
    
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
    def model_to_dto(model: VocabModel, include_examples: bool = True) -> VocabDTO:
        """
        ORM Model → DTO
        
        参数:
            model: 数据库 ORM 对象
            include_examples: 是否包含例句（默认包含）
        
        返回:
            VocabDTO: 领域数据对象
        
        使用场景:
            - 从数据库查询词汇后，返回给 AI 逻辑层
            - API 接口返回数据给前端
        """
        # 转换例句（如果需要）
        examples = []
        if include_examples and model.examples:
            examples = [
                VocabExampleAdapter.model_to_dto(ex)
                for ex in model.examples
            ]
        
        return VocabDTO(
            vocab_id=model.vocab_id,
            vocab_body=model.vocab_body,
            explanation=model.explanation,
            language=model.language,
            source=VocabAdapter._convert_source_to_dto(model.source),
            is_starred=model.is_starred,
            learn_status=VocabAdapter._convert_learn_status_to_dto(model.learn_status) if model.learn_status else "not_mastered",
            examples=examples
        )
    
    @staticmethod
    def dto_to_model(dto: VocabDTO, vocab_id: Optional[int] = None) -> VocabModel:
        """
        DTO → ORM Model
        
        参数:
            dto: 领域数据对象
            vocab_id: 可选的 vocab_id（用于更新场景）
        
        返回:
            VocabModel: 数据库 ORM 对象
        
        使用场景:
            - 接收前端/AI 层的数据，准备存入数据库
            - 创建或更新词汇
        
        注意:
            - 不包含例句的转换（例句需单独处理）
            - vocab_id 为 None 时表示新建，有值时表示更新
        """
        model = VocabModel(
            vocab_body=dto.vocab_body,
            explanation=dto.explanation,
            language=dto.language,
            source=VocabAdapter._convert_source_to_model(dto.source),
            is_starred=dto.is_starred,
            learn_status=VocabAdapter._convert_learn_status_to_model(getattr(dto, 'learn_status', 'not_mastered'))
        )
        
        # 如果提供了 vocab_id，设置它（用于更新场景）
        if vocab_id is not None:
            model.vocab_id = vocab_id
        
        return model
    
    @staticmethod
    def models_to_dtos(models: List[VocabModel], include_examples: bool = False) -> List[VocabDTO]:
        """
        批量转换：Models → DTOs
        
        参数:
            models: ORM Model 列表
            include_examples: 是否包含例句（批量查询时通常不包含，以提升性能）
        
        使用场景:
            - 列表查询、搜索结果返回
        """
        return [
            VocabAdapter.model_to_dto(model, include_examples=include_examples)
            for model in models
        ]


# ==================== 使用示例（注释） ====================
"""
### 示例 1: 从数据库读取后转为 DTO

```python
from database_system.business_logic.managers import VocabManager
from backend.adapters import VocabAdapter

# 1. 从数据库查询（返回 Model）
vocab_manager = VocabManager(session)
vocab_model = vocab_manager.get_vocab(vocab_id=1)

# 2. 转换为 DTO（供 AI 逻辑使用）
vocab_dto = VocabAdapter.model_to_dto(vocab_model, include_examples=True)

# 3. 现在可以将 vocab_dto 传递给 AI 逻辑或返回给前端
return vocab_dto
```

### 示例 2: 接收 DTO 后存入数据库

```python
from backend.adapters import VocabAdapter
from database_system.business_logic.managers import VocabManager

# 1. 接收前端/AI 层的 DTO
vocab_dto = VocabDTO(
    vocab_id=0,  # 新建时为0或不设置
    vocab_body="hello",
    explanation="问候语",
    source="manual",
    is_starred=False,
    examples=[]
)

# 2. 转换为 Model
vocab_model = VocabAdapter.dto_to_model(vocab_dto)

# 3. 存入数据库（通过 Manager）
vocab_manager = VocabManager(session)
# 注意：这里需要直接操作 session，或者 Manager 提供接受 Model 的方法
session.add(vocab_model)
session.commit()
```

### 示例 3: 在 data_manager 中使用

```python
# backend/data_managers/vocab_manager.py

from backend.adapters import VocabAdapter
from database_system.business_logic.managers import VocabManager as DBVocabManager

class VocabManager:
    def __init__(self, session):
        self.session = session
        self.db_manager = DBVocabManager(session)
    
    def get_vocab(self, vocab_id: int) -> VocabDTO:
        \"\"\"获取词汇（返回 DTO）\"\"\"
        # 1. 从数据库获取 Model
        vocab_model = self.db_manager.get_vocab(vocab_id)
        if not vocab_model:
            return None
        
        # 2. 转换为 DTO 返回
        return VocabAdapter.model_to_dto(vocab_model, include_examples=True)
    
    def add_vocab(self, vocab_body: str, explanation: str, 
                  source: str = "auto") -> VocabDTO:
        \"\"\"添加词汇（返回 DTO）\"\"\"
        # 1. 通过数据库 Manager 创建（返回 Model）
        vocab_model = self.db_manager.add_vocab(
            vocab_body=vocab_body,
            explanation=explanation,
            source=source
        )
        
        # 2. 转换为 DTO 返回
        return VocabAdapter.model_to_dto(vocab_model)
```
"""
