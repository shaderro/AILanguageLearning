#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出所有邀请码及其使用状态
用于快速查看哪些邀请码已创建、哪些已被使用
"""

import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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
from database_system.business_logic.models import InviteCode, User


def list_invite_codes(environment=None):
    """列出所有邀请码及其使用状态"""
    if environment is None:
        try:
            from backend.config import ENV
            environment = ENV
        except ImportError:
            environment = os.getenv("ENV", "development")

    print("=" * 80)
    print("邀请码列表及使用状态")
    print("=" * 80)
    print(f"\n📦 数据库环境: {environment}")
    print("   （可通过环境变量 ENV=production 连接线上库）")
    print("=" * 80)

    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()

    try:
        codes = session.query(InviteCode).order_by(InviteCode.created_at.desc()).all()

        if not codes:
            print("\n❌ 未找到任何邀请码")
            return 1

        # 统计
        active_count = sum(1 for c in codes if c.status == 'active')
        redeemed_count = sum(1 for c in codes if c.status == 'redeemed')
        disabled_count = sum(1 for c in codes if c.status == 'disabled')
        expired_count = sum(1 for c in codes if c.status == 'expired')

        print(f"\n📊 统计: 共 {len(codes)} 个 | 可用 {active_count} | 已使用 {redeemed_count} | 已禁用 {disabled_count} | 已过期 {expired_count}")
        print("-" * 80)

        for c in codes:
            points = (c.token_grant or 0) / 10000
            status_emoji = {"active": "🟢", "redeemed": "✅", "disabled": "🔴", "expired": "⏰"}.get(c.status, "⚪")
            status_text = {"active": "可用", "redeemed": "已使用", "disabled": "已禁用", "expired": "已过期"}.get(c.status, c.status)

            line = f"{status_emoji} {c.code} | {c.token_grant:,} token ({points:.0f}积分) | {status_text}"
            if c.redeemed_by_user_id:
                user = session.query(User).filter(User.user_id == c.redeemed_by_user_id).first()
                email = user.email if user else f"user_id={c.redeemed_by_user_id}"
                line += f" | 用户: {email}"
                if c.redeemed_at:
                    line += f" | 兑换于 {c.redeemed_at.strftime('%Y-%m-%d %H:%M')}"
            if c.note:
                line += f" | 备注: {c.note[:30]}"
            print(line)

        print("=" * 80)
        print("\n💡 提示:")
        print("   - 添加新邀请码: python generate_invite_codes.py")
        print("   - 查看完整指南: INVITE_CODES_AND_BETA_USERS_GUIDE.md")
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
    env = os.getenv("ENV")
    exit_code = list_invite_codes(env)
    sys.exit(exit_code)
