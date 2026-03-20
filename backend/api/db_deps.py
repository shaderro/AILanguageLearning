"""
单一 FastAPI 依赖：数据库 Session。

重要：各路由必须与 auth 使用「同一个 get_db_session 函数对象」，
FastAPI 才会在一次请求内复用同一个 Session，否则会打开两条连接
（get_current_user 一条 + 路由 handler 一条），容易在 Render 等小连接池上耗尽。
"""
from database_system.database_manager import get_database_manager


def get_db_session():
    try:
        from backend.config import ENV
        environment = ENV
    except ImportError:
        import os
        environment = os.getenv("ENV", "development")

    db_manager = get_database_manager(environment)
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
