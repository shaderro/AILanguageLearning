#!/usr/bin/env python3
"""
创建 user_article_access 表的迁移脚本

此脚本会在线上数据库中创建 user_article_access 表（如果不存在）。

使用方法：
1. 在 Render 的 Shell 中执行（或通过 SSH）
2. 或者设置 ENV=production 后本地运行（连接到线上数据库）

注意：确保环境变量 DATABASE_URL 已正确设置为线上数据库 URL
"""

import sys
import os

# 添加路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import Base, UserArticleAccess
from sqlalchemy import inspect, text
from backend.config import ENV


def check_table_exists(engine, table_name):
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_user_article_access_table(engine, session):
    """创建 user_article_access 表"""
    table_name = 'user_article_access'
    
    if check_table_exists(engine, table_name):
        print(f"✅ 表 {table_name} 已存在，跳过创建")
        return True
    
    try:
        print(f"📝 开始创建表 {table_name}...")
        
        # 使用 SQLAlchemy 的 Base.metadata.create_all 创建表
        # 只创建 UserArticleAccess 表
        UserArticleAccess.__table__.create(engine, checkfirst=True)
        
        print(f"✅ 成功创建表 {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ 创建表 {table_name} 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_table(engine, session):
    """验证表结构"""
    inspector = inspect(engine)
    
    if 'user_article_access' not in inspector.get_table_names():
        print("❌ 验证失败：表 user_article_access 不存在")
        return False
    
    columns = inspector.get_columns('user_article_access')
    column_names = [col['name'] for col in columns]
    
    expected_columns = ['id', 'user_id', 'text_id', 'last_opened_at', 'created_at', 'updated_at']
    missing_columns = [col for col in expected_columns if col not in column_names]
    
    if missing_columns:
        print(f"⚠️ 警告：缺少列 {missing_columns}")
        return False
    
    print("✅ 表结构验证通过")
    print(f"   列: {', '.join(column_names)}")
    return True


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 创建 user_article_access 表")
    print("=" * 80)
    print(f"📊 环境: {ENV}")
    print()
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(ENV)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
        
        try:
            # 创建表
            if create_user_article_access_table(engine, session):
                # 验证表结构
                verify_table(engine, session)
                print()
                print("=" * 80)
                print("✅ 迁移完成！")
                print("=" * 80)
            else:
                print()
                print("=" * 80)
                print("❌ 迁移失败！")
                print("=" * 80)
                sys.exit(1)
                
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
