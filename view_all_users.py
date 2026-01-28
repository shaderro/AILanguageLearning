#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看所有用户信息（不包括密码）
注意：密码是加密存储的，无法查看明文密码
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
from database_system.business_logic.models import User

def view_all_users():
    """查看所有用户信息"""
    print("=" * 80)
    print("查看所有用户信息")
    print("=" * 80)
    print("⚠️  注意：密码是加密存储的（bcrypt哈希），无法查看明文密码")
    print("=" * 80)
    
    # 从环境变量读取环境配置
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    print(f"\n📦 使用环境: {environment}")
    print(f"⚠️  注意：确保环境变量指向正确的数据库")
    
    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    
    try:
        # 查询所有用户
        users = session.query(User).order_by(User.user_id).all()
        
        if not users:
            print("\n❌ 没有找到任何用户")
            return 1
        
        print(f"\n📊 用户列表（共 {len(users)} 个用户）:")
        print("=" * 80)
        
        for user in users:
            role = user.role or 'user'
            token_balance = user.token_balance or 0
            points = token_balance / 10000
            password_status = "已设置密码" if user.password_hash else "未设置密码"
            
            print(f"\n👤 User ID: {user.user_id}")
            print(f"   Email: {user.email or 'N/A'}")
            print(f"   角色: {role}")
            print(f"   Token: {token_balance:,}")
            print(f"   积分: {points:.1f}")
            print(f"   密码: {password_status}")
            print(f"   创建时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}")
            if user.token_updated_at:
                print(f"   Token更新时间: {user.token_updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 统计信息
        print(f"\n" + "=" * 80)
        print(f"📊 统计信息:")
        print("=" * 80)
        admin_count = sum(1 for u in users if (u.role or 'user') == 'admin')
        user_count = len(users) - admin_count
        with_email_count = sum(1 for u in users if u.email)
        with_password_count = sum(1 for u in users if u.password_hash)
        
        print(f"   总用户数: {len(users)}")
        print(f"   Admin 用户: {admin_count}")
        print(f"   User 用户: {user_count}")
        print(f"   有邮箱的用户: {with_email_count}")
        print(f"   已设置密码的用户: {with_password_count}")
        print("=" * 80)
        
        print(f"\n💡 提示:")
        print(f"   - 密码是加密存储的（bcrypt哈希），无法查看明文密码")
        print(f"   - 如果需要重置密码，可以使用 reset_user_password.py 脚本")
        print(f"   - 或者通过前端登录页面使用'忘记密码'功能")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    exit_code = view_all_users()
    sys.exit(exit_code)
