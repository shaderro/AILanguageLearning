#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询本地开发环境中的用户角色信息
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

def check_user_roles():
    """查询用户角色信息"""
    print("=" * 80)
    print("查询本地开发环境中的用户角色信息")
    print("=" * 80)
    
    # 从环境变量读取环境配置
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    print(f"\n📦 使用环境: {environment}")
    
    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    
    try:
        # 查询所有用户
        users = session.query(User).order_by(User.user_id).all()
        
        if not users:
            print("\n❌ 没有找到任何用户")
            return 1
        
        # 按角色分组
        admin_users = []
        regular_users = []
        no_role_users = []
        
        for user in users:
            role = user.role or 'user'  # 默认为 'user'
            token_balance = user.token_balance or 0
            points = token_balance / 10000
            
            user_info = {
                'user_id': user.user_id,
                'email': user.email or 'N/A',
                'role': role,
                'token_balance': token_balance,
                'points': points
            }
            
            if role == 'admin':
                admin_users.append(user_info)
            elif role == 'user':
                regular_users.append(user_info)
            else:
                no_role_users.append(user_info)
        
        # 显示结果
        print(f"\n📊 用户统计:")
        print(f"  - 总用户数: {len(users)}")
        print(f"  - Admin 用户: {len(admin_users)}")
        print(f"  - User 用户: {len(regular_users)}")
        print(f"  - 其他角色: {len(no_role_users)}")
        
        # 显示 Admin 用户
        if admin_users:
            print(f"\n👑 Admin 用户（无限制 token）:")
            print("-" * 80)
            for user in admin_users:
                print(f"  User ID: {user['user_id']}")
                print(f"    Email: {user['email']}")
                print(f"    角色: {user['role']}")
                print(f"    Token: {user['token_balance']:,}")
                print(f"    积分: {user['points']:.1f}")
                print()
        else:
            print(f"\n⚠️ 没有 Admin 用户")
        
        # 显示普通用户
        if regular_users:
            print(f"\n👤 User 用户（受 token 限制）:")
            print("-" * 80)
            for user in regular_users:
                print(f"  User ID: {user['user_id']}")
                print(f"    Email: {user['email']}")
                print(f"    角色: {user['role']}")
                print(f"    Token: {user['token_balance']:,}")
                print(f"    积分: {user['points']:.1f}")
                print()
        else:
            print(f"\n⚠️ 没有 User 用户")
        
        # 显示其他角色用户
        if no_role_users:
            print(f"\n❓ 其他角色用户:")
            print("-" * 80)
            for user in no_role_users:
                print(f"  User ID: {user['user_id']}")
                print(f"    Email: {user['email']}")
                print(f"    角色: {user['role']}")
                print(f"    Token: {user['token_balance']:,}")
                print(f"    积分: {user['points']:.1f}")
                print()
        
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
    exit_code = check_user_roles()
    sys.exit(exit_code)
