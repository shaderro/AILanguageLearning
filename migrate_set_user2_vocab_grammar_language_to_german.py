#!/usr/bin/env python3
"""
数据库迁移脚本：将user 2的所有vocab和grammar的language字段设置为"德文"

执行步骤：
1. 备份当前数据库
2. 连接数据库
3. 查找user_id=2的所有vocab和grammar
4. 将它们的language字段设置为"德文"
5. 验证更新结果
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
from sqlalchemy import text


def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def update_user2_vocab_grammar_language(environment, db_path, target_language="德文", user_id=2):
    """为user 2的所有vocab和grammar设置language字段"""
    print(f"\n📋 更新 {environment} 环境数据库...")
    print(f"   📁 数据库路径: {db_path}")
    print(f"   👤 用户ID: {user_id}")
    print(f"   🌐 目标语言: {target_language}")
    
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
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        # 检查vocab_expressions表
        vocab_has_user_id = False
        vocab_count = 0
        if 'vocab_expressions' not in table_names:
            print(f"   ⚠️  vocab_expressions 表不存在，跳过")
        else:
            # 检查是否有user_id列
            vocab_columns = [col['name'] for col in inspector.get_columns('vocab_expressions')]
            vocab_has_user_id = 'user_id' in vocab_columns
            
            if vocab_has_user_id:
                # 5. 统计user 2的vocab数量（有user_id列）
                vocab_count_result = session.execute(text("""
                    SELECT COUNT(*) FROM vocab_expressions 
                    WHERE user_id = :user_id
                """), {"user_id": user_id}).fetchone()
                vocab_count = vocab_count_result[0] if vocab_count_result else 0
                print(f"   📊 找到 {vocab_count} 个user {user_id}的vocab记录")
                
                # 6. 更新vocab的language字段
                if vocab_count > 0:
                    session.execute(text("""
                        UPDATE vocab_expressions 
                        SET language = :language 
                        WHERE user_id = :user_id
                    """), {"language": target_language, "user_id": user_id})
                    session.commit()
                    print(f"   ✅ 成功更新 {vocab_count} 个vocab的language字段为 '{target_language}'")
                else:
                    print(f"   ℹ️  user {user_id} 没有vocab记录")
            else:
                # 如果没有user_id列，更新所有记录（可能是旧schema）
                vocab_count_result = session.execute(text("""
                    SELECT COUNT(*) FROM vocab_expressions
                """)).fetchone()
                vocab_count = vocab_count_result[0] if vocab_count_result else 0
                print(f"   ⚠️  vocab_expressions 表没有user_id列，将更新所有 {vocab_count} 条记录")
                
                if vocab_count > 0:
                    session.execute(text("""
                        UPDATE vocab_expressions 
                        SET language = :language
                    """), {"language": target_language})
                    session.commit()
                    print(f"   ✅ 成功更新 {vocab_count} 个vocab的language字段为 '{target_language}'")
        
        # 检查grammar_rules表
        grammar_has_user_id = False
        grammar_count = 0
        if 'grammar_rules' not in table_names:
            print(f"   ⚠️  grammar_rules 表不存在，跳过")
        else:
            # 检查是否有user_id列
            grammar_columns = [col['name'] for col in inspector.get_columns('grammar_rules')]
            grammar_has_user_id = 'user_id' in grammar_columns
            
            if grammar_has_user_id:
                # 7. 统计user 2的grammar数量（有user_id列）
                grammar_count_result = session.execute(text("""
                    SELECT COUNT(*) FROM grammar_rules 
                    WHERE user_id = :user_id
                """), {"user_id": user_id}).fetchone()
                grammar_count = grammar_count_result[0] if grammar_count_result else 0
                print(f"   📊 找到 {grammar_count} 个user {user_id}的grammar记录")
                
                # 8. 更新grammar的language字段
                if grammar_count > 0:
                    session.execute(text("""
                        UPDATE grammar_rules 
                        SET language = :language 
                        WHERE user_id = :user_id
                    """), {"language": target_language, "user_id": user_id})
                    session.commit()
                    print(f"   ✅ 成功更新 {grammar_count} 个grammar的language字段为 '{target_language}'")
                else:
                    print(f"   ℹ️  user {user_id} 没有grammar记录")
            else:
                # 如果没有user_id列，更新所有记录（可能是旧schema）
                grammar_count_result = session.execute(text("""
                    SELECT COUNT(*) FROM grammar_rules
                """)).fetchone()
                grammar_count = grammar_count_result[0] if grammar_count_result else 0
                print(f"   ⚠️  grammar_rules 表没有user_id列，将更新所有 {grammar_count} 条记录")
                
                if grammar_count > 0:
                    session.execute(text("""
                        UPDATE grammar_rules 
                        SET language = :language
                    """), {"language": target_language})
                    session.commit()
                    print(f"   ✅ 成功更新 {grammar_count} 个grammar的language字段为 '{target_language}'")
        
        # 9. 验证更新结果
        print(f"\n   🔍 验证更新结果...")
        if 'vocab_expressions' in table_names:
            if vocab_has_user_id:
                vocab_verified = session.execute(text("""
                    SELECT COUNT(*) FROM vocab_expressions 
                    WHERE user_id = :user_id AND language = :language
                """), {"user_id": user_id, "language": target_language}).fetchone()
            else:
                vocab_verified = session.execute(text("""
                    SELECT COUNT(*) FROM vocab_expressions 
                    WHERE language = :language
                """), {"language": target_language}).fetchone()
            
            vocab_verified_count = vocab_verified[0] if vocab_verified else 0
            if vocab_count > 0:
                if vocab_verified_count == vocab_count:
                    print(f"   ✅ Vocab验证成功：{vocab_verified_count}/{vocab_count} 个记录的language为 '{target_language}'")
                else:
                    print(f"   ⚠️  Vocab验证：{vocab_verified_count}/{vocab_count} 个记录的language为 '{target_language}'")
        
        if 'grammar_rules' in table_names:
            if grammar_has_user_id:
                grammar_verified = session.execute(text("""
                    SELECT COUNT(*) FROM grammar_rules 
                    WHERE user_id = :user_id AND language = :language
                """), {"user_id": user_id, "language": target_language}).fetchone()
            else:
                grammar_verified = session.execute(text("""
                    SELECT COUNT(*) FROM grammar_rules 
                    WHERE language = :language
                """), {"language": target_language}).fetchone()
            
            grammar_verified_count = grammar_verified[0] if grammar_verified else 0
            if grammar_count > 0:
                if grammar_verified_count == grammar_count:
                    print(f"   ✅ Grammar验证成功：{grammar_verified_count}/{grammar_count} 个记录的language为 '{target_language}'")
                else:
                    print(f"   ⚠️  Grammar验证：{grammar_verified_count}/{grammar_count} 个记录的language为 '{target_language}'")
        
        return True
            
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
    print("数据库迁移：将user 2的所有vocab和grammar的language字段设置为'德文'")
    print("="*60)
    
    # 迁移所有环境的数据库
    environments = [
        ('development', DB_FILES['dev']),
        ('production', DB_FILES['prod']),
    ]
    
    success_count = 0
    total_tasks = len(environments)
    
    for env, db_path in environments:
        if update_user2_vocab_grammar_language(env, db_path, target_language="德文", user_id=2):
            success_count += 1
    
    print("\n" + "="*60)
    if success_count == total_tasks:
        print("✅ 所有迁移完成！")
    else:
        print(f"⚠️  部分迁移完成 ({success_count}/{total_tasks})")
    print("="*60)
    print("\n下一步：")
    print("1. 验证数据库中的language字段")
    print("2. 测试vocab和grammar的查询功能")
    print("3. 确认user 2的vocab和grammar都显示为'德文'")


if __name__ == "__main__":
    main()

