#!/usr/bin/env python3
"""
Asked Tokens 数据管理器
支持 JSON 文件和 SQLite 数据库两种存储方式
使用 text_id + sentence_id + sentence_token_id 作为唯一标识
"""

import json
import os
import sqlite3
from typing import Set, List, Optional
from dataclasses import asdict

# 从 data_classes_new 导入 AskedToken
from .data_classes_new import AskedToken


class AskedTokensManager:
    """Asked Tokens 数据管理器"""
    
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
                json_dir = os.path.join(current_dir, "data", "current", "asked_tokens")
            
            self.json_dir = json_dir
            os.makedirs(self.json_dir, exist_ok=True)
            print(f"[INFO] [AskedTokens] JSON 目录: {self.json_dir}")
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS asked_tokens (
                        user_id TEXT NOT NULL,
                        text_id INTEGER NOT NULL,
                        sentence_id INTEGER NOT NULL,
                        sentence_token_id INTEGER NOT NULL,
                        PRIMARY KEY (user_id, text_id, sentence_id, sentence_token_id)
                    )
                """)
                conn.commit()
                print("[OK] [AskedTokens] Database table initialized")
        except Exception as e:
            print(f"[ERROR] [AskedTokens] Database initialization failed: {e}")
            raise
    
    def _get_json_file_path(self, user_id: str) -> str:
        """获取用户的 JSON 文件路径"""
        return os.path.join(self.json_dir, f"{user_id}.json")
    
    def mark_token_asked(self, user_id: str, text_id: int, sentence_id: int, 
                        sentence_token_id: int = None, vocab_id: int = None, grammar_id: int = None, type: str = "token") -> bool:
        """
        标记 token 或 sentence 为已提问
        
        Args:
            user_id: 用户ID
            text_id: 文章ID
            sentence_id: 句子ID
            sentence_token_id: Token ID（可选）
            vocab_id: 词汇ID（可选）
            grammar_id: 语法ID（可选）
            type: 标记类型，'token' 或 'sentence'，默认 'token'
        
        向后兼容：如果 type 未指定但 sentence_token_id 不为空，默认为 'token'
        """
        # 向后兼容逻辑
        if type is None and sentence_token_id is not None:
            type = "token"
        
        # Debug logging removed for performance
        
        try:
            asked_token = AskedToken(
                user_id=user_id,
                text_id=text_id,
                sentence_id=sentence_id,
                sentence_token_id=sentence_token_id,
                type=type,
                vocab_id=vocab_id,
                grammar_id=grammar_id
            )
            
            if self.use_database:
                return self._mark_asked_database(asked_token)
            else:
                return self._mark_asked_json(asked_token)
        except Exception as e:
            print(f"❌ [AskedTokens] Failed to mark token as asked: {e}")
            return False
    
    def _mark_asked_database(self, asked_token: AskedToken) -> bool:
        """数据库模式：标记已提问"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO asked_tokens 
                    (user_id, text_id, sentence_id, sentence_token_id, type)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    asked_token.user_id,
                    asked_token.text_id,
                    asked_token.sentence_id,
                    asked_token.sentence_token_id,
                    asked_token.type
                ))
                conn.commit()
                print(f"✅ [AskedTokens] Marked as asked in database: {asked_token.text_id}:{asked_token.sentence_id}:{asked_token.sentence_token_id} (type={asked_token.type})")
                return True
        except Exception as e:
            print(f"❌ [AskedTokens] Database mark failed: {e}")
            return False
    
    def _mark_asked_json(self, asked_token: AskedToken) -> bool:
        """JSON 文件模式：标记已提问"""
        try:
            file_path = self._get_json_file_path(asked_token.user_id)
            print(f"🔧 [AskedTokens] JSON file path: {file_path}")
            
            # 读取现有数据
            asked_tokens = []
            if os.path.exists(file_path):
                print(f"📖 [AskedTokens] Reading existing file: {file_path}")
                with open(file_path, "r", encoding="utf-8") as f:
                    asked_tokens = json.load(f)
                print(f"📊 [AskedTokens] Existing tokens count: {len(asked_tokens)}")
            else:
                print(f"📝 [AskedTokens] Creating new file: {file_path}")
            
            # 检查是否已存在
            token_key = f"{asked_token.text_id}:{asked_token.sentence_id}:{asked_token.sentence_token_id}:{asked_token.type}"
            existing = False
            for token_data in asked_tokens:
                # 比较时需要考虑 type 字段
                if (token_data.get("text_id") == asked_token.text_id and
                    token_data.get("sentence_id") == asked_token.sentence_id and
                    token_data.get("sentence_token_id") == asked_token.sentence_token_id and
                    token_data.get("type", "token") == asked_token.type):  # 向后兼容：默认为 token
                    existing = True
                    print(f"⚠️ [AskedTokens] Already exists: {token_key}")
                    break
            
            if not existing:
                print(f"➕ [AskedTokens] Adding new entry: {token_key}")
                asked_tokens.append(asdict(asked_token))
                
                # 写回文件
                print(f"💾 [AskedTokens] Writing to file: {file_path}")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(asked_tokens, f, ensure_ascii=False, indent=2)
                print(f"✅ [AskedTokens] File written successfully")
            else:
                print(f"ℹ️ [AskedTokens] Token already exists, skipping")
            
            print(f"✅ [AskedTokens] Token marked as asked in JSON: {token_key}")
            return True
        except Exception as e:
            print(f"❌ [AskedTokens] JSON mark failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_asked_tokens_for_article(self, user_id: str, text_id: int) -> Set[str]:
        """获取用户在指定文章下已提问的 token 键集合"""
        # Debug logging removed for performance
        
        try:
            if self.use_database:
                return self._get_asked_tokens_database(user_id, text_id)
            else:
                return self._get_asked_tokens_json_all_users(text_id)  # 修改：获取所有用户的数据
        except Exception as e:
            print(f"❌ [AskedTokens] Failed to get asked tokens: {e}")
            return set()
    
    def _get_asked_tokens_database(self, user_id: str, text_id: int) -> Set[str]:
        """数据库模式：获取已提问的 token 键"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT text_id, sentence_id, sentence_token_id
                    FROM asked_tokens 
                    WHERE text_id = ? AND type = 'token' AND sentence_token_id IS NOT NULL
                """, (text_id,))  # 只获取token类型的记录
                
                keys = set()
                for row in cursor.fetchall():
                    t_id, s_id, st_id = row
                    keys.add(f"{t_id}:{s_id}:{st_id}")
                
                # Debug logging removed for performance
                return keys
        except Exception as e:
            print(f"❌ [AskedTokens] Database query failed: {e}")
            return set()
    
    def _get_asked_tokens_json_all_users(self, text_id: int) -> Set[str]:
        """JSON 文件模式：获取所有用户在指定文章下已提问的 token 键"""
        # Debug logging removed for performance
        
        try:
            keys = set()
            
            # 扫描所有用户的 JSON 文件
            if not os.path.exists(self.json_dir):
                # Debug logging removed for performance
                return keys
            
            # Debug logging removed for performance
            for filename in os.listdir(self.json_dir):
                if filename.endswith('.json'):
                    user_file_path = os.path.join(self.json_dir, filename)
                    # Debug logging removed for performance
                    
                    try:
                        with open(user_file_path, "r", encoding="utf-8") as f:
                            user_tokens = json.load(f)
                        
                        # Debug logging removed for performance
                        
                        for token_data in user_tokens:
                            if token_data.get("text_id") == text_id:
                                # 只处理token类型的记录，跳过sentence类型
                                if token_data.get("type") == "token" and token_data.get("sentence_token_id") is not None:
                                    key = f"{token_data['text_id']}:{token_data['sentence_id']}:{token_data['sentence_token_id']}"
                                    keys.add(key)
                                    # Debug logging removed for performance
                    except Exception as e:
                        # Debug logging removed for performance
                        continue
            
            # Debug logging removed for performance
            return keys
        except Exception as e:
            print(f"❌ [AskedTokens] JSON query failed: {e}")
            import traceback
            traceback.print_exc()
            return set()
    
    def _get_asked_tokens_json(self, user_id: str, text_id: int) -> Set[str]:
        """JSON 文件模式：获取已提问的 token 键（保留原方法）"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return set()
            
            with open(file_path, "r", encoding="utf-8") as f:
                asked_tokens = json.load(f)
            
            keys = set()
            for token_data in asked_tokens:
                if token_data.get("text_id") == text_id:
                    keys.add(f"{token_data['text_id']}:{token_data['sentence_id']}:{token_data['sentence_token_id']}")
            
            # Debug logging removed for performance
            return keys
        except Exception as e:
            print(f"❌ [AskedTokens] JSON query failed: {e}")
            return set()
    
    def unmark_token_asked(self, user_id: str, token_key: str) -> bool:
        """取消标记 token 为已提问"""
        try:
            if self.use_database:
                return self._unmark_asked_database(user_id, token_key)
            else:
                return self._unmark_asked_json(user_id, token_key)
        except Exception as e:
            print(f"❌ [AskedTokens] Failed to unmark token: {e}")
            return False
    
    def _unmark_asked_database(self, user_id: str, token_key: str) -> bool:
        """数据库模式：取消标记"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # token_key 格式：text_id:sentence_id:sentence_token_id
                parts = token_key.split(":")
                text_id, sentence_id, sentence_token_id = int(parts[0]), int(parts[1]), int(parts[2])
                
                cursor.execute("""
                    DELETE FROM asked_tokens 
                    WHERE text_id = ? AND sentence_id = ? AND sentence_token_id = ?
                """, (text_id, sentence_id, sentence_token_id))  # 修改：移除 user_id 过滤
                
                conn.commit()
                print(f"✅ [AskedTokens] Token unmarked in database: {token_key}")
                return True
        except Exception as e:
            print(f"❌ [AskedTokens] Database unmark failed: {e}")
            return False
    
    def _unmark_asked_json(self, user_id: str, token_key: str) -> bool:
        """JSON 文件模式：取消标记"""
        try:
            file_path = self._get_json_file_path(user_id)
            if not os.path.exists(file_path):
                return True
            
            with open(file_path, "r", encoding="utf-8") as f:
                asked_tokens = json.load(f)
            
            # 过滤掉指定的 token
            filtered_tokens = []
            for token_data in asked_tokens:
                current_key = f"{token_data['text_id']}:{token_data['sentence_id']}:{token_data['sentence_token_id']}"
                if current_key != token_key:
                    filtered_tokens.append(token_data)
            
            # 写回文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(filtered_tokens, f, ensure_ascii=False, indent=2)
            
            print(f"✅ [AskedTokens] Token unmarked in JSON: {token_key}")
            return True
        except Exception as e:
            print(f"❌ [AskedTokens] JSON unmark failed: {e}")
            return False


    # ===== 向后兼容方法 =====
    
    def mark_as_vocab_notation(self, user_id: str, text_id: int, sentence_id: int, 
                              token_id: int, vocab_id: Optional[int] = None) -> bool:
        """
        向后兼容方法：标记为词汇标注
        这个方法是为了与新系统兼容而添加的
        """
        print(f"[INFO] [AskedTokens] mark_as_vocab_notation called (legacy compatibility)")
        return self.mark_token_asked(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=token_id,
            type="token",
            vocab_id=vocab_id,
            grammar_id=None
        )
    
    def mark_as_grammar_notation(self, user_id: str, text_id: int, sentence_id: int,
                                grammar_id: Optional[int] = None, marked_token_ids: List[int] = None) -> bool:
        """
        向后兼容方法：标记为语法标注
        这个方法是为了与新系统兼容而添加的
        """
        print(f"[INFO] [AskedTokens] mark_as_grammar_notation called (legacy compatibility)")
        return self.mark_token_asked(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=None,
            type="sentence",
            vocab_id=None,
            grammar_id=grammar_id
        )
    
    def is_vocab_notation_exists(self, user_id: str, text_id: int, sentence_id: int, token_id: int) -> bool:
        """
        向后兼容方法：检查词汇标注是否存在
        """
        print(f"[INFO] [AskedTokens] is_vocab_notation_exists called (legacy compatibility)")
        asked_tokens = self.get_asked_tokens_for_article(text_id, user_id)
        key = f"{text_id}:{sentence_id}:{token_id}"
        return key in asked_tokens
    
    def is_grammar_notation_exists(self, user_id: str, text_id: int, sentence_id: int) -> bool:
        """
        向后兼容方法：检查语法标注是否存在
        """
        print(f"[INFO] [AskedTokens] is_grammar_notation_exists called (legacy compatibility)")
        # 检查是否有 sentence 类型的标注
        try:
            if self.use_database:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM asked_tokens 
                        WHERE user_id = ? AND text_id = ? AND sentence_id = ? AND type = 'sentence'
                    """, (user_id, text_id, sentence_id))
                    count = cursor.fetchone()[0]
                    return count > 0
            else:
                file_path = self._get_json_file_path(user_id)
                if not os.path.exists(file_path):
                    return False
                
                with open(file_path, "r", encoding="utf-8") as f:
                    asked_tokens = json.load(f)
                
                for token_data in asked_tokens:
                    if (token_data.get("text_id") == text_id and
                        token_data.get("sentence_id") == sentence_id and
                        token_data.get("type") == "sentence"):
                        return True
                return False
        except Exception as e:
            print(f"[ERROR] [AskedTokens] Failed to check grammar notation: {e}")
            return False


# 全局实例（支持配置切换）
_asked_tokens_manager = None

def get_asked_tokens_manager(use_database: bool = False) -> AskedTokensManager:
    """
    获取 AskedTokensManager 实例
    
    🔧 注意：asked_tokens 现在是 legacy 系统，默认只使用 JSON 文件，不使用数据库
    即使传入 use_database=True，也会强制使用 JSON 模式
    """
    global _asked_tokens_manager
    # 🔧 强制使用 JSON 模式，因为 asked_tokens 是 legacy 系统
    use_database = False
    if _asked_tokens_manager is None:
        _asked_tokens_manager = AskedTokensManager(use_database=use_database)
    return _asked_tokens_manager
