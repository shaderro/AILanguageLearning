#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加邀请码和 Token 系统相关表结构

迁移内容：
1. users 表新增字段：
   - role: VARCHAR(32) NOT NULL DEFAULT 'user'（角色：admin/user）
   - token_balance: BIGINT NOT NULL DEFAULT 0（当前 token 余额）
   - token_updated_at: DATETIME NULL（最近一次余额变动时间）
   - 索引：idx_users_role

2. 新建 invite_codes 表（一次性邀请码）：
   - id, code, token_grant, status, created_at, expires_at
   - redeemed_by_user_id, redeemed_at, note
   - 唯一约束：code
   - 索引：status, redeemed_by_user_id

3. 新建 token_ledger 表（token 账本）：
   - id, user_id, delta, reason, ref_type, ref_id
   - created_at, idempotency_key
   - 索引：user_id, (user_id, created_at)
   - 唯一约束：idempotency_key
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
from database_system.business_logic.models import Base, InviteCode, TokenLedger
from sqlalchemy import inspect, text


def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return False
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"[WARN] 检查列时出错: {e}")
        return False


def check_table_exists(engine, table_name):
    """检查表是否存在"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except Exception as e:
        print(f"[WARN] 检查表时出错: {e}")
        return False


def check_index_exists(engine, table_name, index_name):
    """检查索引是否存在"""
    try:
        inspector = inspect(engine)
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except Exception as e:
        print(f"[WARN] 检查索引时出错: {e}")
        return False


def add_user_columns(engine, session):
    """给 users 表添加新字段"""
    try:
        print("   [CHECK] 检查 users 表字段...")
        
        # 检查并添加 role 字段
        if not check_column_exists(engine, 'users', 'role'):
            print("   [ADD] 添加 role 字段...")
            # SQLite 和 PostgreSQL 都支持添加带默认值的列
            alter_sql = text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'")
            session.execute(alter_sql)
            session.commit()
            print("   [OK] role 字段添加成功")
        else:
            print("   [SKIP] role 字段已存在，跳过")
        
        # 检查并添加 token_balance 字段
        if not check_column_exists(engine, 'users', 'token_balance'):
            print("   [ADD] 添加 token_balance 字段...")
            # SQLite 使用 INTEGER，PostgreSQL 使用 BIGINT
            # SQLAlchemy 会根据数据库类型自动转换
            alter_sql = text("ALTER TABLE users ADD COLUMN token_balance BIGINT NOT NULL DEFAULT 0")
            session.execute(alter_sql)
            session.commit()
            print("   [OK] token_balance 字段添加成功")
        else:
            print("   [SKIP] token_balance 字段已存在，跳过")
        
        # 检查并添加 token_updated_at 字段
        if not check_column_exists(engine, 'users', 'token_updated_at'):
            print("   [ADD] 添加 token_updated_at 字段...")
            alter_sql = text("ALTER TABLE users ADD COLUMN token_updated_at DATETIME")
            session.execute(alter_sql)
            session.commit()
            print("   [OK] token_updated_at 字段添加成功")
        else:
            print("   [SKIP] token_updated_at 字段已存在，跳过")
        
        # 检查并创建 role 索引
        if not check_index_exists(engine, 'users', 'idx_users_role'):
            print("   [ADD] 创建 idx_users_role 索引...")
            create_index_sql = text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            session.execute(create_index_sql)
            session.commit()
            print("   [OK] idx_users_role 索引创建成功")
        else:
            print("   [SKIP] idx_users_role 索引已存在，跳过")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   [ERROR] 添加 users 表字段失败: {e}")
        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
            print("   [INFO] 字段可能已存在，继续...")
            return True
        raise


def create_invite_codes_table(engine, session):
    """创建 invite_codes 表"""
    try:
        if check_table_exists(engine, 'invite_codes'):
            print("   [SKIP] invite_codes 表已存在，跳过")
            return True
        
        print("   [CREATE] 创建 invite_codes 表...")
        
        # 使用 SQLAlchemy 的 Base.metadata.create_all 创建表
        # 这样可以确保表结构与 models.py 定义一致
        InviteCode.__table__.create(engine, checkfirst=False)
        session.commit()
        
        print("   [OK] invite_codes 表创建成功")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   [ERROR] 创建 invite_codes 表失败: {e}")
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print("   [INFO] 表可能已存在，继续...")
            return True
        raise


def create_token_ledger_table(engine, session):
    """创建 token_ledger 表"""
    try:
        if check_table_exists(engine, 'token_ledger'):
            print("   [SKIP] token_ledger 表已存在，跳过")
            return True
        
        print("   [CREATE] 创建 token_ledger 表...")
        
        # 使用 SQLAlchemy 的 Base.metadata.create_all 创建表
        TokenLedger.__table__.create(engine, checkfirst=False)
        session.commit()
        
        print("   [OK] token_ledger 表创建成功")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"   [ERROR] 创建 token_ledger 表失败: {e}")
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print("   [INFO] 表可能已存在，继续...")
            return True
        raise


def migrate_database(environment, db_path):
    """迁移指定环境的数据库"""
    print(f"\n{'='*60}")
    print(f"[ENV] 迁移环境: {environment}")
    print(f"[PATH] 数据库路径: {db_path}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(db_path) and 'sqlite' in db_path:
        print(f"[WARN] 数据库文件不存在: {db_path}")
        print("   将创建新数据库（包含所有新表结构）")
    
    # 1. 初始化数据库管理器
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 2. 检查 users 表是否存在
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            print("[WARN] users 表不存在，将创建所有表...")
            # 如果表不存在，创建所有表（会包含新字段）
            Base.metadata.create_all(engine)
            print("[OK] 所有表已创建（包含新字段）")
        else:
            # 3. 添加 users 表新字段
            print("\n[STEP 1/3] 更新 users 表...")
            add_user_columns(engine, session)
            
            # 4. 创建 invite_codes 表
            print("\n[STEP 2/3] 创建 invite_codes 表...")
            create_invite_codes_table(engine, session)
            
            # 5. 创建 token_ledger 表
            print("\n[STEP 3/3] 创建 token_ledger 表...")
            create_token_ledger_table(engine, session)
        
        # 6. 验证迁移结果
        print("\n[VERIFY] 验证迁移结果...")
        success = True
        
        if not check_column_exists(engine, 'users', 'role'):
            print("   [FAIL] users.role 字段验证失败")
            success = False
        if not check_column_exists(engine, 'users', 'token_balance'):
            print("   [FAIL] users.token_balance 字段验证失败")
            success = False
        if not check_column_exists(engine, 'users', 'token_updated_at'):
            print("   [FAIL] users.token_updated_at 字段验证失败")
            success = False
        if not check_table_exists(engine, 'invite_codes'):
            print("   [FAIL] invite_codes 表验证失败")
            success = False
        if not check_table_exists(engine, 'token_ledger'):
            print("   [FAIL] token_ledger 表验证失败")
            success = False
        
        if success:
            print(f"\n[OK] {environment} 环境迁移完成！")
            return True
        else:
            print(f"\n[FAIL] {environment} 环境验证失败")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {environment} 环境迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("[MIGRATION] 开始迁移：添加邀请码和 Token 系统")
    print("="*60)
    
    # 从配置文件获取数据库路径
    from database_system.data_storage.config.config import DB_FILES
    
    # 只迁移 development 环境（本地 dev 数据库）
    environments = {
        'development': DB_FILES['dev'],
    }
    
    success_count = 0
    total_count = len(environments)
    
    for env, db_path in environments.items():
        try:
            if migrate_database(env, db_path):
                success_count += 1
        except Exception as e:
            print(f"\n[ERROR] {env} 环境迁移失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"[RESULT] 迁移完成：{success_count}/{total_count} 个环境成功")
    print("="*60)
    
    if success_count == total_count:
        print("\n[OK] 本地 dev 数据库迁移成功！")
        print("\n[NEXT] 下一步：")
        print("   1. 在 pgAdmin 中对生产数据库执行相同的 migration SQL")
        print("   2. 验证表结构是否正确")
        print("   3. 测试邀请码兑换和 token 扣费功能")
        return 0
    else:
        print(f"\n[FAIL] 迁移失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
