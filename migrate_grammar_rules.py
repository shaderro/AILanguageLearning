#!/usr/bin/env python3
"""
数据库迁移脚本：为 grammar_rules 表添加新字段
"""
import sqlite3
import os

# 数据库路径（支持多个数据库文件）
db_paths = [
    "database_system/data_storage/data/dev.db",  # 开发环境
    "database_system/data_storage/data/language_learning.db",  # 生产环境
    "database_system/data_storage/data/test.db",  # 测试环境
]

# 要添加的字段列表
new_columns = [
    ("display_name", "TEXT"),
    ("canonical_category", "TEXT"),
    ("canonical_subtype", "TEXT"),
    ("canonical_function", "TEXT"),
    ("canonical_key", "TEXT"),
]

# 遍历所有数据库文件
for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"⏭️  跳过不存在的数据库: {db_path}")
        continue
    
    print(f"\n{'='*60}")
    print(f"📂 处理数据库: {db_path}")
    print(f"{'='*60}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grammar_rules'")
        if not cursor.fetchone():
            print(f"⏭️  表 grammar_rules 不存在，跳过")
            conn.close()
            continue
        
        # 检查每个字段是否已存在
        cursor.execute("PRAGMA table_info(grammar_rules)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📋 当前 grammar_rules 表的字段: {', '.join(existing_columns)}")
        
        # 添加新字段
        added_count = 0
        for column_name, column_type in new_columns:
            if column_name in existing_columns:
                print(f"⏭️  字段 {column_name} 已存在，跳过")
            else:
                sql = f"ALTER TABLE grammar_rules ADD COLUMN {column_name} {column_type}"
                print(f"➕ 执行: {sql}")
                cursor.execute(sql)
                print(f"✅ 成功添加字段: {column_name}")
                added_count += 1
        
        # 提交更改
        if added_count > 0:
            conn.commit()
            print(f"\n✅ 迁移完成！添加了 {added_count} 个字段。")
        else:
            print(f"\n✅ 所有字段已存在，无需迁移。")
        
        # 验证结果
        cursor.execute("PRAGMA table_info(grammar_rules)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 更新后的字段列表: {', '.join(final_columns)}")
        
    except sqlite3.Error as e:
        print(f"\n❌ 错误: {e}")
        conn.rollback()
    finally:
        conn.close()

print(f"\n{'='*60}")
print(f"✅ 所有数据库迁移完成！")
print(f"{'='*60}")

