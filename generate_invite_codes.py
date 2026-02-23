#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成邀请码脚本
生成5个邀请码，每个邀请码提供 1,000,000 tokens (100积分)
"""

import sys
import os
import io
import string
import random
from datetime import datetime, timezone

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 必须在导入 database_system 之前加载 .env，否则 DATABASE_URL 无法被读取
try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).resolve().parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import InviteCode

def generate_invite_code(length=8):
    """生成随机邀请码（大写字母和数字）"""
    characters = string.ascii_uppercase + string.digits
    # 排除容易混淆的字符：0, O, 1, I
    characters = characters.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    return ''.join(random.choice(characters) for _ in range(length))

def create_invite_codes(count=5, token_grant=1000000):
    """创建指定数量的邀请码"""
    print("=" * 80)
    print(f"生成 {count} 个邀请码，每个邀请码提供 {token_grant:,} tokens ({token_grant/10000:.0f} 积分)")
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
        created_codes = []
        
        for i in range(count):
            # 生成唯一的邀请码
            max_attempts = 100
            code = None
            for attempt in range(max_attempts):
                candidate = generate_invite_code()
                # 检查是否已存在
                existing = session.query(InviteCode).filter(
                    InviteCode.code == candidate
                ).first()
                if not existing:
                    code = candidate
                    break
            
            if not code:
                print(f"\n❌ 无法生成唯一的邀请码（尝试了 {max_attempts} 次）")
                return 1
            
            # 创建邀请码记录
            invite_code = InviteCode(
                code=code,
                token_grant=token_grant,
                status='active',
                created_at=datetime.now(timezone.utc),
                expires_at=None,  # 不过期
                note=f"批量生成 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            session.add(invite_code)
            created_codes.append(code)
            print(f"✅ 生成邀请码 {i+1}/{count}: {code}")
        
        # 提交事务
        session.commit()
        
        # 显示结果
        print("\n" + "=" * 80)
        print("📋 生成的邀请码列表:")
        print("=" * 80)
        for i, code in enumerate(created_codes, 1):
            print(f"  {i}. {code} - {token_grant:,} tokens ({token_grant/10000:.0f} 积分)")
        
        print("\n" + "=" * 80)
        print("💡 提示:")
        print("  - 邀请码已保存到数据库")
        print("  - 状态: active（可用）")
        print("  - 每个邀请码只能被一个用户兑换一次")
        print("  - 兑换后状态将变为 redeemed")
        print("=" * 80)
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    exit_code = create_invite_codes(count=5, token_grant=1000000)
    sys.exit(exit_code)
