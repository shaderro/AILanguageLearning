#!/usr/bin/env python3
"""
Grammar Notation 数据管理器
支持 JSON 文件和 SQLite 数据库两种存储方式
用于管理语法知识点标注
"""

import json
import os
import sqlite3
from typing import Set, List, Optional
from dataclasses import asdict
from datetime import datetime

# 从 data_classes_new 导入 GrammarNotation
import sys
import os
sys.path.append(os.path.dirname(__file__))
from data_classes_new import GrammarNotation


class GrammarNotationManager:
    """Grammar Notation 数据管理器"""
    
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
                json_dir = os.path.join(current_dir, "data", "current", "grammar_notations")
            
            self.json_dir = json_dir
            os.makedirs(self.json_dir, exist_ok=True)
            # Debug logging removed for performance
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS grammar_notations (
                        user_id TEXT NOT NULL,
                        text_id INTEGER NOT NULL,
                        sentence_id INTEGER NOT NULL,
                        grammar_id INTEGER,
                        marked_token_ids TEXT NOT NULL,
                        created_at TEXT,
                        PRIMARY KEY (user_id, text_id, sentence_id)
                    )
                """)
                conn.commit()
                # Debug logging removed for performance
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Database initialization failed: {e}")
            raise
    
    def _get_json_file_path(self, user_id: str) -> str:
        """获取用户的 JSON 文件路径"""
        return os.path.join(self.json_dir, f"{user_id}.json")
    
    def create_grammar_notation(self, user_id: str, text_id: int, sentence_id: int, 
                               grammar_id: Optional[int] = None, marked_token_ids: List[int] = None) -> bool:
        """
        创建语法标注
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            grammar_id: 语法规则ID（可选）
            marked_token_ids: 句中重点语法成分的token id列表
        """
        if marked_token_ids is None:
            marked_token_ids = []
            
        print(f"[INFO] [GrammarNotation] create_grammar_notation called:")
        print(f"  - user_id: {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - grammar_id: {grammar_id}")
        print(f"  - marked_token_ids: {marked_token_ids}")
        
        try:
            grammar_notation = GrammarNotation(
                user_id=user_id,
                text_id=text_id,
                sentence_id=sentence_id,
                grammar_id=grammar_id,
                marked_token_ids=marked_token_ids,
                created_at=datetime.now().isoformat()
            )
            
            if self.use_database:
                return self._create_grammar_notation_database(grammar_notation)
            else:
                return self._create_grammar_notation_json(grammar_notation)
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Failed to create grammar notation: {e}")
            return False
    
    def _create_grammar_notation_database(self, grammar_notation: GrammarNotation) -> bool:
        """数据库模式：创建语法标注（使用主 ORM）"""
        try:
            # 使用主数据库的 ORM Session
            from database_system.database_manager import DatabaseManager
            db_manager = DatabaseManager('development')
            session = db_manager.get_session()
            
            try:
                from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
                crud = GrammarNotationCRUD(session)
                
                # 🔧 检查是否已存在（包含 grammar_id，支持同一句子有多个语法知识点）
                if crud.exists(grammar_notation.user_id, grammar_notation.text_id, 
                              grammar_notation.sentence_id, grammar_notation.grammar_id):
                    print(f"[INFO] [GrammarNotation] Already exists: {grammar_notation.text_id}:{grammar_notation.sentence_id}, grammar_id={grammar_notation.grammar_id}")
                    session.close()
                    return True
                
                # 创建新标注
                crud.create(
                    user_id=grammar_notation.user_id,
                    text_id=grammar_notation.text_id,
                    sentence_id=grammar_notation.sentence_id,
                    grammar_id=grammar_notation.grammar_id,
                    marked_token_ids=grammar_notation.marked_token_ids
                )
                print(f"[OK] [GrammarNotation] Created grammar notation in ORM: {grammar_notation.text_id}:{grammar_notation.sentence_id}")
                session.close()
                return True
            except Exception as e:
                session.rollback()
                session.close()
                raise e
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] ORM creation failed: {e}")
            return False
    
    def _create_grammar_notation_json(self, grammar_notation: GrammarNotation) -> bool:
        """JSON 文件模式：创建语法标注"""
        try:
            file_path = self._get_json_file_path(grammar_notation.user_id)
            print(f"[INFO] [GrammarNotation] JSON file path: {file_path}")
            
            # 读取现有数据
            grammar_notations = []
            if os.path.exists(file_path):
                print(f"[READ] [GrammarNotation] Reading existing file: {file_path}")
                with open(file_path, "r", encoding="utf-8") as f:
                    grammar_notations = json.load(f)
                print(f"[DATA] [GrammarNotation] Existing notations count: {len(grammar_notations)}")
            else:
                print(f"[WRITE] [GrammarNotation] Creating new file: {file_path}")
            
            # 检查是否已存在
            notation_key = f"{grammar_notation.text_id}:{grammar_notation.sentence_id}"
            existing = False
            for notation_data in grammar_notations:
                if (notation_data.get("text_id") == grammar_notation.text_id and
                    notation_data.get("sentence_id") == grammar_notation.sentence_id):
                    existing = True
                    print(f"[WARN] [GrammarNotation] Already exists: {notation_key}")
                    break
            
            if not existing:
                # 添加新标注
                grammar_notations.append(asdict(grammar_notation))
                print(f"[ADD] [GrammarNotation] Added new notation: {notation_key}")
            else:
                # 更新现有标注
                for notation_data in grammar_notations:
                    if (notation_data.get("text_id") == grammar_notation.text_id and
                        notation_data.get("sentence_id") == grammar_notation.sentence_id):
                        notation_data.update(asdict(grammar_notation))
                        print(f"[REFRESH] [GrammarNotation] Updated existing notation: {notation_key}")
                        break
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(grammar_notations, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] [GrammarNotation] Created grammar notation in JSON: {notation_key}")
            return True
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] JSON creation failed: {e}")
            return False
    
    def is_grammar_notation_exists(self, user_id: str, text_id: int, sentence_id: int) -> bool:
        """检查语法标注是否存在"""
        try:
            if self.use_database:
                return self._check_grammar_notation_database(user_id, text_id, sentence_id)
            else:
                return self._check_grammar_notation_json(user_id, text_id, sentence_id)
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Failed to check grammar notation: {e}")
            return False
    
    def _check_grammar_notation_database(self, user_id: str, text_id: int, sentence_id: int) -> bool:
        """数据库模式：检查语法标注是否存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM grammar_notations 
                    WHERE user_id = ? AND text_id = ? AND sentence_id = ?
                """, (user_id, text_id, sentence_id))
                
                count = cursor.fetchone()[0]
                exists = count > 0
                print(f"[SEARCH] [GrammarNotation] Database check result: {exists}")
                return exists
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Database check failed: {e}")
            return False
    
    def _check_grammar_notation_json(self, user_id: str, text_id: int, sentence_id: int) -> bool:
        """JSON 文件模式：检查语法标注是否存在"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, "r", encoding="utf-8") as f:
                grammar_notations = json.load(f)
            
            for notation_data in grammar_notations:
                if (notation_data.get("text_id") == text_id and
                    notation_data.get("sentence_id") == sentence_id):
                    print(f"[SEARCH] [GrammarNotation] JSON check result: True")
                    return True
            
            print(f"[SEARCH] [GrammarNotation] JSON check result: False")
            return False
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] JSON check failed: {e}")
            return False
    
    def get_grammar_notations_for_article(self, text_id: int, user_id: Optional[str] = None) -> Set[str]:
        """
        获取指定文章的语法标注键集合
        
        Args:
            text_id: 文章ID
            user_id: 用户ID（可选，如果为None则获取所有用户的数据）
        """
        print(f"[INFO] [GrammarNotation] get_grammar_notations_for_article called for text_id: {text_id}, user_id: {user_id}")
        
        try:
            if self.use_database:
                if user_id:
                    return self._get_grammar_notations_database(user_id, text_id)
                else:
                    return self._get_grammar_notations_database_all_users(text_id)
            else:
                if user_id:
                    return self._get_grammar_notations_json(user_id, text_id)
                else:
                    return self._get_grammar_notations_json_all_users(text_id)
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Failed to get grammar notations: {e}")
            return set()
    
    def _get_grammar_notations_database(self, user_id: str, text_id: int) -> Set[str]:
        """数据库模式：获取语法标注键（使用主 ORM）"""
        try:
            from database_system.database_manager import DatabaseManager
            from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
            
            db_manager = DatabaseManager('development')
            session = db_manager.get_session()
            
            try:
                crud = GrammarNotationCRUD(session)
                notations = crud.get_by_text(text_id, user_id)
                keys = {f"{n.text_id}:{n.sentence_id}" for n in notations}
                print(f"[OK] [GrammarNotation] Retrieved {len(keys)} grammar notations from ORM")
                session.close()
                return keys
            except Exception as e:
                session.close()
                raise e
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] ORM query failed: {e}")
            return set()
    
    def _get_grammar_notations_database_all_users(self, text_id: int) -> Set[str]:
        """数据库模式：获取所有用户在指定文章下的语法标注键（使用主 ORM）"""
        try:
            from database_system.database_manager import DatabaseManager
            from database_system.business_logic.crud.notation_crud import GrammarNotationCRUD
            
            db_manager = DatabaseManager('development')
            session = db_manager.get_session()
            
            try:
                crud = GrammarNotationCRUD(session)
                notations = crud.get_by_text(text_id, user_id=None)
                keys = {f"{n.text_id}:{n.sentence_id}" for n in notations}
                print(f"[OK] [GrammarNotation] Retrieved {len(keys)} grammar notations from ORM (all users)")
                session.close()
                return keys
            except Exception as e:
                session.close()
                raise e
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] ORM query failed: {e}")
            return set()
    
    def _get_grammar_notations_json_all_users(self, text_id: int) -> Set[str]:
        """JSON 文件模式：获取所有用户在指定文章下的语法标注键"""
        print(f"[INFO] [GrammarNotation] _get_grammar_notations_json_all_users called for text_id: {text_id}")
        
        try:
            keys = set()
            
            # 扫描所有用户的 JSON 文件
            if not os.path.exists(self.json_dir):
                print(f"[WARN] [GrammarNotation] JSON directory does not exist: {self.json_dir}")
                return keys
            
            print(f"[DIR] [GrammarNotation] Scanning directory: {self.json_dir}")
            for filename in os.listdir(self.json_dir):
                if filename.endswith('.json'):
                    user_file_path = os.path.join(self.json_dir, filename)
                    print(f"[READ] [GrammarNotation] Reading user file: {filename}")
                    
                    try:
                        with open(user_file_path, "r", encoding="utf-8") as f:
                            user_notations = json.load(f)
                        
                        print(f"[DATA] [GrammarNotation] User {filename} has {len(user_notations)} notations")
                        
                        for notation_data in user_notations:
                            if notation_data.get("text_id") == text_id:
                                key = f"{notation_data['text_id']}:{notation_data['sentence_id']}"
                                keys.add(key)
                                print(f"[ADD] [GrammarNotation] Found matching notation: {key}")
                    except Exception as e:
                        print(f"[WARN] [GrammarNotation] Error reading {filename}: {e}")
                        continue
            
            print(f"[OK] [GrammarNotation] Retrieved {len(keys)} grammar notations from all users")
            print(f"[SEARCH] [GrammarNotation] Keys: {list(keys)}")
            return keys
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] JSON query failed: {e}")
            import traceback
            traceback.print_exc()
            return set()
    
    def _get_grammar_notations_json(self, user_id: str, text_id: int) -> Set[str]:
        """JSON 文件模式：获取语法标注键（保留原方法）"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return set()
            
            with open(file_path, "r", encoding="utf-8") as f:
                grammar_notations = json.load(f)
            
            keys = set()
            for notation_data in grammar_notations:
                if notation_data.get("text_id") == text_id:
                    keys.add(f"{notation_data['text_id']}:{notation_data['sentence_id']}")
            
            print(f"[OK] [GrammarNotation] Retrieved {len(keys)} grammar notations from JSON")
            return keys
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] JSON query failed: {e}")
            return set()
    
    def delete_grammar_notation(self, user_id: str, notation_key: str) -> bool:
        """删除语法标注"""
        try:
            if self.use_database:
                return self._delete_grammar_notation_database(user_id, notation_key)
            else:
                return self._delete_grammar_notation_json(user_id, notation_key)
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Failed to delete grammar notation: {e}")
            return False
    
    def _delete_grammar_notation_database(self, user_id: str, notation_key: str) -> bool:
        """数据库模式：删除语法标注"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # notation_key 格式：text_id:sentence_id
                parts = notation_key.split(":")
                text_id, sentence_id = int(parts[0]), int(parts[1])
                
                cursor.execute("""
                    DELETE FROM grammar_notations 
                    WHERE user_id = ? AND text_id = ? AND sentence_id = ?
                """, (user_id, text_id, sentence_id))
                
                conn.commit()
                print(f"[OK] [GrammarNotation] Grammar notation deleted from database: {notation_key}")
                return True
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Database deletion failed: {e}")
            return False
    
    def _delete_grammar_notation_json(self, user_id: str, notation_key: str) -> bool:
        """JSON 文件模式：删除语法标注"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return True
            
            with open(file_path, "r", encoding="utf-8") as f:
                grammar_notations = json.load(f)
            
            # 过滤掉指定的标注
            filtered_notations = []
            for notation_data in grammar_notations:
                current_key = f"{notation_data['text_id']}:{notation_data['sentence_id']}"
                if current_key != notation_key:
                    filtered_notations.append(notation_data)
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(filtered_notations, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] [GrammarNotation] Grammar notation deleted from JSON: {notation_key}")
            return True
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] JSON deletion failed: {e}")
            return False
    
    def get_grammar_notation_details(self, user_id: str, text_id: int, sentence_id: int) -> Optional[GrammarNotation]:
        """获取语法标注详情"""
        try:
            if self.use_database:
                return self._get_grammar_notation_details_database(user_id, text_id, sentence_id)
            else:
                return self._get_grammar_notation_details_json(user_id, text_id, sentence_id)
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Failed to get grammar notation details: {e}")
            return None
    
    def _get_grammar_notation_details_database(self, user_id: str, text_id: int, sentence_id: int) -> Optional[GrammarNotation]:
        """数据库模式：获取语法标注详情"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, text_id, sentence_id, grammar_id, marked_token_ids, created_at
                    FROM grammar_notations 
                    WHERE user_id = ? AND text_id = ? AND sentence_id = ?
                """, (user_id, text_id, sentence_id))
                
                row = cursor.fetchone()
                if row:
                    user_id, text_id, sentence_id, grammar_id, marked_token_ids_json, created_at = row
                    # 将 JSON 字符串转换回列表
                    marked_token_ids = json.loads(marked_token_ids_json)
                    return GrammarNotation(
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        grammar_id=grammar_id,
                        marked_token_ids=marked_token_ids,
                        created_at=created_at
                    )
                return None
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] Database query failed: {e}")
            return None
    
    def _get_grammar_notation_details_json(self, user_id: str, text_id: int, sentence_id: int) -> Optional[GrammarNotation]:
        """JSON 文件模式：获取语法标注详情"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                grammar_notations = json.load(f)
            
            for notation_data in grammar_notations:
                if (notation_data.get("text_id") == text_id and
                    notation_data.get("sentence_id") == sentence_id):
                    return GrammarNotation(**notation_data)
            
            return None
        except Exception as e:
            print(f"[ERROR] [GrammarNotation] JSON query failed: {e}")
            return None


# 全局实例（支持配置切换）
_grammar_notation_manager = None

def get_grammar_notation_manager(use_database: bool = True) -> GrammarNotationManager:
    """获取 GrammarNotationManager 实例"""
    global _grammar_notation_manager
    if _grammar_notation_manager is None:
        _grammar_notation_manager = GrammarNotationManager(use_database=use_database)
    return _grammar_notation_manager
