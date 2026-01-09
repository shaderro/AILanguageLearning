#!/usr/bin/env python3
"""
检查环境变量配置状态
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from backend.config import JWT_SECRET, OPENAI_API_KEY, ENV
    
    print("=" * 50)
    print("环境变量配置状态")
    print("=" * 50)
    
    # 检查 JWT_SECRET
    if JWT_SECRET and JWT_SECRET != "your-secret-key-change-in-production":
        print(f"✅ JWT_SECRET: 已设置 ({JWT_SECRET[:20]}...)")
    else:
        print("⚠️  JWT_SECRET: 未设置（使用默认值，不安全）")
        print("   建议：在 .env 文件中设置 JWT_SECRET")
    
    # 检查 OPENAI_API_KEY
    if OPENAI_API_KEY and OPENAI_API_KEY != "sk-your-api-key-here":
        print(f"✅ OPENAI_API_KEY: 已设置 ({OPENAI_API_KEY[:20]}...)")
    else:
        print("⚠️  OPENAI_API_KEY: 未设置（AI 功能不可用）")
        print("   建议：在 .env 文件中设置 OPENAI_API_KEY（如果需要 AI 功能）")
    
    # 检查 ENV
    print(f"✅ ENV: {ENV}")
    
    print("=" * 50)
    
    # 检查 .env 文件是否存在
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print(f"✅ .env 文件存在: {env_file}")
    else:
        print(f"❌ .env 文件不存在: {env_file}")
        print("   请创建 .env 文件并配置环境变量")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("   请确保已安装 python-dotenv: pip install python-dotenv")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

