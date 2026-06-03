from typing import Dict, List, Tuple
from .base_adapter import BaseAdapter


class PostgreSQLAdapter(BaseAdapter):
    def connect(self) -> bool:
        import psycopg2
        import psycopg2.extras
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config.get('username'),
                password=self.config.get('password'),
                dbname=self.config.get('database'),
                connect_timeout=5,
            )
            self.connection.autocommit = True
            return True
        except Exception as e:
            self.connection = None
            raise ConnectionError(f"PostgreSQL connection failed: {e}")

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def test_connection(self) -> bool:
        try:
            if not self.connection or self.connection.closed:
                return False
            cur = self.connection.cursor()
            cur.execute("SELECT 1")
            return True
        except Exception:
            return False

    def execute_query(self, query: str) -> Tuple[List[Dict], int, List[str]]:
        import psycopg2.extras
        cur = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            if cur.description:
                rows = [dict(r) for r in cur.fetchall()]
                return rows, len(rows), columns
            return [], cur.rowcount if cur.rowcount >= 0 else 0, columns
        except Exception:
            raise

    def fetch_before_image(self, table: str, where_clause: str) -> List[Dict]:
        import psycopg2.extras
        try:
            cur = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            sql = f"SELECT * FROM {table}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]
        except Exception:
            return []

    def execute_recovery_sql(self, sql: str) -> bool:
        try:
            cur = self.connection.cursor()
            cur.execute(sql)
            return True
        except Exception:
            return False