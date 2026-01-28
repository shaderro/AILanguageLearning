#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查后端代码中 token 不足判断逻辑
用于排查为什么余额小于0还能使用AI功能
"""

import sys
import os

def check_backend_logic():
    """检查后端代码中的 token 不足判断逻辑"""
    print("=" * 80)
    print("检查后端代码中的 token 不足判断逻辑")
    print("=" * 80)
    
    # 检查 main.py 中的逻辑
    main_py_path = "frontend/my-web-ui/backend/main.py"
    if os.path.exists(main_py_path):
        print(f"\n📄 检查 {main_py_path}:")
        print("-" * 80)
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 查找 token 不足检查的代码
            if 'token_balance' in content and 'role' in content:
                # 查找相关代码段
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'token_balance' in line and ('<' in line or '>' in line):
                        # 显示上下文
                        start = max(0, i - 3)
                        end = min(len(lines), i + 4)
                        print(f"\n   行 {i+1} 附近:")
                        for j in range(start, end):
                            marker = ">>> " if j == i else "    "
                            print(f"   {marker}{j+1:4d}: {lines[j]}")
            else:
                print("   ⚠️  未找到 token_balance 和 role 相关的检查逻辑")
    else:
        print(f"   ❌ 文件不存在: {main_py_path}")
    
    # 检查 token_service.py
    token_service_path = "backend/services/token_service.py"
    if os.path.exists(token_service_path):
        print(f"\n📄 检查 {token_service_path}:")
        print("-" * 80)
        with open(token_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'record_token_usage' in content:
                print("   ✅ 找到 record_token_usage 函数")
            else:
                print("   ⚠️  未找到 record_token_usage 函数")
    
    # 检查前端 tokenUtils.js
    token_utils_path = "frontend/my-web-ui/src/utils/tokenUtils.js"
    if os.path.exists(token_utils_path):
        print(f"\n📄 检查 {token_utils_path}:")
        print("-" * 80)
        with open(token_utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'isTokenInsufficient' in content:
                print("   ✅ 找到 isTokenInsufficient 函数")
                # 显示函数内容
                lines = content.split('\n')
                in_function = False
                for i, line in enumerate(lines):
                    if 'isTokenInsufficient' in line and '=' in line:
                        in_function = True
                        print(f"\n   函数定义（行 {i+1} 开始）:")
                    if in_function:
                        print(f"   {i+1:4d}: {line}")
                        if line.strip() == '};' and in_function:
                            break
            else:
                print("   ⚠️  未找到 isTokenInsufficient 函数")
    
    print("\n" + "=" * 80)
    print("💡 建议检查项：")
    print("=" * 80)
    print("1. 检查后端 main.py 中 /api/chat 端点的 token 不足判断")
    print("2. 检查用户 role 字段是否为 NULL（NULL 应该被视为 'user'）")
    print("3. 检查 token_balance 字段是否为 NULL（NULL 应该被视为 0）")
    print("4. 检查判断逻辑：if user.role != 'admin' and (user.token_balance is None or user.token_balance < 1000)")
    print("5. 检查是否有其他地方绕过了这个检查")
    print("=" * 80)

if __name__ == "__main__":
    check_backend_logic()
