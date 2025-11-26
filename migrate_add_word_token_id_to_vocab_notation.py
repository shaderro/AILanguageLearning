#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移：在 vocab_notations 表中添加 word_token_id 字段

此迁移脚本会：
1. 在 vocab_notations 表中添加 word_token_id 字段（用于非空格语言的 word token 级别标注）

适用场景：
- 支持中文、日文等非空格语言的 word token 级别词汇标注
- 空格语言（英文、德文等）不受影响，word_token_id 为 NULL

执行步骤：
1. 备份数据库
2. 在 vocab_notations 表中添加 word_token_id 字段
3. 验证迁移结果
"""

import sys
import os
import shutil
from datetime import datetime
from sqlalchemy import inspect, text

# 添加路径（脚本在根目录，database_system 也在根目录）
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES


def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_word_token_id_to_vocab_notation(engine, session):
    """在 vocab_notations 表中添加 word_token_id 字段"""
    try:
        if check_column_exists(engine, 'vocab_notations', 'word_token_id'):
            print("   ℹ️  vocab_notations.word_token_id 字段已存在，跳过")
            return True
        
        print("   📝 添加 word_token_id 字段到 vocab_notations 表...")
        # 注意：SQLite 的 ALTER TABLE ADD COLUMN 不支持直接添加外键约束
        # 我们只添加列，外键约束在模型定义中，SQLAlchemy 会在创建新表时应用
        # 对于现有表，应用层会维护引用完整性
        session.execute(text("""
            ALTER TABLE vocab_notations 
            ADD COLUMN word_token_id INTEGER
        """))
        session.commit()
        print("   ✅ word_token_id 字段已添加")
        print("   ℹ️  注意：SQLite 不支持在 ALTER TABLE 时添加外键约束")
        print("   ℹ️  外键关系由 SQLAlchemy 模型定义，应用层会维护引用完整性")
        return True
    except Exception as e:
        session.rollback()
        print(f"   ❌ 添加 word_token_id 字段失败: {e}")
        raise


def migrate_database(environment='development'):
    """迁移指定环境的数据库"""
    print(f"\n{'='*60}")
    print(f"🔄 开始迁移 {environment} 环境数据库")
    print(f"{'='*60}\n")
    
    # 1. 获取数据库路径
    env_map = {
        'development': 'dev',
        'testing': 'test',
        'production': 'prod'
    }
    db_key = env_map.get(environment, 'dev')
    db_path = DB_FILES.get(db_key)
    
    if not db_path:
        print(f"❌ 找不到 {environment} 环境的数据库路径")
        return False
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        print("   将创建新数据库...")
    
    # 2. 备份数据库
    print(f"📦 步骤 1: 备份数据库...")
    backup_path = backup_database(db_path)
    
    # 3. 初始化数据库管理器
    print(f"\n📋 步骤 2: 初始化数据库连接...")
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 4. 添加 word_token_id 字段到 vocab_notations 表
        print(f"\n📋 步骤 3: 更新 vocab_notations 表...")
        add_word_token_id_to_vocab_notation(engine, session)
        
        # 5. 验证迁移结果
        print(f"\n📋 步骤 4: 验证迁移结果...")
        has_word_token_id = check_column_exists(engine, 'vocab_notations', 'word_token_id')
        
        if has_word_token_id:
            print(f"\n{'='*60}")
            print(f"✅ {environment} 环境迁移完成！")
            print(f"{'='*60}")
            print(f"\n迁移结果：")
            print(f"  ✅ vocab_notations.word_token_id 字段: {'已添加' if has_word_token_id else '未添加'}")
            if backup_path:
                print(f"\n备份文件: {backup_path}")
            return True
        else:
            print(f"\n❌ {environment} 环境验证失败")
            print(f"  - vocab_notations.word_token_id: {'✅' if has_word_token_id else '❌'}")
            return False
            
    except Exception as e:
        print(f"\n❌ {environment} 环境迁移失败: {e}")
        if backup_path:
            print(f"\n可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("数据库迁移：在 vocab_notations 表中添加 word_token_id 字段")
    print("="*60)
    print("\n此迁移将：")
    print("  1. 在 vocab_notations 表中添加 word_token_id 字段（可为 NULL）")
    print("\n注意：")
    print("  - 此迁移对现有数据无影响（word_token_id 默认为 NULL）")
    print("  - 空格语言（英文、德文等）不受影响")
    print("  - 仅非空格语言（中文、日文等）会使用 word_token_id")
    print("="*60)
    
    # 询问要迁移的环境
    print("\n请选择要迁移的环境：")
    print("  1. development (开发环境)")
    print("  2. testing (测试环境)")
    print("  3. production (生产环境)")
    print("  4. 全部环境")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    environments = {
        '1': ['development'],
        '2': ['testing'],
        '3': ['production'],
        '4': ['development', 'testing', 'production']
    }
    
    selected_envs = environments.get(choice, ['development'])
    
    if choice == '4':
        confirm = input("\n⚠️  确定要迁移所有环境吗？(yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ 操作已取消")
            return
    
    # 执行迁移
    success_count = 0
    for env in selected_envs:
        try:
            if migrate_database(env):
                success_count += 1
        except Exception as e:
            print(f"\n❌ {env} 环境迁移失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"迁移完成：{success_count}/{len(selected_envs)} 个环境成功")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

