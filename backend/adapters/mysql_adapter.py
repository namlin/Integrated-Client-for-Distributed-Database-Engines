from typing import Dict, List, Tuple
from .base_adapter import BaseAdapter


class MySQLAdapter(BaseAdapter):
    def connect(self) -> bool:
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config.get('username'),
                password=self.config.get('password'),
                database=self.config.get('database'),
                connection_timeout=5,
                autocommit=True,
            )
            return True
        except Exception as e:
            self.connection = None
            raise ConnectionError(f"MySQL connection failed: {e}")

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def test_connection(self) -> bool:
        try:
            if not self.connection or not self.connection.is_connected():
                return False
            self.connection.ping(reconnect=False)
            return True
        except Exception:
            return False

    def execute_query(self, query: str) -> Tuple[List[Dict], int, List[str]]:
        cur = self.connection.cursor(dictionary=True)
        try:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            if cur.description:
                rows = cur.fetchall()
                return rows, len(rows), columns
            return [], cur.rowcount if cur.rowcount >= 0 else 0, columns
        except Exception:
            raise

    def fetch_before_image(self, table: str, where_clause: str) -> List[Dict]:
        try:
            cur = self.connection.cursor(dictionary=True)
            sql = f"SELECT * FROM {table}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            cur.execute(sql)
            return cur.fetchall()
        except Exception:
            return []

    def execute_recovery_sql(self, sql: str) -> bool:
        try:
            cur = self.connection.cursor()
            cur.execute(sql)
            return True
        except Exception:
            return False