# 数据库配置文件
import os

# 优先使用环境变量中的 DATABASE_URL（云平台会自动注入）
DATABASE_URL_ENV = os.getenv('DATABASE_URL')

if DATABASE_URL_ENV:
    # 云平台环境：使用环境变量
    # 标准化连接字符串格式
    if DATABASE_URL_ENV.startswith('postgres://'):
        # 某些平台可能使用 postgres://，需要转换为 postgresql://
        DATABASE_URL_ENV = DATABASE_URL_ENV.replace('postgres://', 'postgresql://', 1)
    elif not DATABASE_URL_ENV.startswith('postgresql://') and not DATABASE_URL_ENV.startswith('postgresql+psycopg2://'):
        # 确保使用正确的协议前缀
        if DATABASE_URL_ENV.startswith('postgresql+'):
            pass  # 已经有协议前缀
        else:
            # 如果不是已知的协议，尝试添加 postgresql://
            pass  # 保持原样，让 SQLAlchemy 处理
    
    # 所有环境都使用同一个 PostgreSQL 数据库（云平台）
    DATABASE_CONFIG = {
        'development': DATABASE_URL_ENV,
        'testing': DATABASE_URL_ENV,
        'production': DATABASE_URL_ENV
    }
    print(f"[OK] 使用环境变量 DATABASE_URL（云平台 PostgreSQL）")
else:
    # 本地开发环境：使用 SQLite（向后兼容）
    DATABASE_CONFIG = {
        'development': 'sqlite:///database_system/data_storage/data/dev.db',
        'testing': 'sqlite:///database_system/data_storage/data/test.db',
        'production': 'sqlite:///database_system/data_storage/data/language_learning.db'
    }
    print(f"[OK] 使用本地 SQLite 数据库配置")

# 数据库文件路径（仅用于 SQLite，云平台不需要）
DB_FILES = {
    'dev': 'database_system/data_storage/data/dev.db',
    'test': 'database_system/data_storage/data/test.db',
    'prod': 'database_system/data_storage/data/language_learning.db'
} 