from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 5.0,  # busy_timeout=5000ms: ロック解放待機
    },
    pool_pre_ping=True,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # 1. WAL (Write-Ahead Logging) モード有効化 (読み書き並行性向上)
    cursor.execute("PRAGMA journal_mode=WAL;")
    # 2. 外部キー制約の強制有効化
    cursor.execute("PRAGMA foreign_keys=ON;")
    # 3. 同期レベルの最適化 (NORMAL)
    cursor.execute("PRAGMA synchronous=NORMAL;")
    # 4. busy_timeout の再設定 (5000ms)
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
