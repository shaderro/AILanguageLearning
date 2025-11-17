"""
文章适配器 - Models ↔ DTO 转换

职责：
1. 将数据库 ORM Models 转换为领域 DTO（供 AI 逻辑使用）
2. 将领域 DTO 转换为 ORM Models（供数据库存储）
3. 处理嵌套结构（文章包含句子列表）

使用场景：
- 从数据库读取数据后，转为 DTO 返回给上层
- 接收上层 DTO 数据，转为 Models 存入数据库
"""
from typing import Optional, List
from database_system.business_logic.models import (
    OriginalText as TextModel,
    Sentence as SentenceModel,
    DifficultyLevel as ModelDifficultyLevel
)
from backend.data_managers.data_classes_new import (
    OriginalText as TextDTO,
    Sentence as SentenceDTO,
    Token as TokenDTO
)


class SentenceAdapter:
    """句子适配器"""
    
    @staticmethod
    def model_to_dto(model: SentenceModel, include_tokens: bool = False) -> SentenceDTO:
        """
        ORM Model → DTO
        从数据库读取后转换为领域对象
        
        注意：
        - grammar_annotations和vocab_annotations在Model中是JSON格式，需要转换为tuple
        - tokens可能不包含，根据include_tokens参数决定
        """
        # 处理annotations（JSON → tuple）
        grammar_annotations = tuple(model.grammar_annotations) if model.grammar_annotations else ()
        vocab_annotations = tuple(model.vocab_annotations) if model.vocab_annotations else ()
        
        # 处理tokens
        tokens = ()
        if include_tokens and model.tokens:
            tokens = tuple([
                TokenDTO(
                    token_body=t.token_body,
                    token_type=t.token_type.value if t.token_type else 'TEXT',
                    difficulty_level=t.difficulty_level.value.lower() if t.difficulty_level else None,
                    # 可选字段按需映射（如果 ORM 上存在这些属性）
                    global_token_id=getattr(t, "global_token_id", None),
                    sentence_token_id=t.sentence_token_id,
                    pos_tag=getattr(t, "pos_tag", None),
                    lemma=getattr(t, "lemma", None),
                    is_grammar_marker=getattr(t, "is_grammar_marker", False),
                    linked_vocab_id=getattr(t, "linked_vocab_id", None),
                )
                for t in sorted(model.tokens, key=lambda x: x.sentence_token_id)
            ])
        
        # 处理difficulty_level（枚举 → 字符串）
        difficulty_level = None
        if model.sentence_difficulty_level:
            difficulty_level = model.sentence_difficulty_level.value.lower()
        
        return SentenceDTO(
            text_id=model.text_id,
            sentence_id=model.sentence_id,
            sentence_body=model.sentence_body,
            grammar_annotations=grammar_annotations,
            vocab_annotations=vocab_annotations,
            sentence_difficulty_level=difficulty_level,
            tokens=tokens
        )
    
    @staticmethod
    def dto_to_model(dto: SentenceDTO) -> SentenceModel:
        """
        DTO → ORM Model
        准备存入数据库
        
        注意：
        - grammar_annotations和vocab_annotations需要转换为JSON格式（list）
        - tokens不包含在Model中（tokens有单独的表）
        """
        # 处理annotations（tuple → list for JSON）
        grammar_annotations = list(dto.grammar_annotations) if dto.grammar_annotations else []
        vocab_annotations = list(dto.vocab_annotations) if dto.vocab_annotations else []
        
        # 处理difficulty_level（字符串 → 枚举）
        difficulty_level = None
        if dto.sentence_difficulty_level:
            try:
                # 确保值是大写的
                difficulty_level = ModelDifficultyLevel[dto.sentence_difficulty_level.upper()]
            except (ValueError, AttributeError, KeyError):
                difficulty_level = None
        
        return SentenceModel(
            text_id=dto.text_id,
            sentence_id=dto.sentence_id,
            sentence_body=dto.sentence_body,
            sentence_difficulty_level=difficulty_level,
            grammar_annotations=grammar_annotations,
            vocab_annotations=vocab_annotations
        )


