"""
统一的环境变量配置模块

⚠️ 重要：所有敏感信息必须通过环境变量管理，不要硬编码在代码中！

使用方法：
1. 创建 .env 文件（不要提交到版本控制）
2. 在 .env 文件中设置所需的环境变量
3. 在代码中从本模块导入配置值
"""
import os
from pathlib import Path

# 尝试加载 .env 文件（如果安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    # 从项目根目录查找 .env 文件
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] 已加载环境变量文件: {env_path}")
    else:
        print(f"[WARN] 未找到 .env 文件: {env_path}")
except ImportError:
    print("[WARN] python-dotenv 未安装，将直接从系统环境变量读取")
    pass

# ==================== 必需的环境变量 ====================

# JWT 密钥（用于生成和验证 JWT token）
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    import warnings
    warnings.warn("⚠️ JWT_SECRET 环境变量未设置！生产环境必须设置此变量。")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    import warnings
    warnings.warn("⚠️ OPENAI_API_KEY 环境变量未设置！")

# 数据库环境（development/testing/production）
ENV = os.getenv("ENV", "development")
if ENV not in ["development", "testing", "production"]:
    raise ValueError(f"ENV 必须是 development/testing/production 之一，当前值: {ENV}")

# 数据库 URL（可选，如果设置了则覆盖配置文件中的值）
DATABASE_URL = os.getenv("DATABASE_URL")  # 如果未设置，将使用配置文件中的默认值

# ==================== 可选的环境变量 ====================

# 其他配置可以在这里添加
# DEBUG = os.getenv("DEBUG", "false").lower() == "true"

