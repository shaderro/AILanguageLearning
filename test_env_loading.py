#!/usr/bin/env python3
"""
测试环境变量加载
"""
import sys
from pathlib import Path

print("=" * 60)
print("环境变量加载测试")
print("=" * 60)

# 检查 python-dotenv
print("\n1. 检查 python-dotenv 安装状态...")
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv 已安装")
except ImportError:
    print("❌ python-dotenv 未安装")
    print("正在安装...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv"], 
                           capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ python-dotenv 安装成功")
        from dotenv import load_dotenv
    else:
        print(f"❌ 安装失败: {result.stderr}")
        sys.exit(1)

# 检查 .env 文件
print("\n2. 检查 .env 文件...")
env_path = Path('.env')
if env_path.exists():
    print(f"✅ .env 文件存在: {env_path.absolute()}")
else:
    print(f"❌ .env 文件不存在: {env_path.absolute()}")
    sys.exit(1)

# 加载 .env 文件
print("\n3. 加载 .env 文件...")
try:
    load_dotenv(env_path, override=True)
    print("✅ .env 文件加载成功")
except Exception as e:
    print(f"❌ 加载失败: {e}")
    sys.exit(1)

# 读取环境变量
print("\n4. 读取环境变量...")
import os

jwt_secret = os.getenv("JWT_SECRET")
openai_key = os.getenv("OPENAI_API_KEY")
env = os.getenv("ENV", "development")

print(f"JWT_SECRET: {'✅ 已设置 (' + jwt_secret[:30] + '...)' if jwt_secret else '❌ 未设置'}")
print(f"OPENAI_API_KEY: {'✅ 已设置 (' + openai_key[:30] + '...)' if openai_key else '❌ 未设置'}")
print(f"ENV: {env}")

# 检查 backend/config.py 的路径
print("\n5. 检查 backend/config.py 的路径计算...")
config_path = Path('backend/config.py')
if config_path.exists():
    print(f"✅ backend/config.py 存在")
    # 计算 .env 路径（按照 config.py 的逻辑）
    calculated_env_path = config_path.parent.parent / '.env'
    print(f"   计算的 .env 路径: {calculated_env_path.absolute()}")
    print(f"   路径存在: {calculated_env_path.exists()}")
else:
    print(f"❌ backend/config.py 不存在")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

