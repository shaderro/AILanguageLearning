#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置用户密码脚本
用于管理员重置用户密码

用法:
    python reset_user_password.py <user_id> <new_password>
    或
    python reset_user_password.py <email> <new_password>
"""

import sys
import os
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User
from backend.utils.auth import hash_password


def reset_user_password(user_identifier, new_password):
    """重置用户密码"""
    print("=" * 80)
    print("重置用户密码")
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
        # 尝试通过 user_id 或 email 查找用户
        user = None
        try:
            user_id = int(user_identifier)
            user = session.query(User).filter(User.user_id == user_id).first()
            print(f"🔍 通过 user_id={user_id} 查找用户...")
        except ValueError:
            # 如果不是数字，尝试作为 email
            user = session.query(User).filter(User.email == user_identifier).first()
            print(f"🔍 通过 email={user_identifier} 查找用户...")
        
        if not user:
            print(f"\n❌ 用户不存在: {user_identifier}")
            return 1
        
        print(f"\n📊 找到用户:")
        print(f"   User ID: {user.user_id}")
        print(f"   Email: {user.email or 'N/A'}")
        print(f"   角色: {user.role or 'user'}")
        
        # 确认操作
        print(f"\n⚠️  准备重置密码...")
        print(f"   新密码长度: {len(new_password)} 字符")
        
        # 加密新密码
        new_password_hash = hash_password(new_password)
        
        # 更新密码
        user.password_hash = new_password_hash
        session.commit()
        
        print(f"\n✅ 密码重置成功!")
        print(f"   User ID: {user.user_id}")
        print(f"   Email: {user.email or 'N/A'}")
        print(f"   新密码已加密并保存")
        print(f"\n💡 提示: 用户现在可以使用新密码登录")
        print("=" * 80)
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法:")
        print("  python reset_user_password.py <user_id或email> <new_password>")
        print("\n示例:")
        print("  python reset_user_password.py 5 mynewpassword123")
        print("  python reset_user_password.py user@example.com mynewpassword123")
        sys.exit(1)
    
    user_identifier = sys.argv[1]
    new_password = sys.argv[2]
    
    if len(new_password) < 6:
        print("⚠️  警告: 密码长度少于6个字符，建议使用更长的密码")
        response = input("是否继续? (y/n): ")
        if response.lower() != 'y':
            print("操作已取消")
            sys.exit(0)
    
    exit_code = reset_user_password(user_identifier, new_password)
    sys.exit(exit_code)
