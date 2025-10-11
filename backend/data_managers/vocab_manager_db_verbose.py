"""
VocabManager - 基于数据库的实现（详细日志版本）

展示完整的数据转换过程，用于学习和调试
"""

from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.data_managers.data_classes_new import (
    VocabExpression as VocabDTO,
    VocabExpressionExample as VocabExampleDTO
)
from backend.adapters import VocabAdapter, VocabExampleAdapter
from database_system.business_logic.managers import VocabManager as DBVocabManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class VocabManager:
    """
    词汇管理器 - 数据库版本（带详细日志）
    """
    
    def __init__(self, session: Session, verbose: bool = True):
        """
        初始化词汇管理器
        
        参数:
            session: SQLAlchemy Session
            verbose: 是否显示详细日志
        """
        self.session = session
        self.db_manager = DBVocabManager(session)
        self.verbose = verbose
        
        if self.verbose:
            logger.info("=" * 70)
            logger.info("[VocabManagerDB] 初始化完成")
            logger.info(f"  Session类型: {type(session).__name__}")
            logger.info(f"  DB Manager类型: {type(self.db_manager).__name__}")
            logger.info("=" * 70)
    
    def _log(self, message: str, level: str = "INFO"):
        """内部日志方法"""
        if self.verbose:
            prefix = {
                "INFO": "[INFO]",
                "STEP": "[STEP]",
                "DATA": "[DATA]",
                "CONV": "[CONVERT]",
            }.get(level, "[INFO]")
            logger.info(f"{prefix} {message}")
    
    def get_vocab_by_id(self, vocab_id: int) -> Optional[VocabDTO]:
        """
        根据ID获取词汇（带详细日志）
        """
        self._log(f"\n{'='*70}")
        self._log(f"开始获取词汇: ID={vocab_id}", "STEP")
        self._log(f"{'='*70}")
        
        # 步骤1: 从数据库获取Model
        self._log("\n[步骤1] 从数据库获取 ORM Model", "STEP")
        self._log("  调用: db_manager.get_vocab(vocab_id)")
        
        vocab_model = self.db_manager.get_vocab(vocab_id)
        
        if not vocab_model:
            self._log(f"  结果: 未找到 ID={vocab_id} 的词汇")
            return None
        
        self._log(f"  结果: 成功获取 VocabModel")
        self._log(f"  Model类型: {type(vocab_model).__name__}", "DATA")
        self._log(f"  Model模块: {type(vocab_model).__module__}", "DATA")
        
        # 显示Model的关键字段
        self._log("\n[步骤1.1] VocabModel 字段详情:", "DATA")
        self._log(f"  vocab_id: {vocab_model.vocab_id}")
        self._log(f"  vocab_body: {vocab_model.vocab_body}")
        self._log(f"  explanation: {vocab_model.explanation[:50]}..." if len(vocab_model.explanation) > 50 else f"  explanation: {vocab_model.explanation}")
        self._log(f"  source: {vocab_model.source} (类型: {type(vocab_model.source).__name__})")
        self._log(f"  source.value: {vocab_model.source.value}")
        self._log(f"  source.name: {vocab_model.source.name}")
        self._log(f"  is_starred: {vocab_model.is_starred}")
        self._log(f"  examples数量: {len(vocab_model.examples) if vocab_model.examples else 0}")
        
        # 步骤2: 使用Adapter转换为DTO
        self._log("\n[步骤2] 使用 VocabAdapter 转换: Model → DTO", "STEP")
        self._log("  调用: VocabAdapter.model_to_dto(vocab_model, include_examples=True)")
        
        self._log("\n[步骤2.1] Adapter 内部操作:", "CONV")
        self._log("  1. 转换基本字段 (vocab_id, vocab_body, explanation)")
        self._log("  2. 转换 source: SourceType枚举 → 字符串")
        self._log(f"     {vocab_model.source} → '{vocab_model.source.value.lower()}'")
        self._log("  3. 转换 examples: SQLAlchemy关系 → List[VocabExampleDTO]")
        
        vocab_dto = VocabAdapter.model_to_dto(vocab_model, include_examples=True)
        
        self._log("\n[步骤2.2] 转换完成，得到 VocabDTO:", "CONV")
        self._log(f"  DTO类型: {type(vocab_dto).__name__}", "DATA")
        self._log(f"  DTO模块: {type(vocab_dto).__module__}", "DATA")
        
        # 显示DTO的关键字段
        self._log("\n[步骤2.3] VocabDTO 字段详情:", "DATA")
        self._log(f"  vocab_id: {vocab_dto.vocab_id}")
        self._log(f"  vocab_body: {vocab_dto.vocab_body}")
        self._log(f"  explanation: {vocab_dto.explanation[:50]}..." if len(vocab_dto.explanation) > 50 else f"  explanation: {vocab_dto.explanation}")
        self._log(f"  source: '{vocab_dto.source}' (类型: {type(vocab_dto.source).__name__})")
        self._log(f"  is_starred: {vocab_dto.is_starred}")
        self._log(f"  examples: {len(vocab_dto.examples)} 个 (类型: {type(vocab_dto.examples).__name__})")
        
        # 显示转换前后对比
        self._log("\n[步骤3] 转换前后对比:", "CONV")
        self._log(f"  字段          | Model                          | DTO")
        self._log(f"  ------------- | ------------------------------ | -------------------")
        self._log(f"  类型          | {type(vocab_model).__name__:30} | {type(vocab_dto).__name__}")
        self._log(f"  source        | {str(vocab_model.source):30} | '{vocab_dto.source}'")
        self._log(f"  source类型    | {type(vocab_model.source).__name__:30} | {type(vocab_dto.source).__name__}")
        self._log(f"  examples类型  | SQLAlchemy关系                   | list")
        
        self._log("\n[关键转换]:", "CONV")
        self._log(f"  1. source枚举 → 字符串: {vocab_model.source} → '{vocab_dto.source}'")
        self._log(f"  2. ORM Model → dataclass DTO")
        self._log(f"  3. 数据库对象 → 可序列化对象")
        
        self._log(f"\n{'='*70}")
        self._log(f"[完成] 返回 VocabDTO 给 FastAPI", "STEP")
        self._log(f"{'='*70}\n")
        
        return vocab_dto
    
    def get_all_vocabs(self, skip: int = 0, limit: int = 100, 
                       starred_only: bool = False) -> List[VocabDTO]:
        """
        获取所有词汇（带日志）
        """
        self._log(f"\n{'='*70}")
        self._log(f"获取词汇列表: skip={skip}, limit={limit}, starred_only={starred_only}", "STEP")
        self._log(f"{'='*70}")
        
        self._log("\n[步骤1] 从数据库获取 Model 列表", "STEP")
        vocab_models = self.db_manager.list_vocabs(skip=skip, limit=limit, starred_only=starred_only)
        self._log(f"  获取到 {len(vocab_models)} 个 VocabModel")
        
        self._log("\n[步骤2] 批量转换: Models → DTOs", "STEP")
        self._log("  调用: VocabAdapter.models_to_dtos(vocab_models, include_examples=False)")
        
        vocabs_dto = VocabAdapter.models_to_dtos(vocab_models, include_examples=False)
        
        self._log(f"  转换完成: {len(vocabs_dto)} 个 VocabDTO")
        
        if vocabs_dto:
            self._log("\n[示例] 第一个词汇的转换:", "DATA")
            self._log(f"  Model.source: {vocab_models[0].source}")
            self._log(f"  DTO.source: '{vocabs_dto[0].source}'")
        
        self._log(f"\n[完成] 返回 {len(vocabs_dto)} 个 VocabDTO\n", "STEP")
        
        return vocabs_dto
    
    def add_new_vocab(self, vocab_body: str, explanation: str, 
                      source: str = "qa", is_starred: bool = False) -> VocabDTO:
        """
        添加新词汇（带日志）
        """
        self._log(f"\n{'='*70}")
        self._log(f"创建新词汇: '{vocab_body}'", "STEP")
        self._log(f"{'='*70}")
        
        self._log("\n[步骤1] 调用数据库 Manager 创建", "STEP")
        self._log(f"  参数:")
        self._log(f"    vocab_body: '{vocab_body}'")
        self._log(f"    explanation: '{explanation}'")
        self._log(f"    source: '{source}' (字符串)")
        self._log(f"    is_starred: {is_starred}")
        
        vocab_model = self.db_manager.add_vocab(
            vocab_body=vocab_body,
            explanation=explanation,
            source=source,
            is_starred=is_starred
        )
        
        self._log(f"\n[步骤1.1] 数据库 Manager 内部操作:", "CONV")
        self._log(f"  1. 将 source字符串 '{source}' 转换为 SourceType枚举")
        self._log(f"  2. 创建 VocabModel 对象")
        self._log(f"  3. 保存到数据库（session.add + flush）")
        self._log(f"  4. 数据库自动生成 ID: {vocab_model.vocab_id}")
        
        self._log("\n[步骤2] 转换为 DTO 返回", "STEP")
        vocab_dto = VocabAdapter.model_to_dto(vocab_model)
        
        self._log(f"  Model.source: {vocab_model.source} (枚举)")
        self._log(f"  DTO.source: '{vocab_dto.source}' (字符串)")
        
        self._log(f"\n[完成] 返回新创建的 VocabDTO (ID={vocab_dto.vocab_id})\n", "STEP")
        
        return vocab_dto
    
    # 其他方法保持不变，使用原始实现
    def get_vocab_by_body(self, vocab_body: str) -> Optional[VocabDTO]:
        vocab_model = self.db_manager.find_vocab_by_body(vocab_body)
        if not vocab_model:
            return None
        return VocabAdapter.model_to_dto(vocab_model, include_examples=True)
    
    def update_vocab(self, vocab_id: int, **kwargs) -> Optional[VocabDTO]:
        vocab_model = self.db_manager.update_vocab(vocab_id, **kwargs)
        if not vocab_model:
            return None
        return VocabAdapter.model_to_dto(vocab_model)
    
    def delete_vocab(self, vocab_id: int) -> bool:
        return self.db_manager.delete_vocab(vocab_id)
    
    def toggle_star(self, vocab_id: int) -> bool:
        return self.db_manager.toggle_star(vocab_id)
    
    def get_id_by_vocab_body(self, vocab_body: str) -> Optional[int]:
        vocab = self.get_vocab_by_body(vocab_body)
        return vocab.vocab_id if vocab else None
    
    def add_vocab_example(self, vocab_id: int, text_id: int, 
                         sentence_id: int, context_explanation: str,
                         token_indices: Optional[List[int]] = None) -> VocabExampleDTO:
        example_model = self.db_manager.add_vocab_example(
            vocab_id=vocab_id,
            text_id=text_id,
            sentence_id=sentence_id,
            context_explanation=context_explanation,
            token_indices=token_indices or []
        )
        return VocabExampleAdapter.model_to_dto(example_model)
    
    def get_examples_by_vocab_id(self, vocab_id: int) -> List[VocabExampleDTO]:
        vocab = self.get_vocab_by_id(vocab_id)
        return vocab.examples if vocab else []
    
    def get_vocab_with_examples(self, vocab_id: int) -> Optional[VocabDTO]:
        return self.get_vocab_by_id(vocab_id)
    
    def get_vocab_stats(self) -> dict:
        return self.db_manager.get_vocab_stats()
    
    def get_new_vocab_id(self) -> int:
        stats = self.get_vocab_stats()
        return stats.get('total', 0) + 1

