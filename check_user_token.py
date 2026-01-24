#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询指定用户的 token balance
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

def check_user_token(user_id):
    """查询指定用户的 token balance"""
    print("=" * 80)
    print(f"查询 User {user_id} 的 Token Balance")
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
        # 查询用户
        user = session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            print(f"\n❌ User {user_id} 不存在")
            return 1
        
        # 获取 token balance
        token_balance = user.token_balance or 0
        points = token_balance / 10000
        
        # 显示结果
        print(f"\n📊 User {user_id} 的 Token 信息:")
        print("-" * 80)
        print(f"  User ID: {user.user_id}")
        print(f"  Email: {user.email or 'N/A'}")
        print(f"  角色: {user.role or 'user'}")
        print(f"  Token Balance: {token_balance:,}")
        print(f"  积分: {points:.1f}")
        if user.token_updated_at:
            print(f"  最后更新: {user.token_updated_at}")
        print("-" * 80)
        
        # 显示状态提示
        if token_balance < 0:
            print(f"\n⚠️  注意: Token balance 为负数")
        elif token_balance < 1000:
            print(f"\n⚠️  注意: Token balance 不足 1000（积分不足 0.1），AI 功能将被禁用")
        elif user.role == 'admin':
            print(f"\n✅ Admin 用户，不受 token 限制")
        else:
            print(f"\n✅ Token balance 充足，可以正常使用 AI 功能")
        
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
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    exit_code = check_user_token(user_id)
    sys.exit(exit_code)
