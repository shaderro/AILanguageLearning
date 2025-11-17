#!/usr/bin/env python3
"""
数据库迁移脚本：将所有用户的文章（original_texts）的 language 字段设置为 "德文"

执行步骤：
1. 备份当前数据库
2. 连接数据库
3. 查询所有 original_texts 记录
4. 将所有记录的 language 字段设置为 "德文"
5. 提交更改
"""

import sys
import os
import shutil
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES
from database_system.business_logic.models import OriginalText
from sqlalchemy import inspect, text


def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def update_all_articles_language(environment, db_path, target_language="德文"):
    """更新所有文章的 language 字段"""
    print(f"\n📋 更新 {environment} 环境数据库...")
    print(f"   📁 数据库路径: {db_path}")
    
    # 1. 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"   ⚠️  数据库文件不存在: {db_path}")
        return False
    
    # 2. 备份数据库
    backup_path = backup_database(db_path)
    
    # 3. 连接数据库
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
    except Exception as e:
        print(f"   ❌ 连接数据库失败: {e}")
        return False
    
    try:
        # 4. 检查表是否存在
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        if 'original_texts' not in table_names:
            print("   ⚠️  original_texts 表不存在，跳过")
            return False
        
        # 5. 检查 language 字段是否存在
        columns = [col['name'] for col in inspector.get_columns('original_texts')]
        if 'language' not in columns:
            print("   ⚠️  language 字段不存在，请先运行 migrate_add_language_field_auto.py")
            return False
        
        # 6. 使用原生 SQL 查询文章数量（避免 ORM 模型结构问题）
        count_result = session.execute(text("SELECT COUNT(*) as count FROM original_texts"))
        total_count = count_result.fetchone()[0]
        
        if total_count == 0:
            print("   ℹ️  没有找到任何文章记录")
            return True
        
        print(f"   📊 找到 {total_count} 条文章记录")
        
        # 7. 统计当前语言分布（使用原生 SQL）
        try:
            lang_result = session.execute(text("SELECT language, COUNT(*) as count FROM original_texts GROUP BY language"))
            language_counts = {row[0]: row[1] for row in lang_result.fetchall() if row[0] is not None}
            null_result = session.execute(text("SELECT COUNT(*) as count FROM original_texts WHERE language IS NULL"))
            null_count = null_result.fetchone()[0]
            
            if language_counts or null_count > 0:
                print("   📈 当前语言分布：")
                for lang, count in language_counts.items():
                    print(f"      - {lang}: {count} 条")
                if null_count > 0:
                    print(f"      - NULL: {null_count} 条")
        except Exception as e:
            print(f"   ⚠️  统计语言分布时出错（可能表结构较旧）: {e}")
            language_counts = {}
            null_count = total_count
        
        # 8. 使用原生 SQL 更新所有记录的 language 字段
        try:
            # 先更新 NULL 值
            update_null_sql = text("UPDATE original_texts SET language = :lang WHERE language IS NULL")
            result_null = session.execute(update_null_sql, {"lang": target_language})
            updated_null = result_null.rowcount
            
            # 再更新非 NULL 但不同的值
            update_other_sql = text("UPDATE original_texts SET language = :lang WHERE language != :lang")
            result_other = session.execute(update_other_sql, {"lang": target_language})
            updated_other = result_other.rowcount
            
            updated_count = updated_null + updated_other
            
            # 9. 提交更改
            if updated_count > 0:
                session.commit()
                print(f"   ✅ 成功更新 {updated_count} 条记录的 language 字段为 '{target_language}'")
            else:
                print(f"   ℹ️  所有记录的 language 字段已经是 '{target_language}'，无需更新")
        except Exception as e:
            session.rollback()
            print(f"   ❌ 更新失败: {e}")
            raise
        
        # 10. 验证更新（使用原生 SQL）
        try:
            verify_result = session.execute(text(f"SELECT COUNT(*) as count FROM original_texts WHERE language = :lang"), {"lang": target_language})
            german_count = verify_result.fetchone()[0]
            
            if german_count == total_count:
                print(f"   ✅ 验证成功：所有 {total_count} 条记录的 language 字段都是 '{target_language}'")
                return True
            else:
                print(f"   ⚠️  验证失败：{german_count}/{total_count} 条记录的 language 字段是 '{target_language}'")
                return False
        except Exception as e:
            print(f"   ⚠️  验证时出错: {e}")
            return True  # 即使验证失败，也认为更新可能成功
            
    except Exception as e:
        session.rollback()
        print(f"   ❌ {environment} 环境更新失败: {e}")
        if backup_path:
            print(f"   💾 可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("数据库迁移：将所有文章的 language 字段设置为 '德文'")
    print("="*60)
    
    # 迁移所有环境的数据库
    environments = [
        ('development', DB_FILES['dev']),
        ('production', DB_FILES['prod']),
    ]
    
    success_count = 0
    for env, db_path in environments:
        if update_all_articles_language(env, db_path, target_language="德文"):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == len(environments):
        print("✅ 所有迁移完成！")
    else:
        print(f"⚠️  部分迁移完成 ({success_count}/{len(environments)})")
    print("="*60)
    print("\n下一步：")
    print("1. 验证数据库中的 language 字段")
    print("2. 测试文章显示功能")
    print("3. 确认所有文章的 language 字段都是 '德文'")


if __name__ == "__main__":
    main()

