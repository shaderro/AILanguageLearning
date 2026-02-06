#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断聊天历史记录跨设备同步问题
检查：
1. user_id 是否正确保存到数据库
2. user_id 类型是否一致（字符串 vs 整数）
3. 查询时是否正确使用 user_id 过滤
4. 数据库表结构和数据
"""

import sys
import os
import argparse

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database_system.database_manager import DatabaseManager
from backend.data_managers.chat_message_manager_db import ChatMessageManagerDB
from sqlalchemy import text, inspect
from collections import defaultdict

def diagnose_chat_history_sync(environment=None):
    """诊断聊天历史记录同步问题
    
    Args:
        environment: 数据库环境 ('development', 'testing', 'production')，如果不指定则从环境变量或配置读取
    """
    
    print("=" * 80)
    print("[诊断] 聊天历史记录跨设备同步诊断")
    print("=" * 80)
    
    # 1. 检查数据库连接
    print("\n[1] 检查数据库连接...")
    
    # 优先使用命令行参数，其次使用环境变量，最后使用默认值
    if environment is None:
        try:
            from backend.config import ENV
            environment = ENV
        except ImportError:
            environment = os.getenv("ENV", "development")
    
    print(f"   环境: {environment}")
    
    # 检查是否有 DATABASE_URL（生产环境需要）
    database_url = os.getenv("DATABASE_URL")
    if environment == "production":
        if not database_url:
            print(f"   [WARN] 警告: 生产环境需要设置 DATABASE_URL 环境变量")
            print(f"   请设置: set DATABASE_URL=postgresql://... (Windows)")
            print(f"   或: export DATABASE_URL=postgresql://... (Linux/Mac)")
            print(f"   或: $env:DATABASE_URL='postgresql://...' (PowerShell)")
        else:
            print(f"   [OK] 已检测到 DATABASE_URL 环境变量")
    
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        print(f"   [OK] 数据库连接成功")
        print(f"   数据库类型: {'PostgreSQL' if 'postgres' in str(db_manager.database_url).lower() else 'SQLite'}")
    except Exception as e:
        print(f"   [ERROR] 数据库连接失败: {e}")
        return
    
    # 2. 检查表是否存在
    print("\n[2] 检查 chat_messages 表...")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if 'chat_messages' in tables:
            print(f"   [OK] 表 chat_messages 存在")
            
            # 获取表结构
            columns = inspector.get_columns('chat_messages')
            print(f"   表结构:")
            for col in columns:
                print(f"     - {col['name']}: {col['type']} (nullable={col['nullable']})")
        else:
            print(f"   [ERROR] 表 chat_messages 不存在")
            print(f"   可用表: {', '.join(tables)}")
            return
    except Exception as e:
        print(f"   [ERROR] 检查表失败: {e}")
        return
    
    # 3. 检查数据中的 user_id 情况
    print("\n[3] 检查数据库中的 user_id 数据...")
    try:
        with engine.connect() as conn:
            # 统计 user_id 分布
            result = conn.execute(text("""
                SELECT 
                    user_id,
                    COUNT(*) as count,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message
                FROM chat_messages
                GROUP BY user_id
                ORDER BY count DESC
            """))
            
            rows = result.fetchall()
            if not rows:
                print("   [WARN] 表中没有数据")
            else:
                print(f"   [统计] user_id 分布统计:")
                total_messages = 0
                null_count = 0
                for row in rows:
                    user_id, count, first_msg, last_msg = row
                    total_messages += count
                    if user_id is None:
                        null_count = count
                        print(f"     - user_id=NULL: {count} 条消息")
                    else:
                        print(f"     - user_id='{user_id}' (类型: {type(user_id).__name__}): {count} 条消息")
                        print(f"       最早: {first_msg}, 最晚: {last_msg}")
                
                print(f"\n   总计: {total_messages} 条消息")
                if null_count > 0:
                    print(f"   [WARN] 警告: 有 {null_count} 条消息的 user_id 为 NULL（这些消息无法跨设备同步）")
    except Exception as e:
        print(f"   [ERROR] 查询数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 使用 ChatMessageManagerDB 测试查询
    print("\n[4] 测试 ChatMessageManagerDB 查询...")
    try:
        chat_manager = ChatMessageManagerDB(environment)
        
        # 测试：查询所有 user_id 的消息
        print("   测试1: 查询所有消息（不指定 user_id）...")
        all_messages = chat_manager.list_messages(limit=10)
        print(f"      结果: {len(all_messages)} 条消息")
        if all_messages:
            print(f"      示例消息:")
            for msg in all_messages[:3]:
                print(f"        - ID={msg['id']}, user_id={msg['user_id']} (类型: {type(msg['user_id']).__name__}), is_user={msg['is_user']}, content='{msg['content'][:30]}...'")
        
        # 测试：查询特定 user_id 的消息（字符串）
        print("\n   测试2: 查询 user_id='2' 的消息（字符串类型）...")
        user_2_str = chat_manager.list_messages(user_id='2', limit=10)
        print(f"      结果: {len(user_2_str)} 条消息")
        
        # 测试：查询特定 user_id 的消息（整数）
        print("\n   测试3: 查询 user_id=2 的消息（整数类型）...")
        user_2_int = chat_manager.list_messages(user_id=2, limit=10)
        print(f"      结果: {len(user_2_int)} 条消息")
        
        # 比较结果
        if len(user_2_str) != len(user_2_int):
            print(f"   [WARN] 警告: 字符串和整数类型的 user_id 查询结果不一致！")
            print(f"      这可能是因为数据库中存储的类型与查询类型不匹配")
        
        # 测试：查询 NULL user_id 的消息
        print("\n   测试4: 查询 user_id=None 的消息...")
        null_messages = chat_manager.list_messages(user_id=None, limit=10)
        print(f"      结果: {len(null_messages)} 条消息")
        
    except Exception as e:
        print(f"   [ERROR] 测试查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 检查最近的保存日志
    print("\n[5] 检查最近的保存操作...")
    print("   [提示] 请查看后端日志，查找以下模式:")
    print("      - '✅ [DB] Chat message added: User=True, user_id=...'")
    print("      - '✅ [DB] Chat message added: User=False, user_id=...'")
    print("   [提示] 如果 user_id 为 None，说明保存时没有传递 user_id")
    
    # 6. 检查 API 端点
    print("\n[6] 检查 API 端点配置...")
    print("   [提示] 请确认:")
    print("      - /api/chat/history 端点是否正确使用 get_current_user")
    print("      - 前端调用时是否正确传递 Authorization header")
    print("      - session_state.user_id 是否正确设置")
    
    # 7. 生成诊断报告
    print("\n" + "=" * 80)
    print("[诊断建议]")
    print("=" * 80)
    print("""
