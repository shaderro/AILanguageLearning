#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加段落字段到 sentences 表

迁移内容：
1. 在 sentences 表中添加 paragraph_id 列（Integer, nullable=True）
2. 在 sentences 表中添加 is_new_paragraph 列（Boolean, nullable=True, default=False）
"""

import sys
import os
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_system.database_manager import DatabaseManager
from sqlalchemy import inspect, text


def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception as e:
        print(f"[WARN] 检查列时出错: {e}")
        return False


def migrate_add_paragraph_fields():
    """添加段落字段到 sentences 表"""
    print("\n" + "="*70)
    print("📝 迁移：添加段落字段到 sentences 表")
    print("="*70)
    
    # 使用 development 环境
    db_manager = DatabaseManager('development')
    engine = db_manager.get_engine()
    
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            inspector = inspect(engine)
            if 'sentences' not in inspector.get_table_names():
                print("❌ sentences 表不存在，跳过迁移")
                return False
            
            # 检查 paragraph_id 列是否存在
            has_paragraph_id = check_column_exists(engine, 'sentences', 'paragraph_id')
            has_is_new_paragraph = check_column_exists(engine, 'sentences', 'is_new_paragraph')
            
            if has_paragraph_id and has_is_new_paragraph:
                print("✅ paragraph_id 和 is_new_paragraph 列已存在，无需迁移")
                return True
            
            # 开始事务
            trans = conn.begin()
            try:
                # 添加 paragraph_id 列
                if not has_paragraph_id:
                    print("   ➕ 添加 paragraph_id 列...")
                    conn.execute(text("""
                        ALTER TABLE sentences 
                        ADD COLUMN paragraph_id INTEGER
                    """))
                    print("   ✅ paragraph_id 列添加成功")
                else:
                    print("   ⓘ paragraph_id 列已存在，跳过")
                
                # 添加 is_new_paragraph 列
                if not has_is_new_paragraph:
                    print("   ➕ 添加 is_new_paragraph 列...")
                    conn.execute(text("""
                        ALTER TABLE sentences 
                        ADD COLUMN is_new_paragraph BOOLEAN DEFAULT 0
                    """))
                    print("   ✅ is_new_paragraph 列添加成功")
                else:
                    print("   ⓘ is_new_paragraph 列已存在，跳过")
                
                # 提交事务
                trans.commit()
                print("\n✅ 迁移完成！")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 迁移失败: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"\n❌ 连接数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_add_paragraph_fields()
    sys.exit(0 if success else 1)
