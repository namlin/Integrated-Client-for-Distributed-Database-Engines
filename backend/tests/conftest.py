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

    def _parse_literal(token):
        value = token.strip()
        if value.upper() == 'NULL':
            return None
        if value.upper() == 'TRUE':
            return True
        if value.upper() == 'FALSE':
            return False
        if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
            return value[1:-1]
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def _split_csv(text):
        parts = []
        current = []
        in_quotes = False
        quote_char = ''
        for char in text:
            if char in ('"', "'"):
                if in_quotes and char == quote_char:
                    in_quotes = False
                    quote_char = ''
                elif not in_quotes:
                    in_quotes = True
                    quote_char = char
            if char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            parts.append(''.join(current).strip())
        return [part for part in parts if part]

    def _matches(row, where_clause):
        if not where_clause:
            return True
        for condition in [part.strip() for part in where_clause.split('AND')]:
            if not condition:
                continue
            if '=' not in condition:
                return False
            column, raw_value = [part.strip() for part in condition.split('=', 1)]
            if row.get(column) != _parse_literal(raw_value):
                return False
        return True

    class FakeAdapter(BaseAdapter):
        executed_queries = []
        tables = {
            'students': [{'id': 1, 'nombre': 'Mario', 'grade': 80}],
            'test_table': [{'id': 1, 'name': 'test', 'value': 10}],
        }

        def connect(self):
            self.connection = True
            return True
        def disconnect(self):
            self.connection = None
        def test_connection(self):
            return True
        def execute_query(self, query):
            self.executed_queries.append(query)
            normalized = query.strip().rstrip(';')
            upper = normalized.upper()

            if upper.startswith('SELECT'):
                import re
                match = re.search(r'FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$', normalized, re.IGNORECASE)
                if match:
                    table = match.group(1).lower()
                    where_clause = match.group(2)
                    rows = [dict(row) for row in self.tables.get(table, []) if _matches(row, where_clause)]
                    columns = list(rows[0].keys()) if rows else []
                    return rows, len(rows), columns
                default_row = {'id': 1, 'name': 'test'}
                return [default_row], 1, list(default_row.keys())

            if upper.startswith('UPDATE'):
                import re
                match = re.match(r'^UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$', normalized, re.IGNORECASE)
                if match:
                    table, set_clause, where_clause = match.groups()
                    table = table.lower()
                    updates = {}
                    for assignment in _split_csv(set_clause):
                        if '=' not in assignment:
                            continue
                        column, raw_value = [part.strip() for part in assignment.split('=', 1)]
                        updates[column] = _parse_literal(raw_value)
                    affected = 0
                    for row in self.tables.get(table, []):
                        if _matches(row, where_clause):
                            row.update(updates)
                            affected += 1
                    return [], affected, []
                return [], 0, []

            if upper.startswith('DELETE'):
                import re
                match = re.match(r'^DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$', normalized, re.IGNORECASE)
                if match:
                    table, where_clause = match.groups()
                    table = table.lower()
                    remaining = []
                    affected = 0
                    for row in self.tables.get(table, []):
                        if _matches(row, where_clause):
                            affected += 1
                        else:
                            remaining.append(row)
                    self.tables[table] = remaining
                    return [], affected, []
                return [], 0, []

            if upper.startswith('INSERT'):
                import re
                match = re.match(r'^INSERT\s+INTO\s+(\w+)\s*\((.+?)\)\s*VALUES\s*\((.+?)\)$', normalized, re.IGNORECASE)
                if match:
                    table, columns_text, values_text = match.groups()
                    table = table.lower()
                    columns = [column.strip() for column in columns_text.split(',') if column.strip()]
                    values = [_parse_literal(value) for value in _split_csv(values_text)]
                    row = dict(zip(columns, values))
                    self.tables.setdefault(table, []).append(row)
                    return [], 1, []
                return [], 0, []

            return [], 0, []

        def fetch_before_image(self, table, where):
            rows = [dict(row) for row in self.tables.get(table, []) if _matches(row, where)]
            return rows
        def execute_recovery_sql(self, sql):
            self.execute_query(sql)
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
    FakeAdapter.executed_queries = []
    FakeAdapter.tables = {
        'students': [{'id': 1, 'nombre': 'Mario', 'grade': 80}],
        'test_table': [{'id': 1, 'name': 'test', 'value': 10}],
    }
    return FakeAdapter