1. 如果发现 user_id 为 NULL 的消息：
   - 检查 /api/chat 端点是否正确从 token 提取 user_id
   - 检查 session_state.user_id 是否正确设置
   - 检查 add_user_message/add_ai_response 是否接收到 user_id

2. 如果发现类型不匹配（字符串 vs 整数）：
   - 确保保存时统一使用字符串类型（str(user_id)）
   - 确保查询时也使用字符串类型

3. 如果查询结果为空：
   - 检查前端是否正确传递 Authorization header
   - 检查 get_current_user 是否正常工作
   - 检查数据库中的 user_id 是否与当前登录用户的 user_id 匹配

4. 需要添加的日志：
   - 在 /api/chat 端点记录: user_id 提取结果
   - 在 add_user_message/add_ai_response 记录: 接收到的 user_id
   - 在 /api/chat/history 端点记录: 查询使用的 user_id 和查询结果数量
    """)
    
    print("\n[完成] 诊断完成")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='诊断聊天历史记录跨设备同步问题')
    parser.add_argument(
        '--env', 
        '--environment',
        type=str,
        choices=['development', 'testing', 'production'],
        default=None,
        help='数据库环境 (development/testing/production)，默认从环境变量或配置读取'
    )
    
    args = parser.parse_args()
    diagnose_chat_history_sync(environment=args.env)
