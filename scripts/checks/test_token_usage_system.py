#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Token 使用记录与扣减机制

测试内容：
1. 检查 token_logs 表是否存在
2. 测试 API 调用后 token 扣减
3. 测试 user profile 接口返回 token 使用信息
4. 验证数据库记录
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
from database_system.business_logic.models import User, TokenLog, TokenLedger
from sqlalchemy import inspect, func
from datetime import datetime



def check_table_exists(engine, table_name):
    """检查表是否存在"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except Exception as e:
        print(f"❌ 检查表时出错: {e}")
        return False


def test_table_exists():
    """测试 1: 检查 token_logs 表是否存在"""
    print("=" * 80)
    print("测试 1: 检查 token_logs 表是否存在")
    print("=" * 80)
    
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    db_manager = DatabaseManager(environment)
    engine = db_manager.get_engine()
    
    if check_table_exists(engine, 'token_logs'):
        print("✅ token_logs 表存在")
        
        # 检查字段
        inspector = inspect(engine)
        columns = {col['name']: col['type'] for col in inspector.get_columns('token_logs')}
        required_fields = ['id', 'user_id', 'total_tokens', 'prompt_tokens', 'completion_tokens', 'model_name', 'created_at']
        
        print("\n📋 表字段检查:")
        for field in required_fields:
            if field in columns:
                print(f"  ✅ {field}: {columns[field]}")
            else:
                print(f"  ❌ {field}: 缺失")
        
        return True
    else:
        print("❌ token_logs 表不存在，请先运行迁移脚本:")
        print("   python migrate_add_token_logs_table.py")
        return False


def test_user_token_balance():
    """测试 2: 检查用户 token 余额"""
    print("\n" + "=" * 80)
    print("测试 2: 检查用户 token 余额")
    print("=" * 80)
    
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    
    try:
        # 获取前 5 个用户
        users = session.query(User).limit(5).all()
        
        if not users:
            print("⚠️  没有找到用户，请先创建测试用户")
            return False
        
        print(f"\n📊 用户 Token 余额:")
        for user in users:
            balance = user.token_balance or 0
            print(f"  - 用户 ID {user.user_id}: {balance:,} tokens")
        
        return True
    except Exception as e:
        print(f"❌ 查询用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_token_logs():
    """测试 3: 检查 token_logs 记录"""
    print("\n" + "=" * 80)
    print("测试 3: 检查 token_logs 记录")
    print("=" * 80)
    
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    
    try:
        # 统计总记录数
        total_logs = session.query(func.count(TokenLog.id)).scalar()
        print(f"\n📊 Token 使用记录总数: {total_logs}")
        
        if total_logs > 0:
            # 获取最近的 5 条记录
            recent_logs = session.query(TokenLog).order_by(TokenLog.created_at.desc()).limit(5).all()
            
            print(f"\n📋 最近 5 条记录:")
            for log in recent_logs:
                print(f"  - ID {log.id}: 用户 {log.user_id} | "
                      f"总 tokens: {log.total_tokens} | "
                      f"Prompt: {log.prompt_tokens} | "
                      f"Completion: {log.completion_tokens} | "
                      f"模型: {log.model_name} | "
                      f"时间: {log.created_at}")
            
            # 按用户统计
            user_stats = (
                session.query(
                    TokenLog.user_id,
                    func.count(TokenLog.id).label('count'),
                    func.sum(TokenLog.total_tokens).label('total')
                )
                .group_by(TokenLog.user_id)
                .all()
            )
            
            print(f"\n📊 按用户统计:")
            for user_id, count, total in user_stats:
                print(f"  - 用户 {user_id}: {count} 次调用, 累计 {total or 0} tokens")
        else:
            print("ℹ️  还没有 token 使用记录")
            print("   提示: 运行后端并调用 /api/chat 接口后，记录会自动创建")
        
        return True
    except Exception as e:
        print(f"❌ 查询 token_logs 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_token_ledger():
    """测试 4: 检查 token_ledger 记录"""
    print("\n" + "=" * 80)
    print("测试 4: 检查 token_ledger 记录（账本）")
    print("=" * 80)
    
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")
    
    db_manager = DatabaseManager(environment)
    session = db_manager.get_session()
    
    try:
        # 统计 ai_usage 类型的记录
        ai_usage_count = (
            session.query(func.count(TokenLedger.id))
            .filter(TokenLedger.reason == 'ai_usage')
            .scalar()
        )
        
        print(f"\n📊 AI 使用记录数: {ai_usage_count}")
        
        if ai_usage_count > 0:
            # 获取最近的 5 条 ai_usage 记录
            recent_ledger = (
                session.query(TokenLedger)
                .filter(TokenLedger.reason == 'ai_usage')
                .order_by(TokenLedger.created_at.desc())
                .limit(5)
                .all()
            )
            
            print(f"\n📋 最近 5 条 AI 使用账本记录:")
            for ledger in recent_ledger:
                print(f"  - ID {ledger.id}: 用户 {ledger.user_id} | "
                      f"变动: {ledger.delta} tokens | "
                      f"原因: {ledger.reason} | "
                      f"时间: {ledger.created_at}")
        else:
            print("ℹ️  还没有 AI 使用账本记录")
        
        return True
    except Exception as e:
        print(f"❌ 查询 token_ledger 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_api_endpoint_info():
    """测试 5: 显示 API 测试信息"""
    print("\n" + "=" * 80)
    print("测试 5: API 测试指南")
    print("=" * 80)
    
    print("""
📝 手动测试步骤:

1. 启动后端服务器:
   - 确保后端正在运行（通常是 http://localhost:8000）

2. 获取用户认证 token:
   - 调用 POST /api/auth/login 登录
   - 保存返回的 access_token

3. 测试 Chat API（会触发 token 扣减）:
   - 调用 POST /api/chat
   - 请求头: Authorization: Bearer <access_token>
   - 请求体: {"user_question": "测试问题"}
   - 观察后端日志中的 "💰 [Token Usage]" 输出

4. 测试 User Profile API（查看 token 使用情况）:
   - 调用 GET /api/auth/me
   - 请求头: Authorization: Bearer <access_token>
   - 检查返回的 token_balance 和 total_tokens_used

5. 验证数据库:
   - 运行此测试脚本查看 token_logs 和 token_ledger 记录
   - 或直接查询数据库

📋 预期结果:
  - 每次 API 调用后，token_balance 减少
  - total_tokens_used 增加
  - token_logs 表中有新记录
  - token_ledger 表中有 ai_usage 记录
  - 后端日志输出 token 使用信息
""")


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("Token 使用记录与扣减机制 - 测试脚本")
    print("=" * 80)
    
    results = []
    
    # 测试 1: 检查表是否存在
    results.append(("表存在性检查", test_table_exists()))
    
    # 测试 2: 检查用户 token 余额
    results.append(("用户 Token 余额", test_user_token_balance()))
    
    # 测试 3: 检查 token_logs 记录
    results.append(("Token 使用记录", test_token_logs()))
    
    # 测试 4: 检查 token_ledger 记录
    results.append(("Token 账本记录", test_token_ledger()))
    
    # 测试 5: API 测试指南
    test_api_endpoint_info()
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ 所有基础测试通过！")
        print("   接下来可以按照上面的 API 测试指南进行手动测试")
    else:
        print("\n⚠️  部分测试未通过，请检查上述错误信息")


if __name__ == "__main__":
    main()
