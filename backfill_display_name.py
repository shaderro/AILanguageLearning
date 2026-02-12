#!/usr/bin/env python3
"""
回填脚本：将 rule_name 的值复制到 display_name
确保所有记录的 display_name 都不为 NULL
"""
import sqlite3
import os

# 数据库路径（支持多个数据库文件）
db_paths = [
    "database_system/data_storage/data/dev.db",  # 开发环境
    "database_system/data_storage/data/language_learning.db",  # 生产环境
    "database_system/data_storage/data/test.db",  # 测试环境
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
        
        # 检查 display_name 字段是否存在
        cursor.execute("PRAGMA table_info(grammar_rules)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'display_name' not in columns:
            print(f"❌ 错误：display_name 字段不存在，请先运行迁移脚本")
            conn.close()
            continue
        
        # 统计需要更新的记录数
        cursor.execute("SELECT COUNT(*) FROM grammar_rules WHERE display_name IS NULL OR display_name = ''")
        null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM grammar_rules")
        total_count = cursor.fetchone()[0]
        
        print(f"📊 总记录数: {total_count}")
        print(f"📊 需要更新的记录数（display_name 为 NULL 或空）: {null_count}")
        
        if null_count == 0:
            print(f"✅ 所有记录的 display_name 都已填充，无需更新")
        else:
            # 更新所有 display_name 为 NULL 或空的记录
            cursor.execute("""
                UPDATE grammar_rules 
                SET display_name = rule_name 
                WHERE display_name IS NULL OR display_name = ''
            """)
            
            updated_count = cursor.rowcount
            conn.commit()
            print(f"✅ 成功更新 {updated_count} 条记录")
        
        # 验证结果：检查是否还有 NULL 值
        cursor.execute("SELECT COUNT(*) FROM grammar_rules WHERE display_name IS NULL OR display_name = ''")
        remaining_null = cursor.fetchone()[0]
        
        if remaining_null == 0:
            print(f"✅ 验证通过：所有记录的 display_name 都不为 NULL")
        else:
            print(f"⚠️  警告：仍有 {remaining_null} 条记录的 display_name 为 NULL 或空")
        
        # 显示一些示例数据
        cursor.execute("SELECT rule_id, rule_name, display_name FROM grammar_rules LIMIT 5")
        examples = cursor.fetchall()
        if examples:
            print(f"\n📋 示例数据（前5条）：")
            for rule_id, rule_name, display_name in examples:
                print(f"  - rule_id={rule_id}, rule_name='{rule_name}', display_name='{display_name}'")
        
    except sqlite3.Error as e:
        print(f"\n❌ 错误: {e}")
        conn.rollback()
    finally:
        conn.close()

print(f"\n{'='*60}")
print(f"✅ 所有数据库回填完成！")
print(f"{'='*60}")

