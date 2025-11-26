"""
OriginalTextManager - 基于数据库的实现

职责：
1. 对外提供统一的 DTO 接口（data_classes_new.py）
2. 内部调用数据库业务层 Manager
3. 使用 Adapter 进行 Model ↔ DTO 转换
4. 处理业务逻辑和错误

使用场景：
- AI Assistants 调用
- FastAPI 接口调用
- 任何需要文章数据的地方

示例：
    from sqlalchemy.orm import Session
    from backend.data_managers import OriginalTextManagerDB
    
    session = get_session()
    text_manager = OriginalTextManagerDB(session)
    
    # 创建文章
    text = text_manager.add_text("示例文章标题")
    
    # 添加句子
    sentence = text_manager.add_sentence_to_text(
        text_id=text.text_id,
        sentence_text="这是第一个句子。"
    )
    
    # 获取文章及其句子
    text_with_sentences = text_manager.get_text_by_id(text.text_id)
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from backend.data_managers.data_classes_new import (
    OriginalText as TextDTO,
    Sentence as SentenceDTO
)
from backend.adapters.text_adapter import TextAdapter, SentenceAdapter
from database_system.business_logic.managers import TextManager as DBTextManager


class OriginalTextManager:
    """
    文章管理器 - 数据库版本
    
    设计原则：
    - 对外统一返回 DTO（领域对象）
    - 内部使用数据库 Manager 操作
    - 通过 Adapter 转换 Model ↔ DTO
    """
    
    def __init__(self, session: Session):
        """
        初始化文章管理器
        
        参数:
            session: SQLAlchemy Session（数据库会话）
        """
        self.session = session
        self.db_manager = DBTextManager(session)
    
    def add_text(self, text_title: str, user_id: int = None, language: str = None, processing_status: str = 'completed') -> TextDTO:
        """
        创建新文章
        
        参数:
            text_title: 文章标题
            user_id: 用户ID（必填，用于数据隔离）
            language: 语言（中文、英文、德文），可选
            processing_status: 处理状态（processing/completed/failed），默认completed
            
        返回:
            TextDTO: 新创建的文章数据对象
            
        使用示例:
            text = text_manager.add_text("我的第一篇德语文章", user_id=1, language="德文")
            print(f"创建文章ID: {text.text_id}")
        """
        text_model = self.db_manager.create_text(text_title, user_id, language, processing_status)
        return TextAdapter.model_to_dto(text_model, include_sentences=False)
    
    def get_text_by_id(self, text_id: int, include_sentences: bool = True) -> Optional[TextDTO]:
        """
        根据ID获取文章
        
        参数:
            text_id: 文章ID
            include_sentences: 是否包含句子列表（默认包含）
            
        返回:
            TextDTO: 文章数据对象（可能包含句子）
            None: 文章不存在
            
        使用示例:
            # 获取文章及其所有句子
            text = text_manager.get_text_by_id(1)
            if text:
                print(f"文章: {text.text_title}")
                print(f"句子数: {len(text.text_by_sentence)}")
            
            # 只获取文章信息，不包含句子
            text = text_manager.get_text_by_id(1, include_sentences=False)
        """
        text_model = self.db_manager.get_text(text_id)
        if not text_model:
            return None
        
        return TextAdapter.model_to_dto(text_model, include_sentences=include_sentences)
    
    def get_all_texts(self, include_sentences: bool = False, user_id: int = None) -> List[TextDTO]:
        """
        获取所有文章（可选用户过滤）
        
        参数:
            include_sentences: 是否包含句子（默认不包含，提升性能）
            user_id: 用户ID（如果提供，只返回该用户的文章）
            
        返回:
            List[TextDTO]: 文章列表
            
        使用示例:
            # 获取所有文章（不含句子）
            texts = text_manager.get_all_texts()
            for text in texts:
                print(f"{text.text_id}: {text.text_title}")
            
            # 获取特定用户的文章
            texts = text_manager.get_all_texts(user_id=1)
        """
        text_models = self.db_manager.list_texts(user_id=user_id)
        return TextAdapter.models_to_dtos(text_models, include_sentences=include_sentences)
    
    def list_texts(self) -> List[TextDTO]:
        """
        列出所有文章（兼容旧版本接口）
        
        返回:
            List[TextDTO]: 文章列表（不含句子）
        """
        return self.get_all_texts(include_sentences=False)
    
    def search_texts(self, keyword: str, user_id: int = None) -> List[TextDTO]:
        """
        搜索文章（根据标题，可选用户过滤）
        
        参数:
            keyword: 搜索关键词
            user_id: 用户ID（如果提供，只搜索该用户的文章）
            
        返回:
            List[TextDTO]: 匹配的文章列表
            
        使用示例:
            results = text_manager.search_texts("德语")
            for text in results:
                print(f"{text.text_id}: {text.text_title}")
            
            # 搜索特定用户的文章
            results = text_manager.search_texts("德语", user_id=1)
        """
        text_models = self.db_manager.search_texts(keyword, user_id=user_id)
        return TextAdapter.models_to_dtos(text_models, include_sentences=False)
    
    def add_sentence_to_text(self, text_id: int, sentence_text: str,
                            difficulty_level: Optional[str] = None) -> SentenceDTO:
        """
        为文章添加句子
        
        参数:
            text_id: 文章ID
            sentence_text: 句子内容
            difficulty_level: 难度等级（"easy" 或 "hard"），可选
            
        返回:
            SentenceDTO: 新创建的句子
            
        使用示例:
            sentence = text_manager.add_sentence_to_text(
                text_id=1,
                sentence_text="Die Katze schläft auf dem Sofa.",
                difficulty_level="hard"
            )
        """
        # 获取下一个句子ID
        sentence_id = self.get_next_sentence_id(text_id)
        
        # 将difficulty_level转换为大写（数据库枚举需要大写）
        if difficulty_level:
            difficulty_level = difficulty_level.upper()
        
        # 创建句子
        sentence_model = self.db_manager.create_sentence(
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_body=sentence_text,
            difficulty_level=difficulty_level
        )
        
        return SentenceAdapter.model_to_dto(sentence_model)
    
    def get_next_sentence_id(self, text_id: int) -> int:
        """
        获取文章的下一个句子ID
        
        参数:
            text_id: 文章ID
            
        返回:
            int: 下一个句子ID
        """
        sentences = self.db_manager.get_sentences(text_id)
        if not sentences:
            return 1
        return max(s.sentence_id for s in sentences) + 1
    
    def get_sentence(self, text_id: int, sentence_id: int) -> Optional[SentenceDTO]:
        """
        获取指定句子
        
        参数:
            text_id: 文章ID
            sentence_id: 句子ID
            
        返回:
            SentenceDTO: 句子数据对象
            None: 句子不存在
        """
        sentence_model = self.db_manager.get_sentence(text_id, sentence_id)
        if not sentence_model:
            return None
        
        return SentenceAdapter.model_to_dto(sentence_model)
    
    def get_sentences_by_text(self, text_id: int) -> List[SentenceDTO]:
        """
        获取文章的所有句子
        
        参数:
            text_id: 文章ID
            
        返回:
            List[SentenceDTO]: 句子列表
        """
        sentence_models = self.db_manager.get_sentences(text_id)
        return [SentenceAdapter.model_to_dto(s) for s in sentence_models]
    
    def get_text_with_sentences(self, text_id: int) -> Optional[TextDTO]:
        """
        获取文章及其所有句子（完整信息）
        
        参数:
            text_id: 文章ID
            
        返回:
            TextDTO: 包含完整句子的文章对象
            None: 文章不存在
            
        使用示例:
            text = text_manager.get_text_with_sentences(1)
            if text:
                print(f"文章: {text.text_title}")
                print(f"句子数: {len(text.text_by_sentence)}")
                for sentence in text.text_by_sentence:
                    print(f"  {sentence.sentence_id}: {sentence.sentence_body}")
        """
        return self.get_text_by_id(text_id, include_sentences=True)
    
    def add_vocab_example_to_sentence(self, text_id: int, sentence_id: int, vocab_id: int):
        """
        为句子添加词汇标注（兼容旧版本接口）
        
        参数:
            text_id: 文章ID
            sentence_id: 句子ID
            vocab_id: 词汇ID
            
        注意:
            这个方法更新句子的vocab_annotations字段
        """
        sentence_model = self.db_manager.get_sentence(text_id, sentence_id)
        if sentence_model:
            # 获取现有的annotations
            vocab_annotations = sentence_model.vocab_annotations or []
            
            # 添加新的vocab_id（如果不存在）
            if vocab_id not in vocab_annotations:
                vocab_annotations.append(vocab_id)
                
                # 更新数据库
                sentence_model.vocab_annotations = vocab_annotations
                self.session.commit()
    
    def add_grammar_example_to_sentence(self, text_id: int, sentence_id: int, rule_id: int):
        """
        为句子添加语法标注（兼容旧版本接口）
        
        参数:
            text_id: 文章ID
            sentence_id: 句子ID
            rule_id: 语法规则ID
            
        注意:
            这个方法更新句子的grammar_annotations字段
        """
        sentence_model = self.db_manager.get_sentence(text_id, sentence_id)
        if sentence_model:
            # 获取现有的annotations
            grammar_annotations = sentence_model.grammar_annotations or []
            
            # 添加新的rule_id（如果不存在）
            if rule_id not in grammar_annotations:
                grammar_annotations.append(rule_id)
                
                # 更新数据库
                sentence_model.grammar_annotations = grammar_annotations
                self.session.commit()
    
    def get_text_stats(self, user_id: int = None) -> dict:
        """
        获取文章统计信息（可选用户过滤）
        
        参数:
            user_id: 用户ID（如果提供，只统计该用户的文章）
        
        返回:
            dict: 统计信息
                - total_texts: 总文章数
                - total_sentences: 总句子数
                
        使用示例:
            stats = text_manager.get_text_stats()
            print(f"总文章: {stats['total_texts']}")
            print(f"总句子: {stats['total_sentences']}")
            
            # 统计特定用户的文章
            stats = text_manager.get_text_stats(user_id=1)
        """
        return self.db_manager.get_text_stats(user_id=user_id)
    
    def get_new_text_id(self) -> int:
        """
        获取新文章ID（兼容旧版本）
        
        注意：数据库版本中，ID 由数据库自动生成，此方法仅用于兼容
        """
        # 数据库会自动生成ID，这里返回下一个可能的ID（仅供参考）
        texts = self.get_all_texts()
        if not texts:
            return 1
        return max(t.text_id for t in texts) + 1
    
    def update_text(self, text_id: int, text_title: str = None, language: str = None, processing_status: str = None) -> Optional[TextDTO]:
        """
        更新文章
        
        参数:
            text_id: 文章ID
            text_title: 新标题（可选）
            language: 新语言（可选）
            processing_status: 新处理状态（可选）
            
        返回:
            TextDTO: 更新后的文章数据对象
            None: 文章不存在
            
        使用示例:
            text = text_manager.update_text(1, text_title="新标题")
        """
        text_model = self.db_manager.update_text(text_id, text_title, language, processing_status)
        if not text_model:
            return None
        return TextAdapter.model_to_dto(text_model, include_sentences=False)
    
    def delete_text(self, text_id: int) -> bool:
        """
        删除文章
        
        参数:
            text_id: 文章ID
            
        返回:
            bool: 是否删除成功
            
        使用示例:
            success = text_manager.delete_text(1)
            if success:
                print("文章已删除")
        """
        return self.db_manager.delete_text(text_id)

