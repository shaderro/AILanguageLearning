#!/usr/bin/env python3
"""
Vocab Notation 数据管理器
支持 JSON 文件和 SQLite 数据库两种存储方式
用于管理词汇知识点标注
"""

import json
import os
import sqlite3
from typing import Set, List, Optional
from dataclasses import asdict
from datetime import datetime

# 从 data_classes_new 导入 VocabNotation
import sys
import os
sys.path.append(os.path.dirname(__file__))
from data_classes_new import VocabNotation


class VocabNotationManager:
    """Vocab Notation 数据管理器"""
    
    def __init__(self, use_database: bool = True, db_path: str = None, json_dir: str = None):
        self.use_database = use_database
        
        if use_database:
            # SQLite 数据库模式
            if db_path is None:
                current_dir = os.path.dirname(os.path.dirname(__file__))
                db_path = os.path.join(current_dir, "database_system", "data_storage", "data", "language_learning.db")
            
            self.db_path = db_path
            self._init_database()
        else:
            # JSON 文件模式
            if json_dir is None:
                current_dir = os.path.dirname(os.path.dirname(__file__))
                json_dir = os.path.join(current_dir, "data", "current", "vocab_notations")
            
            self.json_dir = json_dir
            os.makedirs(self.json_dir, exist_ok=True)
            # Debug logging removed for performance
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vocab_notations (
                        user_id TEXT NOT NULL,
                        text_id INTEGER NOT NULL,
                        sentence_id INTEGER NOT NULL,
                        token_id INTEGER NOT NULL,
                        vocab_id INTEGER,
                        created_at TEXT,
                        PRIMARY KEY (user_id, text_id, sentence_id, token_id)
                    )
                """)
                conn.commit()
                # Debug logging removed for performance
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Database initialization failed: {e}")
            raise
    
    def _get_json_file_path(self, user_id: str) -> str:
        """获取用户的 JSON 文件路径"""
        return os.path.join(self.json_dir, f"{user_id}.json")
    
    def create_vocab_notation(self, user_id: str, text_id: int, sentence_id: int, 
                             token_id: int, vocab_id: Optional[int] = None) -> bool:
        """
        创建词汇标注
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            token_id: Token ID（当前句子中哪个token）
            vocab_id: 词汇ID（可选）
        """
        print(f"[INFO] [VocabNotation] create_vocab_notation called:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - token_id: {token_id}")
        print(f"  - vocab_id: {vocab_id}")
        
        try:
            vocab_notation = VocabNotation(
                user_id=user_id,
                text_id=text_id,
                sentence_id=sentence_id,
                token_id=token_id,
                vocab_id=vocab_id,
                created_at=datetime.now().isoformat()
            )
            
            if self.use_database:
                return self._create_vocab_notation_database(vocab_notation)
            else:
                return self._create_vocab_notation_json(vocab_notation)
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Failed to create vocab notation: {e}")
            return False
    
    def _create_vocab_notation_database(self, vocab_notation: VocabNotation) -> bool:
        """数据库模式：创建词汇标注（使用主 ORM）"""
        try:
            # 使用主数据库的 ORM Session
            from database_system.database_manager import DatabaseManager
            db_manager = DatabaseManager('development')
            session = db_manager.get_session()
            
            try:
                from database_system.business_logic.crud.notation_crud import VocabNotationCRUD
                crud = VocabNotationCRUD(session)
                
                # 检查是否已存在
                if crud.exists(vocab_notation.user_id, vocab_notation.text_id, 
                              vocab_notation.sentence_id, vocab_notation.token_id):
                    print(f"[INFO] [VocabNotation] Already exists: {vocab_notation.text_id}:{vocab_notation.sentence_id}:{vocab_notation.token_id}")
                    session.close()
                    return True
                
                # 创建新标注
                crud.create(
                    user_id=vocab_notation.user_id,
                    text_id=vocab_notation.text_id,
                    sentence_id=vocab_notation.sentence_id,
                    token_id=vocab_notation.token_id,
                    vocab_id=vocab_notation.vocab_id
                )
                print(f"[OK] [VocabNotation] Created vocab notation in ORM: {vocab_notation.text_id}:{vocab_notation.sentence_id}:{vocab_notation.token_id}")
                session.close()
                return True
            except Exception as e:
                session.rollback()
                session.close()
                raise e
        except Exception as e:
            print(f"[ERROR] [VocabNotation] ORM creation failed: {e}")
            return False
    
    def _create_vocab_notation_json(self, vocab_notation: VocabNotation) -> bool:
        """JSON 文件模式：创建词汇标注"""
        try:
            file_path = self._get_json_file_path(vocab_notation.user_id)
            print(f"[INFO] [VocabNotation] JSON file path: {file_path}")
            
            # 读取现有数据
            vocab_notations = []
            if os.path.exists(file_path):
                print(f"[READ] [VocabNotation] Reading existing file: {file_path}")
                with open(file_path, "r", encoding="utf-8") as f:
                    vocab_notations = json.load(f)
                print(f"[DATA] [VocabNotation] Existing notations count: {len(vocab_notations)}")
            else:
                print(f"[WRITE] [VocabNotation] Creating new file: {file_path}")
            
            # 检查是否已存在
            notation_key = f"{vocab_notation.text_id}:{vocab_notation.sentence_id}:{vocab_notation.token_id}"
            existing = False
            for notation_data in vocab_notations:
                if (notation_data.get("text_id") == vocab_notation.text_id and
                    notation_data.get("sentence_id") == vocab_notation.sentence_id and
                    notation_data.get("token_id") == vocab_notation.token_id):
                    existing = True
                    print(f"[WARN] [VocabNotation] Already exists: {notation_key}")
                    break
            
            if not existing:
                # 添加新标注
                vocab_notations.append(asdict(vocab_notation))
                print(f"[ADD] [VocabNotation] Added new notation: {notation_key}")
            else:
                # 更新现有标注
                for notation_data in vocab_notations:
                    if (notation_data.get("text_id") == vocab_notation.text_id and
                        notation_data.get("sentence_id") == vocab_notation.sentence_id and
                        notation_data.get("token_id") == vocab_notation.token_id):
                        notation_data.update(asdict(vocab_notation))
                        print(f"[REFRESH] [VocabNotation] Updated existing notation: {notation_key}")
                        break
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(vocab_notations, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] [VocabNotation] Created vocab notation in JSON: {notation_key}")
            return True
        except Exception as e:
            print(f"[ERROR] [VocabNotation] JSON creation failed: {e}")
            return False
    
    def is_vocab_notation_exists(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> bool:
        """检查词汇标注是否存在"""
        try:
            if self.use_database:
                return self._check_vocab_notation_database(user_id, text_id, sentence_id, token_id)
            else:
                return self._check_vocab_notation_json(user_id, text_id, sentence_id, token_id)
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Failed to check vocab notation: {e}")
            return False
    
    def _check_vocab_notation_database(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> bool:
        """数据库模式：检查词汇标注是否存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM vocab_notations 
                    WHERE user_id = ? AND text_id = ? AND sentence_id = ? AND token_id = ?
                """, (user_id, text_id, sentence_id, token_id))
                
                count = cursor.fetchone()[0]
                exists = count > 0
                print(f"[SEARCH] [VocabNotation] Database check result: {exists}")
                return exists
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Database check failed: {e}")
            return False
    
    def _check_vocab_notation_json(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> bool:
        """JSON 文件模式：检查词汇标注是否存在"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, "r", encoding="utf-8") as f:
                vocab_notations = json.load(f)
            
            for notation_data in vocab_notations:
                if (notation_data.get("text_id") == text_id and
                    notation_data.get("sentence_id") == sentence_id and
                    notation_data.get("token_id") == token_id):
                    print(f"[SEARCH] [VocabNotation] JSON check result: True")
                    return True
            
            print(f"[SEARCH] [VocabNotation] JSON check result: False")
            return False
        except Exception as e:
            print(f"[ERROR] [VocabNotation] JSON check failed: {e}")
            return False
    
    def get_vocab_notations_for_article(self, text_id: int, user_id: Optional[str] = None) -> Set[str]:
        """
        获取指定文章的词汇标注键集合
        
        Args:
            text_id: 文章ID
            user_id: 用户ID（可选，如果为None则获取所有用户的数据）
        """
        print(f"[INFO] [VocabNotation] get_vocab_notations_for_article called for text_id: {text_id}, user_id: {user_id}")
        
        try:
            if self.use_database:
                if user_id:
                    return self._get_vocab_notations_database(user_id, text_id)
                else:
                    return self._get_vocab_notations_database_all_users(text_id)
            else:
                if user_id:
                    return self._get_vocab_notations_json(user_id, text_id)
                else:
                    return self._get_vocab_notations_json_all_users(text_id)
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Failed to get vocab notations: {e}")
            return set()
    
    def _get_vocab_notations_database(self, user_id: str, text_id: int) -> Set[str]:
        """数据库模式：获取词汇标注键（使用主 ORM）"""
        try:
            from database_system.database_manager import DatabaseManager
            from database_system.business_logic.crud.notation_crud import VocabNotationCRUD
            
            db_manager = DatabaseManager('development')
            session = db_manager.get_session()
            
            try:
                crud = VocabNotationCRUD(session)
                notations = crud.get_by_text(text_id, user_id)
                keys = {f"{n.text_id}:{n.sentence_id}:{n.token_id}" for n in notations}
                print(f"[OK] [VocabNotation] Retrieved {len(keys)} vocab notations from ORM")
                session.close()
                return keys
            except Exception as e:
                session.close()
                raise e
        except Exception as e:
            print(f"[ERROR] [VocabNotation] ORM query failed: {e}")
            return set()
    
    def _get_vocab_notations_database_all_users(self, text_id: int) -> Set[str]:
        """数据库模式：获取所有用户在指定文章下的词汇标注键（使用主 ORM）"""
        try:
            from database_system.database_manager import DatabaseManager
            from database_system.business_logic.crud.notation_crud import VocabNotationCRUD
            
            db_manager = DatabaseManager('development')
            session = db_manager.get_session()
            
            try:
                crud = VocabNotationCRUD(session)
                notations = crud.get_by_text(text_id, user_id=None)
                keys = {f"{n.text_id}:{n.sentence_id}:{n.token_id}" for n in notations}
                print(f"[OK] [VocabNotation] Retrieved {len(keys)} vocab notations from ORM (all users)")
                session.close()
                return keys
            except Exception as e:
                session.close()
                raise e
        except Exception as e:
            print(f"[ERROR] [VocabNotation] ORM query failed: {e}")
            return set()
    
    def _get_vocab_notations_json_all_users(self, text_id: int) -> Set[str]:
        """JSON 文件模式：获取所有用户在指定文章下的词汇标注键"""
        print(f"[INFO] [VocabNotation] _get_vocab_notations_json_all_users called for text_id: {text_id}")
        
        try:
            keys = set()
            
            # 扫描所有用户的 JSON 文件
            if not os.path.exists(self.json_dir):
                print(f"[WARN] [VocabNotation] JSON directory does not exist: {self.json_dir}")
                return keys
            
            print(f"[DIR] [VocabNotation] Scanning directory: {self.json_dir}")
            for filename in os.listdir(self.json_dir):
                if filename.endswith('.json'):
                    user_file_path = os.path.join(self.json_dir, filename)
                    print(f"[READ] [VocabNotation] Reading user file: {filename}")
                    
                    try:
                        with open(user_file_path, "r", encoding="utf-8") as f:
                            user_notations = json.load(f)
                        
                        print(f"[DATA] [VocabNotation] User {filename} has {len(user_notations)} notations")
                        
                        for notation_data in user_notations:
                            if notation_data.get("text_id") == text_id:
                                key = f"{notation_data['text_id']}:{notation_data['sentence_id']}:{notation_data['token_id']}"
                                keys.add(key)
                                print(f"[ADD] [VocabNotation] Found matching notation: {key}")
                    except Exception as e:
                        print(f"[WARN] [VocabNotation] Error reading {filename}: {e}")
                        continue
            
            print(f"[OK] [VocabNotation] Retrieved {len(keys)} vocab notations from all users")
            print(f"[SEARCH] [VocabNotation] Keys: {list(keys)}")
            return keys
        except Exception as e:
            print(f"[ERROR] [VocabNotation] JSON query failed: {e}")
            import traceback
            traceback.print_exc()
            return set()
    
    def _get_vocab_notations_json(self, user_id: str, text_id: int) -> Set[str]:
        """JSON 文件模式：获取词汇标注键（保留原方法）"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return set()
            
            with open(file_path, "r", encoding="utf-8") as f:
                vocab_notations = json.load(f)
            
            keys = set()
            for notation_data in vocab_notations:
                if notation_data.get("text_id") == text_id:
                    keys.add(f"{notation_data['text_id']}:{notation_data['sentence_id']}:{notation_data['token_id']}")
            
            print(f"[OK] [VocabNotation] Retrieved {len(keys)} vocab notations from JSON")
            return keys
        except Exception as e:
            print(f"[ERROR] [VocabNotation] JSON query failed: {e}")
            return set()
    
    def delete_vocab_notation(self, user_id: str, notation_key: str) -> bool:
        """删除词汇标注"""
        try:
            if self.use_database:
                return self._delete_vocab_notation_database(user_id, notation_key)
            else:
                return self._delete_vocab_notation_json(user_id, notation_key)
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Failed to delete vocab notation: {e}")
            return False
    
    def _delete_vocab_notation_database(self, user_id: str, notation_key: str) -> bool:
        """数据库模式：删除词汇标注"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # notation_key 格式：text_id:sentence_id:token_id
                parts = notation_key.split(":")
                text_id, sentence_id, token_id = int(parts[0]), int(parts[1]), int(parts[2])
                
                cursor.execute("""
                    DELETE FROM vocab_notations 
                    WHERE user_id = ? AND text_id = ? AND sentence_id = ? AND token_id = ?
                """, (user_id, text_id, sentence_id, token_id))
                
                conn.commit()
                print(f"[OK] [VocabNotation] Vocab notation deleted from database: {notation_key}")
                return True
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Database deletion failed: {e}")
            return False
    
    def _delete_vocab_notation_json(self, user_id: str, notation_key: str) -> bool:
        """JSON 文件模式：删除词汇标注"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return True
            
            with open(file_path, "r", encoding="utf-8") as f:
                vocab_notations = json.load(f)
            
            # 过滤掉指定的标注
            filtered_notations = []
            for notation_data in vocab_notations:
                current_key = f"{notation_data['text_id']}:{notation_data['sentence_id']}:{notation_data['token_id']}"
                if current_key != notation_key:
                    filtered_notations.append(notation_data)
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(filtered_notations, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] [VocabNotation] Vocab notation deleted from JSON: {notation_key}")
            return True
        except Exception as e:
            print(f"[ERROR] [VocabNotation] JSON deletion failed: {e}")
            return False
    
    def get_vocab_notation_details(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> Optional[VocabNotation]:
        """获取词汇标注详情"""
        try:
            if self.use_database:
                return self._get_vocab_notation_details_database(user_id, text_id, sentence_id, token_id)
            else:
                return self._get_vocab_notation_details_json(user_id, text_id, sentence_id, token_id)
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Failed to get vocab notation details: {e}")
            return None
    
    def _get_vocab_notation_details_database(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> Optional[VocabNotation]:
        """数据库模式：获取词汇标注详情"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, text_id, sentence_id, token_id, vocab_id, created_at
                    FROM vocab_notations 
                    WHERE user_id = ? AND text_id = ? AND sentence_id = ? AND token_id = ?
                """, (user_id, text_id, sentence_id, token_id))
                
                row = cursor.fetchone()
                if row:
                    user_id, text_id, sentence_id, token_id, vocab_id, created_at = row
                    return VocabNotation(
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        token_id=token_id,
                        vocab_id=vocab_id,
                        created_at=created_at
                    )
                return None
        except Exception as e:
            print(f"[ERROR] [VocabNotation] Database query failed: {e}")
            return None
    
    def _get_vocab_notation_details_json(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> Optional[VocabNotation]:
        """JSON 文件模式：获取词汇标注详情"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                vocab_notations = json.load(f)
            
            for notation_data in vocab_notations:
                if (notation_data.get("text_id") == text_id and
                    notation_data.get("sentence_id") == sentence_id and
                    notation_data.get("token_id") == token_id):
                    return VocabNotation(**notation_data)
            
            return None
        except Exception as e:
            print(f"[ERROR] [VocabNotation] JSON query failed: {e}")
            return None


# 全局实例（支持配置切换）
_vocab_notation_manager = None

def get_vocab_notation_manager(use_database: bool = True) -> VocabNotationManager:
    """获取 VocabNotationManager 实例"""
    global _vocab_notation_manager
    if _vocab_notation_manager is None:
        _vocab_notation_manager = VocabNotationManager(use_database=use_database)
    return _vocab_notation_manager
