"""
VocabManager - 基于数据库的实现

职责：
1. 对外提供统一的 DTO 接口（data_classes_new.py）
2. 内部调用数据库业务层 Manager
3. 使用 Adapter 进行 Model ↔ DTO 转换
4. 处理业务逻辑和错误

使用场景：
- AI Assistants 调用
- FastAPI 接口调用
- 任何需要词汇数据的地方

示例：
    from sqlalchemy.orm import Session
    from backend.data_managers import VocabManagerDB
    
    session = get_session()
    vocab_manager = VocabManagerDB(session)
    
    # 获取词汇
    vocab = vocab_manager.get_vocab_by_id(1)
    
    # 添加词汇
    new_vocab = vocab_manager.add_new_vocab("hello", "问候语")
    
    # 搜索词汇
    results = vocab_manager.search_vocabs("hello")
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from backend.data_managers.data_classes_new import (
    VocabExpression as VocabDTO,
    VocabExpressionExample as VocabExampleDTO
)
from backend.adapters import VocabAdapter, VocabExampleAdapter
from database_system.business_logic.managers import VocabManager as DBVocabManager


class VocabManager:
    """
    词汇管理器 - 数据库版本
    
    设计原则：
    - 对外统一返回 DTO（领域对象）
    - 内部使用数据库 Manager 操作
    - 通过 Adapter 转换 Model ↔ DTO
    """
    
    def __init__(self, session: Session):
        """
        初始化词汇管理器
        
        参数:
            session: SQLAlchemy Session（数据库会话）
        """
        self.session = session
        self.db_manager = DBVocabManager(session)
    
    def get_vocab_by_id(self, vocab_id: int) -> Optional[VocabDTO]:
        """
        根据ID获取词汇
        
        参数:
            vocab_id: 词汇ID
            
        返回:
            VocabDTO: 词汇数据对象（包含例句）
            None: 词汇不存在
            
        使用示例:
            vocab = vocab_manager.get_vocab_by_id(1)
            if vocab:
                print(f"{vocab.vocab_body}: {vocab.explanation}")
        """
        vocab_model = self.db_manager.get_vocab(vocab_id)
        if not vocab_model:
            return None
        
        return VocabAdapter.model_to_dto(vocab_model, include_examples=True)
    
    def get_vocab_by_body(self, vocab_body: str) -> Optional[VocabDTO]:
        """
        根据词汇内容查找
        
        参数:
            vocab_body: 词汇内容（如 "hello"）
            
        返回:
            VocabDTO: 词汇数据对象
            None: 词汇不存在
        """
        vocab_model = self.db_manager.find_vocab_by_body(vocab_body)
        if not vocab_model:
            return None
        
        return VocabAdapter.model_to_dto(vocab_model, include_examples=True)
    
    def add_new_vocab(self, vocab_body: str, explanation: str, 
                      source: str = "qa", is_starred: bool = False) -> VocabDTO:
        """
        添加新词汇
        
        参数:
            vocab_body: 词汇内容
            explanation: 词汇解释
            source: 来源（"auto", "qa", "manual"），默认 "qa"
            is_starred: 是否收藏，默认 False
            
        返回:
            VocabDTO: 新创建的词汇数据对象
            
        使用示例:
            new_vocab = vocab_manager.add_new_vocab(
                vocab_body="challenging",
                explanation="具有挑战性的",
                source="manual",
                is_starred=True
            )
            print(f"创建词汇ID: {new_vocab.vocab_id}")
        """
        vocab_model = self.db_manager.add_vocab(
            vocab_body=vocab_body,
            explanation=explanation,
            source=source,
            is_starred=is_starred
        )
        
        return VocabAdapter.model_to_dto(vocab_model)
    
    def get_all_vocabs(self, skip: int = 0, limit: int = 100, 
                       starred_only: bool = False) -> List[VocabDTO]:
        """
        获取所有词汇（分页）
        
        参数:
            skip: 跳过的记录数（用于分页）
            limit: 返回的最大记录数
            starred_only: 是否只返回收藏的词汇
            
        返回:
            List[VocabDTO]: 词汇列表（不包含例句，提升性能）
            
        使用示例:
            # 获取前20个词汇
            vocabs = vocab_manager.get_all_vocabs(skip=0, limit=20)
            
            # 获取收藏的词汇
            starred = vocab_manager.get_all_vocabs(starred_only=True)
        """
        vocab_models = self.db_manager.list_vocabs(
            skip=skip, 
            limit=limit, 
            starred_only=starred_only
        )
        
        # 批量转换，不包含例句以提升性能
        return VocabAdapter.models_to_dtos(vocab_models, include_examples=False)
    
    def get_all_vocab_body(self) -> List[str]:
        """
        获取所有词汇的词汇体（用于快速查找）
        
        返回:
            List[str]: 词汇内容列表
            
        使用示例:
            vocab_bodies = vocab_manager.get_all_vocab_body()
            if "hello" in vocab_bodies:
                print("词汇已存在")
        """
        vocabs = self.get_all_vocabs(limit=10000)  # 获取所有
        return [vocab.vocab_body for vocab in vocabs]
    
    def search_vocabs(self, keyword: str) -> List[VocabDTO]:
        """
        搜索词汇（根据词汇内容或解释）
        
        参数:
            keyword: 搜索关键词
            
        返回:
            List[VocabDTO]: 匹配的词汇列表
            
        使用示例:
            results = vocab_manager.search_vocabs("挑战")
            for vocab in results:
                print(f"{vocab.vocab_body}: {vocab.explanation}")
        """
        vocab_models = self.db_manager.search_vocabs(keyword)
        return VocabAdapter.models_to_dtos(vocab_models, include_examples=False)
    
    def update_vocab(self, vocab_id: int, **kwargs) -> Optional[VocabDTO]:
        """
        更新词汇
        
        参数:
            vocab_id: 词汇ID
            **kwargs: 要更新的字段（vocab_body, explanation, source, is_starred）
            
        返回:
            VocabDTO: 更新后的词汇
            None: 词汇不存在
            
        使用示例:
            updated = vocab_manager.update_vocab(
                vocab_id=1,
                explanation="新的解释",
                is_starred=True
            )
        """
        vocab_model = self.db_manager.update_vocab(vocab_id, **kwargs)
        if not vocab_model:
            return None
        
        return VocabAdapter.model_to_dto(vocab_model)
    
    def delete_vocab(self, vocab_id: int) -> bool:
        """
        删除词汇
        
        参数:
            vocab_id: 词汇ID
            
        返回:
            bool: 是否删除成功
            
        使用示例:
            success = vocab_manager.delete_vocab(1)
            if success:
                print("删除成功")
        """
        return self.db_manager.delete_vocab(vocab_id)
    
    def toggle_star(self, vocab_id: int) -> bool:
        """
        切换词汇的收藏状态
        
        参数:
            vocab_id: 词汇ID
            
        返回:
            bool: 切换后的收藏状态（True=已收藏, False=未收藏）
            
        使用示例:
            is_starred = vocab_manager.toggle_star(1)
            print(f"收藏状态: {'已收藏' if is_starred else '未收藏'}")
        """
        return self.db_manager.toggle_star(vocab_id)
    
    def get_id_by_vocab_body(self, vocab_body: str) -> Optional[int]:
        """
        根据词汇内容获取ID
        
        参数:
            vocab_body: 词汇内容
            
        返回:
            int: 词汇ID
            None: 词汇不存在
            
        使用示例:
            vocab_id = vocab_manager.get_id_by_vocab_body("hello")
            if vocab_id:
                print(f"词汇ID: {vocab_id}")
        """
        vocab = self.get_vocab_by_body(vocab_body)
        return vocab.vocab_id if vocab else None
    
    def add_vocab_example(self, vocab_id: int, text_id: int, 
                         sentence_id: int, context_explanation: str,
                         token_indices: Optional[List[int]] = None) -> VocabExampleDTO:
        """
        为词汇添加例句
        
        参数:
            vocab_id: 词汇ID
            text_id: 文章ID
            sentence_id: 句子ID
            context_explanation: 上下文解释
            token_indices: 关联的token索引列表
            
        返回:
            VocabExampleDTO: 新创建的例句
            
        使用示例:
            example = vocab_manager.add_vocab_example(
                vocab_id=1,
                text_id=1,
                sentence_id=5,
                context_explanation="在这个句子中...",
                token_indices=[3, 4]
            )
        """
        # ✅ 通过数据库 Manager 的公开方法创建例句
        example_model = self.db_manager.add_vocab_example(
            vocab_id=vocab_id,
            text_id=text_id,
            sentence_id=sentence_id,
            context_explanation=context_explanation,
            token_indices=token_indices or []
        )
        
        return VocabExampleAdapter.model_to_dto(example_model)
    
    def get_examples_by_vocab_id(self, vocab_id: int) -> List[VocabExampleDTO]:
        """
        获取词汇的所有例句
        
        参数:
            vocab_id: 词汇ID
            
        返回:
            List[VocabExampleDTO]: 例句列表
            
        使用示例:
            examples = vocab_manager.get_examples_by_vocab_id(1)
            for ex in examples:
                print(f"文章{ex.text_id}, 句子{ex.sentence_id}")
        """
        vocab = self.get_vocab_by_id(vocab_id)
        return vocab.examples if vocab else []
    
    def get_vocab_with_examples(self, vocab_id: int) -> Optional[VocabDTO]:
        """
        获取词汇及其例句（完整信息）
        
        参数:
            vocab_id: 词汇ID
            
        返回:
            VocabDTO: 包含完整例句的词汇对象
            None: 词汇不存在
            
        使用示例:
            vocab = vocab_manager.get_vocab_with_examples(1)
            if vocab:
                print(f"词汇: {vocab.vocab_body}")
                print(f"例句数量: {len(vocab.examples)}")
        """
        return self.get_vocab_by_id(vocab_id)  # 已经包含例句
    
    def get_vocab_stats(self) -> dict:
        """
        获取词汇统计信息
        
        返回:
            dict: 统计信息
                - total: 总词汇数
                - starred: 收藏词汇数
                - auto: 自动生成的词汇数
                - manual: 手动添加的词汇数
                
        使用示例:
            stats = vocab_manager.get_vocab_stats()
            print(f"总词汇: {stats['total']}")
            print(f"收藏词汇: {stats['starred']}")
        """
        return self.db_manager.get_vocab_stats()


# ==================== 兼容性方法（可选） ====================
# 如果需要与旧版本 VocabManager 完全兼容，可以添加以下方法：

    def get_new_vocab_id(self) -> int:
        """
        获取新词汇ID（兼容旧版本）
        
        注意：数据库版本中，ID 由数据库自动生成，此方法仅用于兼容
        """
        # 数据库会自动生成ID，这里返回下一个可能的ID（仅供参考）
        stats = self.get_vocab_stats()
        return stats.get('total', 0) + 1
