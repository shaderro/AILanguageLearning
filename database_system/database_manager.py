from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .data_storage.config.config import DATABASE_CONFIG, DB_FILES

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
            db_path = DB_FILES['dev' if self.environment == 'development' else (
                'test' if self.environment == 'testing' else 'prod'
            )]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self._engine = create_engine(self.database_url, echo=False, future=True)
        return self._engine

    def get_session(self):
        if self._Session is None:
            engine = self.get_engine()
            self._Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        return self._Session()


def get_database_manager(environment: str = 'development') -> DatabaseManager:
    return DatabaseManager(environment) 