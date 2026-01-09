#!/usr/bin/env python3
"""
初始化 PostgreSQL 数据库表结构

此脚本用于在 PostgreSQL 数据库中创建所有必要的表。
适用于首次部署到云平台（如 Render）时使用。

使用方法：
1. 确保环境变量 DATABASE_URL 已设置
2. 运行: python database_system/scripts/init_postgresql.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import Base


def init_postgresql_database(environment='production'):
    """
    初始化 PostgreSQL 数据库表结构
    
    Args:
        environment: 环境名称 (development/testing/production)
    """
    print("\n" + "="*60)
    print("🚀 初始化 PostgreSQL 数据库")
    print("="*60)
    
    # 检查环境变量
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ 错误: 未找到 DATABASE_URL 环境变量")
        print("   请在 Render 环境变量中设置 DATABASE_URL")
        return False
    
    # 检查是否是 PostgreSQL
    if not (database_url.startswith('postgresql://') or 
            database_url.startswith('postgresql+psycopg2://') or
            database_url.startswith('postgres://')):
        print(f"⚠️  警告: DATABASE_URL 不是 PostgreSQL 连接字符串")
        print(f"   当前值: {database_url[:50]}...")
        print("   继续执行...")
    
    try:
        # 创建数据库管理器
        print(f"\n📋 步骤 1: 连接数据库（环境: {environment}）...")
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        
        # 测试连接
        print("   ✅ 数据库连接成功")
        
        # 创建所有表
        print(f"\n📋 步骤 2: 创建数据库表结构...")
        Base.metadata.create_all(engine)
        print("   ✅ 所有表已创建")
        
        # 显示创建的表
        print(f"\n📋 步骤 3: 验证表结构...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"   ✅ 共创建 {len(tables)} 个表:")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"      - {table} ({len(columns)} 列)")
        
        print("\n" + "="*60)
        print("✅ PostgreSQL 数据库初始化完成！")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: 数据库初始化失败")
        print(f"   原因: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    # 从环境变量获取环境名称
    env = os.getenv('ENV', 'production')
    
    print(f"\n环境: {env}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', '未设置')[:50]}...")
    
    # 询问确认（如果不在云平台环境）
    if not os.getenv('RENDER') and not os.getenv('RAILWAY'):
        response = input("\n确定要初始化数据库吗？(输入 yes 继续): ")
        if response.lower() != 'yes':
            print("❌ 操作已取消")
            return
    
    success = init_postgresql_database(env)
    
    if success:
        print("\n✅ 数据库初始化成功！")
        print("现在可以启动应用并开始使用了。")
    else:
        print("\n❌ 数据库初始化失败！")
        print("请检查错误信息并重试。")
        sys.exit(1)


if __name__ == '__main__':
    main()

