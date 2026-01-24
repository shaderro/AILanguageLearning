#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置 user 3 的 token_balance 为 1000（0.1 积分）
用于测试积分不足逻辑
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
from datetime import datetime

def set_user3_tokens():
    """设置 user 3 的 token_balance 为 1000"""
    print("=" * 80)
    print("设置 user 3 的 token_balance 为 1000（0.1 积分）")
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
        # 查询 user 3
        user = session.query(User).filter(User.user_id == 3).first()
        
        if not user:
            print("\n❌ user 3 不存在")
            return 1
        
        # 显示当前余额
        current_balance = user.token_balance or 0
        current_points = current_balance / 10000
        print(f"\n📊 当前状态:")
        print(f"  - User ID: {user.user_id}")
        print(f"  - 当前 Token: {current_balance:,}")
        print(f"  - 当前积分: {current_points:.1f}")
        print(f"  - 角色: {user.role or 'user'}")
        
        # 设置新的余额
        new_balance = 1000
        new_points = new_balance / 10000
        
        user.token_balance = new_balance
        user.token_updated_at = datetime.utcnow()
        
        session.commit()
        
        print(f"\n✅ 更新成功:")
        print(f"  - 新 Token: {new_balance:,}")
        print(f"  - 新积分: {new_points:.1f}")
        print(f"\n💡 现在 user 3 的积分正好是 0.1，可以测试积分不足的逻辑")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    exit_code = set_user3_tokens()
    sys.exit(exit_code)
