#!/usr/bin/env python3
"""
统一标注管理器
提供统一的接口来管理 VocabNotation 和 GrammarNotation
支持向后兼容 AskedToken 系统
"""

import os
from typing import Set, List, Optional, Union, Literal
from datetime import datetime

# 导入各个管理器
try:
    from .vocab_notation_manager import VocabNotationManager, get_vocab_notation_manager
    from .grammar_notation_manager import GrammarNotationManager, get_grammar_notation_manager
    from .asked_tokens_manager import AskedTokensManager, get_asked_tokens_manager
except ImportError:
    from vocab_notation_manager import VocabNotationManager, get_vocab_notation_manager
    from grammar_notation_manager import GrammarNotationManager, get_grammar_notation_manager
    from asked_tokens_manager import AskedTokensManager, get_asked_tokens_manager

# 导入数据结构
try:
    from .data_classes_new import VocabNotation, GrammarNotation, AskedToken
except ImportError:
    from data_classes_new import VocabNotation, GrammarNotation, AskedToken


class UnifiedNotationManager:
    """统一标注管理器"""
    
    def __init__(self, use_database: bool = True, use_legacy_compatibility: bool = True):
        """
        初始化统一管理器
        
        Args:
            use_database: 是否使用数据库存储
            use_legacy_compatibility: 是否启用向后兼容模式
        """
        self.use_database = use_database
        self.use_legacy_compatibility = use_legacy_compatibility
        
        # 初始化各个管理器
        self.vocab_manager = get_vocab_notation_manager(use_database=use_database)
        self.grammar_manager = get_grammar_notation_manager(use_database=use_database)
        
        # 如果需要向后兼容，也初始化 AskedTokensManager
        # 🔧 asked_tokens 现在是 legacy 系统，只使用 JSON 文件，不使用数据库
        if use_legacy_compatibility:
            self.asked_tokens_manager = get_asked_tokens_manager(use_database=False)
        
        print(f"[INFO] [UnifiedNotation] Initialized with database={use_database}, legacy={use_legacy_compatibility}")
    
    def mark_notation(self, notation_type: Literal["vocab", "grammar"], 
                     user_id: str, text_id: int, sentence_id: int,
                     token_id: Optional[int] = None,
                     vocab_id: Optional[int] = None,
                     grammar_id: Optional[int] = None,
                     marked_token_ids: Optional[List[int]] = None,
                     **kwargs) -> bool:
        """
        统一的标注创建接口
        
        Args:
            notation_type: 标注类型，"vocab" 或 "grammar"
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            token_id: Token ID（词汇标注必需）
            vocab_id: 词汇ID（词汇标注可选）
            grammar_id: 语法ID（语法标注可选）
            marked_token_ids: 标记的token ID列表（语法标注可选）
            **kwargs: 其他参数
        """
        print(f"[INFO] [UnifiedNotation] mark_notation called: type={notation_type}")
        
        try:
            if notation_type == "vocab":
                if token_id is None:
                    print(f"[ERROR] [UnifiedNotation] token_id is required for vocab notation")
                    return False
                
                success = self.vocab_manager.create_vocab_notation(
                    user_id=user_id,
                    text_id=text_id,
                    sentence_id=sentence_id,
                    token_id=token_id,
                    vocab_id=vocab_id
                )
                
                # 如果启用向后兼容，同时创建 AskedToken
                if success and self.use_legacy_compatibility:
                    self._create_legacy_asked_token(
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        sentence_token_id=token_id,
                        type="token",
                        vocab_id=vocab_id,
                        grammar_id=None
                    )
                
                return success
                
            elif notation_type == "grammar":
                if marked_token_ids is None:
                    marked_token_ids = []
                
                success = self.grammar_manager.create_grammar_notation(
                    user_id=user_id,
                    text_id=text_id,
                    sentence_id=sentence_id,
                    grammar_id=grammar_id,
                    marked_token_ids=marked_token_ids
                )
                
                # 如果启用向后兼容，同时创建 AskedToken（针对句子）
                if success and self.use_legacy_compatibility:
                    self._create_legacy_asked_token(
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        sentence_token_id=None,
                        type="sentence",
                        vocab_id=None,
                        grammar_id=grammar_id
                    )
                
                return success
            else:
                print(f"[ERROR] [UnifiedNotation] Invalid notation_type: {notation_type}")
                return False
                
        except Exception as e:
            print(f"[ERROR] [UnifiedNotation] Failed to mark notation: {e}")
            return False
    
    def _create_legacy_asked_token(self, user_id: str, text_id: int, sentence_id: int,
                                  sentence_token_id: Optional[int], type: str,
                                  vocab_id: Optional[int], grammar_id: Optional[int]) -> bool:
        """创建向后兼容的 AskedToken"""
        try:
            return self.asked_tokens_manager.mark_token_asked(
                user_id=user_id,
                text_id=text_id,
                sentence_id=sentence_id,
                sentence_token_id=sentence_token_id,
                type=type,
                vocab_id=vocab_id,
                grammar_id=grammar_id
            )
        except Exception as e:
            print(f"[WARN] [UnifiedNotation] Failed to create legacy AskedToken: {e}")
            return False
    
    def get_notations(self, notation_type: Literal["vocab", "grammar", "all"], 
                     text_id: int, user_id: Optional[str] = None) -> Set[str]:
        """
        统一的标注查询接口
        
        Args:
            notation_type: 标注类型，"vocab", "grammar", 或 "all"
            text_id: 文章ID
            user_id: 用户ID（可选）
        """
        print(f"[INFO] [UnifiedNotation] get_notations called: type={notation_type}, text_id={text_id}")
        
        try:
            if notation_type == "vocab":
                return self.vocab_manager.get_vocab_notations_for_article(text_id, user_id)
            elif notation_type == "grammar":
                return self.grammar_manager.get_grammar_notations_for_article(text_id, user_id)
            elif notation_type == "all":
                # 合并所有类型的标注
                vocab_keys = self.vocab_manager.get_vocab_notations_for_article(text_id, user_id)
                grammar_keys = self.grammar_manager.get_grammar_notations_for_article(text_id, user_id)
                
                # 统一键格式：vocab 使用 "text_id:sentence_id:token_id"，grammar 使用 "text_id:sentence_id"
                all_keys = set()
                all_keys.update(vocab_keys)
                all_keys.update(grammar_keys)
                
                return all_keys
            else:
                print(f"[ERROR] [UnifiedNotation] Invalid notation_type: {notation_type}")
                return set()
                
        except Exception as e:
            print(f"[ERROR] [UnifiedNotation] Failed to get notations: {e}")
            return set()
    
    def is_notation_exists(self, notation_type: Literal["vocab", "grammar"],
                          user_id: str, text_id: int, sentence_id: int,
                          token_id: Optional[int] = None) -> bool:
        """
        统一的标注存在性检查接口
        
        Args:
            notation_type: 标注类型，"vocab" 或 "grammar"
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            token_id: Token ID（词汇标注必需）
        """
        print(f"[INFO] [UnifiedNotation] is_notation_exists called: type={notation_type}")
        
        try:
            if notation_type == "vocab":
                if token_id is None:
                    print(f"[ERROR] [UnifiedNotation] token_id is required for vocab notation")
                    return False
                return self.vocab_manager.is_vocab_notation_exists(user_id, text_id, sentence_id, token_id)
            elif notation_type == "grammar":
                return self.grammar_manager.is_grammar_notation_exists(user_id, text_id, sentence_id)
            else:
                print(f"[ERROR] [UnifiedNotation] Invalid notation_type: {notation_type}")
                return False
                
        except Exception as e:
            print(f"[ERROR] [UnifiedNotation] Failed to check notation existence: {e}")
            return False
    
    def delete_notation(self, notation_type: Literal["vocab", "grammar"],
                       user_id: str, notation_key: str) -> bool:
        """
        统一的标注删除接口
        
        Args:
            notation_type: 标注类型，"vocab" 或 "grammar"
            user_id: 用户ID
            notation_key: 标注键（格式：text_id:sentence_id[:token_id]）
        """
        print(f"[INFO] [UnifiedNotation] delete_notation called: type={notation_type}, key={notation_key}")
        
        try:
            if notation_type == "vocab":
                return self.vocab_manager.delete_vocab_notation(user_id, notation_key)
            elif notation_type == "grammar":
                return self.grammar_manager.delete_grammar_notation(user_id, notation_key)
            else:
                print(f"[ERROR] [UnifiedNotation] Invalid notation_type: {notation_type}")
                return False
                
        except Exception as e:
            print(f"[ERROR] [UnifiedNotation] Failed to delete notation: {e}")
            return False
    
    def get_notation_details(self, notation_type: Literal["vocab", "grammar"],
                           user_id: str, text_id: int, sentence_id: int,
                           token_id: Optional[int] = None) -> Optional[Union[VocabNotation, GrammarNotation]]:
        """
        统一的标注详情查询接口
        
        Args:
            notation_type: 标注类型，"vocab" 或 "grammar"
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            token_id: Token ID（词汇标注必需）
        """
        print(f"[INFO] [UnifiedNotation] get_notation_details called: type={notation_type}")
        
        try:
            if notation_type == "vocab":
                if token_id is None:
                    print(f"[ERROR] [UnifiedNotation] token_id is required for vocab notation")
                    return None
                return self.vocab_manager.get_vocab_notation_details(user_id, text_id, sentence_id, token_id)
            elif notation_type == "grammar":
                return self.grammar_manager.get_grammar_notation_details(user_id, text_id, sentence_id)
            else:
                print(f"[ERROR] [UnifiedNotation] Invalid notation_type: {notation_type}")
                return None
                
        except Exception as e:
            print(f"[ERROR] [UnifiedNotation] Failed to get notation details: {e}")
            return None
    
    def migrate_legacy_asked_tokens(self, user_id: str = "default_user") -> bool:
        """
        迁移现有的 AskedToken 数据到新的标注系统
        这是一个一次性操作，用于将现有的 AskedToken 数据迁移到新系统
        
        Args:
            user_id: 要迁移的用户ID
        """
        print(f"[INFO] [UnifiedNotation] Starting migration of legacy AskedToken data for user: {user_id}")
        
        try:
            if not self.use_legacy_compatibility:
                print(f"[WARN] [UnifiedNotation] Legacy compatibility is disabled, skipping migration")
                return True
            
            # 获取现有的 AskedToken 数据
            if self.use_database:
                # 从数据库获取
                import sqlite3
                with sqlite3.connect(self.asked_tokens_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT user_id, text_id, sentence_id, sentence_token_id, type, vocab_id, grammar_id
                        FROM asked_tokens 
                        WHERE user_id = ?
                    """, (user_id,))
                    asked_tokens = cursor.fetchall()
            else:
                # 从 JSON 文件获取
                import json
                file_path = self.asked_tokens_manager._get_json_file_path(user_id)
                if not os.path.exists(file_path):
                    print(f"[INFO] [UnifiedNotation] No legacy data found for user: {user_id}")
                    return True
                
                with open(file_path, "r", encoding="utf-8") as f:
                    asked_tokens_data = json.load(f)
                asked_tokens = [(token["user_id"], token["text_id"], token["sentence_id"], 
                               token["sentence_token_id"], token["type"], token["vocab_id"], token["grammar_id"]) 
                               for token in asked_tokens_data]
            
            migrated_count = 0
            for token_data in asked_tokens:
                user_id, text_id, sentence_id, sentence_token_id, type, vocab_id, grammar_id = token_data
                
                if type == "token" and sentence_token_id is not None:
                    # 迁移为 VocabNotation
                    success = self.vocab_manager.create_vocab_notation(
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        token_id=sentence_token_id,
                        vocab_id=vocab_id
                    )
                    if success:
                        migrated_count += 1
                        print(f"[OK] [UnifiedNotation] Migrated vocab notation: {text_id}:{sentence_id}:{sentence_token_id}")
                
                elif type == "sentence":
                    # 迁移为 GrammarNotation
                    success = self.grammar_manager.create_grammar_notation(
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        grammar_id=grammar_id,
                        marked_token_ids=[]  # 暂时为空，后续可以完善
                    )
                    if success:
                        migrated_count += 1
                        print(f"[OK] [UnifiedNotation] Migrated grammar notation: {text_id}:{sentence_id}")
            
            print(f"[SUCCESS] [UnifiedNotation] Migration completed: {migrated_count} notations migrated")
            return True
            
        except Exception as e:
            print(f"[ERROR] [UnifiedNotation] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False


# 全局实例
_unified_notation_manager = None

def get_unified_notation_manager(use_database: bool = True, use_legacy_compatibility: bool = True) -> UnifiedNotationManager:
    """获取 UnifiedNotationManager 实例"""
    global _unified_notation_manager
    if _unified_notation_manager is None:
        _unified_notation_manager = UnifiedNotationManager(use_database=use_database, use_legacy_compatibility=use_legacy_compatibility)
    return _unified_notation_manager
