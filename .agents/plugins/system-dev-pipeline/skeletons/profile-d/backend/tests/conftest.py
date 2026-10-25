import tempfile
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from core.main import app
from core.config import settings
from db.session import Base, get_db


@pytest.fixture(scope="function")
def temp_db():
    """
    Profile D (PAT-TEST-001) 結合テスト用の一時実ファイルDB動的プロビジョニング。
    インメモリDBではなくUUID付き実ファイルを作成し、WAL並行性および外部キー制約を本番同等に検証後、アトミック破棄する。
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        db_file = Path(temp_dir) / f"test_{uuid.uuid4().hex[:8]}.db"
        test_db_url = f"sqlite:///{db_file}"

        test_engine = create_engine(
            test_db_url,
            connect_args={"timeout": 5.0, "check_same_thread": False},
        )

        @event.listens_for(test_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        yield TestSessionLocal

        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


@pytest.fixture
def client(temp_db):
    """
    一時実ファイルDBが注入されたテスト用クライアント。
    (X-App-Session-Token ヘッダーを自動付与)
    """
    c = TestClient(app)
    c.headers.update({"X-App-Session-Token": settings.APP_SESSION_TOKEN})
    return c
