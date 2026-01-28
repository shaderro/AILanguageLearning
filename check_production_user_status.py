#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查生产环境 PostgreSQL 数据库中用户的角色和 token 状态
用于排查为什么余额小于0还能使用AI功能
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

def check_production_user_status(user_id=None):
    """检查生产环境用户的角色和 token 状态"""
    print("=" * 80)
    print("检查生产环境 PostgreSQL 数据库中用户的角色和 token 状态")
    print("=" * 80)
    
    # 从环境变量读取环境配置（生产环境）
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "production")  # 默认使用 production
    
    print(f"\n📦 使用环境: {environment}")
    print(f"⚠️  注意：确保环境变量指向生产环境的 PostgreSQL 数据库")
    
    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    
    try:
        # 查询用户
        if user_id:
            users = session.query(User).filter(User.user_id == user_id).all()
            if not users:
                print(f"\n❌ User {user_id} 不存在")
                return 1
        else:
            users = session.query(User).order_by(User.user_id).all()
        
        if not users:
            print("\n❌ 没有找到任何用户")
            return 1
        
        # 显示所有用户的状态
        print(f"\n📊 用户状态总览（共 {len(users)} 个用户）:")
        print("=" * 80)
        
        for user in users:
            role = user.role or 'user'  # 默认为 'user'
            token_balance = user.token_balance or 0
            points = token_balance / 10000
            
            # 判断是否受限制
            is_admin = (role == 'admin')
            is_insufficient = (not is_admin and token_balance < 1000)
            
            status_icon = "👑" if is_admin else "👤"
            status_text = "Admin（无限制）" if is_admin else "User（受限制）"
            
            if is_insufficient:
                status_text += " ⚠️ 积分不足"
            
            print(f"\n{status_icon} User ID: {user.user_id}")
            print(f"   Email: {user.email or 'N/A'}")
            print(f"   角色 (role): {role}")
            print(f"   Token Balance: {token_balance:,}")
            print(f"   积分: {points:.1f}")
            print(f"   状态: {status_text}")
            
            # 特别标记问题用户
            if user_id == user.user_id or (not is_admin and token_balance < 0):
                print(f"   ⚠️  当前用户：余额为负数但仍可能可以使用AI功能")
                print(f"   🔍 检查项：")
                print(f"      - role 字段值: '{role}' (期望: 'user')")
                print(f"      - role 是否为 NULL: {user.role is None}")
                print(f"      - role 数据类型: {type(user.role)}")
                print(f"      - token_balance: {token_balance} (期望: >= 1000)")
        
        # 特别检查 user_id = 5
        user_5 = session.query(User).filter(User.user_id == 5).first()
        if user_5:
            print(f"\n" + "=" * 80)
            print(f"🔍 详细检查 User 5（从日志中看到的用户）:")
            print("=" * 80)
            print(f"   User ID: {user_5.user_id}")
            print(f"   Email: {user_5.email or 'N/A'}")
            print(f"   role 原始值: {repr(user_5.role)}")
            print(f"   role 类型: {type(user_5.role)}")
            print(f"   role 是否为 None: {user_5.role is None}")
            print(f"   role 是否为 'admin': {user_5.role == 'admin'}")
            print(f"   role 是否为 'user': {user_5.role == 'user'}")
            print(f"   token_balance: {user_5.token_balance}")
            print(f"   token_balance 类型: {type(user_5.token_balance)}")
            
            # 检查后端判断逻辑
            print(f"\n   🔧 后端判断逻辑检查：")
            role_for_check = user_5.role or 'user'
            is_admin_check = (role_for_check == 'admin')
            is_insufficient_check = (not is_admin_check and (user_5.token_balance is None or user_5.token_balance < 1000))
            
            print(f"      role_for_check = role or 'user' = '{role_for_check}'")
            print(f"      is_admin = (role_for_check == 'admin') = {is_admin_check}")
            print(f"      is_insufficient = (not is_admin and token_balance < 1000) = {is_insufficient_check}")
            
            if is_admin_check:
                print(f"      ⚠️  问题：用户是 admin，不受 token 限制")
            elif not is_insufficient_check:
                print(f"      ⚠️  问题：is_insufficient 为 False，说明判断逻辑可能有问题")
                print(f"          - token_balance = {user_5.token_balance}")
                print(f"          - token_balance < 1000 = {user_5.token_balance < 1000 if user_5.token_balance is not None else 'N/A'}")
            else:
                print(f"      ✅ 判断逻辑正确：用户应该被限制")
        
        # 统计信息
        print(f"\n" + "=" * 80)
        print(f"📊 统计信息:")
        print("=" * 80)
        admin_count = sum(1 for u in users if (u.role or 'user') == 'admin')
        user_count = len(users) - admin_count
        negative_balance_count = sum(1 for u in users if (u.token_balance or 0) < 0)
        insufficient_count = sum(1 for u in users if (u.role or 'user') != 'admin' and (u.token_balance or 0) < 1000)
        
        print(f"   总用户数: {len(users)}")
        print(f"   Admin 用户: {admin_count}")
        print(f"   User 用户: {user_count}")
        print(f"   余额为负数的用户: {negative_balance_count}")
        print(f"   积分不足的用户（非admin且<1000）: {insufficient_count}")
        
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
    import sys
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    exit_code = check_production_user_status(user_id)
    sys.exit(exit_code)
