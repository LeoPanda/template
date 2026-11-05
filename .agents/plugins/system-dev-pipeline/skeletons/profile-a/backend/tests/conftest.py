import os
import tempfile
import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from db.base import Base
from db.session import get_db
from core.main import app

@pytest.fixture(scope="session")
def test_db_path() -> Generator[str, None, None]:
    """UUID分離されたWAL一時実ファイルDBパスを生成し、セッション終了時に完全破棄する"""
    unique_id = uuid.uuid4().hex
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, f"test_app_{unique_id}.db")
    yield db_path
    # クリーンアップ (WAL/SHMファイル含む)
    for ext in ["", "-wal", "-shm"]:
        target = db_path + ext
        if os.path.exists(target):
            try:
                os.remove(target)
            except OSError:
                pass

@pytest.fixture(scope="session")
def db_engine(test_db_path: str):
    """WALモード・外部キー制約を強制した実ファイルSQLiteエンジン"""
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """トランザクション分離されたテスト用DBセッション"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """テスト用FastAPIクライアント"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
