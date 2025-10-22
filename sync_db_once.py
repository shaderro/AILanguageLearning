"""
一次性同步数据库表结构的临时脚本。

用法：
  python sync_db_once.py
"""

from database_system.business_logic.models import Base
from database_system.database_manager import DatabaseManager


def main() -> None:
    engine = DatabaseManager('development').get_engine()
    Base.metadata.create_all(engine)
    print("✅ DB schema synced")


if __name__ == "__main__":
    main()




