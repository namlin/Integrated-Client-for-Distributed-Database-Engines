import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope='session', autouse=True)
def use_temp_wal_db():
    """Point the WAL DB at a temporary file for the entire test session."""
    import database.init_wal_db as db_module
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        tmp_path = f.name
    db_module.WAL_DB_PATH = tmp_path
    db_module.init_db()
    yield tmp_path
    os.unlink(tmp_path)


TEST_CLIENT_ID = 'test-session-001'


@pytest.fixture(scope='session')
def client(use_temp_wal_db):
    from app import app
    with TestClient(app, headers={'X-Client-Session-Id': TEST_CLIENT_ID}) as c:
        yield c


@pytest.fixture
def mock_pg_adapter(monkeypatch):
    """A fake PostgreSQL adapter that succeeds without a real DB."""
    from adapters.base_adapter import BaseAdapter

    class FakeAdapter(BaseAdapter):
        def connect(self):
            self.connection = True
            return True
        def disconnect(self):
            self.connection = None
        def test_connection(self):
            return True
        def execute_query(self, query):
            return [{'id': 1, 'name': 'test'}], 1
        def fetch_before_image(self, table, where):
            return [{'id': 1, 'name': 'old_value'}]
        def execute_recovery_sql(self, sql):
            return True

    from adapters import postgresql_adapter
    monkeypatch.setattr(postgresql_adapter, 'PostgreSQLAdapter', FakeAdapter)
    from services import db_manager as dm_mod
    monkeypatch.setattr(dm_mod, 'ADAPTER_MAP', {
        'PostgreSQL': FakeAdapter,
        'MongoDB': FakeAdapter,
        'MySQL': FakeAdapter,
        'Redis': FakeAdapter,
    })
    return FakeAdapter
