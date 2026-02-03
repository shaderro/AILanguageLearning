from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .data_storage.config.config import DATABASE_CONFIG, DB_FILES
import os

class DatabaseManager:
    def __init__(self, environment: str = 'development'):
        if environment not in DATABASE_CONFIG:
            raise ValueError(f"Unknown environment: {environment}")
        self.environment = environment
        self.database_url = DATABASE_CONFIG[environment]
        self._engine = None
        self._Session = None

    def get_engine(self):
        if self._engine is None:
            # 检查是否是 PostgreSQL（云平台）
            is_postgres = (self.database_url.startswith('postgresql://') or 
                          self.database_url.startswith('postgresql+psycopg2://') or
                          self.database_url.startswith('postgres://'))
            
            if is_postgres:
                # PostgreSQL 配置（云平台）
                # 使用连接池优化性能
                self._engine = create_engine(
                    self.database_url,
                    echo=False,
                    future=True,
                    pool_size=5,  # 连接池大小
                    max_overflow=10,  # 最大溢出连接
                    pool_pre_ping=True,  # 连接前检查（重要：避免连接超时）
                    pool_recycle=3600,  # 1小时后回收连接
                    connect_args={
                        "connect_timeout": 10,  # 连接超时 10 秒
                        "options": "-c statement_timeout=25000ms"  # 查询超时 25 秒（略小于前端 30 秒超时）
                    },
                    execution_options={
                        "timeout": 25  # SQLAlchemy 查询超时 25 秒
                    }
                )
                print(f"[OK] 创建 PostgreSQL 数据库引擎（环境: {self.environment}，查询超时: 25秒）")
            else:
                # SQLite 配置（本地开发）
                db_path = DB_FILES.get(
                    'dev' if self.environment == 'development' else (
                        'test' if self.environment == 'testing' else 'prod'
                    ),
                    None
                )
                if db_path:
                    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                    print(f"[OK] 创建 SQLite 数据库引擎（环境: {self.environment}, 路径: {db_path}）")
                else:
                    print(f"[OK] 创建 SQLite 数据库引擎（环境: {self.environment}）")
                self._engine = create_engine(
                    self.database_url,
                    echo=False,
                    future=True
                )
        return self._engine

    def get_session(self):
        if self._Session is None:
            engine = self.get_engine()
            self._Session = sessionmaker(
                bind=engine,
                autoflush=False,
                autocommit=False,
                future=True
            )
        return self._Session()


def get_database_manager(environment: str = 'development') -> DatabaseManager:
    return DatabaseManager(environment) 