class TextAdapter:
    """文章适配器"""
    
    @staticmethod
    def model_to_dto(model: TextModel, include_sentences: bool = True) -> TextDTO:
        """
        ORM Model → DTO
        
        参数:
            model: 数据库 ORM 对象
            include_sentences: 是否包含句子（默认包含）
        
        返回:
            TextDTO: 领域数据对象
        
        使用场景:
            - 从数据库查询文章后，返回给 AI 逻辑层
            - API 接口返回数据给前端
        """
        # 转换句子（如果需要）
        sentences = []
        if include_sentences:
            try:
                # 🔧 安全访问 sentences 关系（可能未加载或为 None）
                model_sentences = model.sentences if hasattr(model, 'sentences') and model.sentences else []
                sentences = [
                    SentenceAdapter.model_to_dto(s, include_tokens=True)
                    for s in sorted(model_sentences, key=lambda x: x.sentence_id)
                ]
            except Exception as e:
                # 如果访问 sentences 关系失败，返回空列表
                print(f"⚠️ [TextAdapter] 访问 sentences 关系失败: {e}")
                sentences = []
        
        return TextDTO(
            text_id=model.text_id,
            text_title=model.text_title,
            text_by_sentence=sentences,
            language=model.language
        )
    
    @staticmethod
    def dto_to_model(dto: TextDTO, text_id: Optional[int] = None) -> TextModel:
        """
        DTO → ORM Model
        
        参数:
            dto: 领域数据对象
            text_id: 可选的 text_id（用于更新场景）
        
        返回:
            TextModel: 数据库 ORM 对象
        
        使用场景:
            - 接收前端/AI 层的数据，准备存入数据库
            - 创建或更新文章
        
        注意:
            - 不包含句子的转换（句子需单独处理）
            - text_id 为 None 时表示新建，有值时表示更新
        """
        model = TextModel(
            text_title=dto.text_title,
            language=dto.language
        )
        
        # 如果提供了 text_id，设置它（用于更新场景）
        if text_id is not None:
            model.text_id = text_id
        
        return model
    
    @staticmethod
    def models_to_dtos(models: List[TextModel], include_sentences: bool = False) -> List[TextDTO]:
        """
        批量转换：Models → DTOs
        
        参数:
            models: ORM Model 列表
            include_sentences: 是否包含句子（批量查询时通常不包含，以提升性能）
        
        使用场景:
            - 列表查询、搜索结果返回
        """
        return [
            TextAdapter.model_to_dto(model, include_sentences=include_sentences)
            for model in models
        ]


# ==================== 使用示例（注释） ====================
"""
### 示例 1: 从数据库读取后转为 DTO

```python
from database_system.business_logic.managers import TextManager
from backend.adapters import TextAdapter

# 1. 从数据库查询（返回 Model）
text_manager = TextManager(session)
text_model = text_manager.get_text(text_id=1)

# 2. 转换为 DTO（供 AI 逻辑使用）
text_dto = TextAdapter.model_to_dto(text_model, include_sentences=True)

# 3. 现在可以将 text_dto 传递给 AI 逻辑或返回给前端
return text_dto
```

### 示例 2: 接收 DTO 后存入数据库

```python
from backend.adapters import TextAdapter
from database_system.business_logic.managers import TextManager

# 1. 接收前端/AI 层的 DTO
text_dto = TextDTO(
    text_id=0,  # 新建时为0或不设置
    text_title="示例文章",
    text_by_sentence=[]
)

# 2. 转换为 Model
text_model = TextAdapter.dto_to_model(text_dto)

# 3. 存入数据库（通过 Manager）
text_manager = TextManager(session)
created_text = text_manager.create_text(text_dto.text_title)
```

### 示例 3: 在 data_manager 中使用

```python
# backend/data_managers/original_text_manager_db.py

from backend.adapters import TextAdapter, SentenceAdapter
from database_system.business_logic.managers import TextManager as DBTextManager

class OriginalTextManager:
    def __init__(self, session):
        self.session = session
        self.db_manager = DBTextManager(session)
    
    def get_text(self, text_id: int) -> TextDTO:
        \"\"\"获取文章（返回 DTO）\"\"\"
        # 1. 从数据库获取 Model
        text_model = self.db_manager.get_text(text_id)
        if not text_model:
            return None
        
        # 2. 转换为 DTO 返回
        return TextAdapter.model_to_dto(text_model, include_sentences=True)
    
    def add_text(self, text_title: str) -> TextDTO:
        \"\"\"添加文章（返回 DTO）\"\"\"
        # 1. 通过数据库 Manager 创建（返回 Model）
        text_model = self.db_manager.create_text(text_title)
        
        # 2. 转换为 DTO 返回
        return TextAdapter.model_to_dto(text_model)
```
"""

