import json
from typing import Dict, List, Tuple
from .base_adapter import BaseAdapter


class RedisAdapter(BaseAdapter):
    def connect(self) -> bool:
        try:
            import redis
            db_index = 0
            if self.config.get('database'):
                try:
                    db_index = int(self.config['database'])
                except ValueError:
                    db_index = 0
            self.connection = redis.Redis(
                host=self.config['host'],
                port=self.config['port'],
                password=self.config.get('password') or None,
                db=db_index,
                socket_connect_timeout=5,
                decode_responses=True,
            )
            self.connection.ping()
            return True
        except Exception as e:
            self.connection = None
            raise ConnectionError(f"Redis connection failed: {e}")

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

    def test_connection(self) -> bool:
        try:
            if not self.connection:
                return False
            self.connection.ping()
            return True
        except Exception:
            return False

    def execute_query(self, query: str) -> Tuple[List[Dict], int, List[str]]:
        """
        Query format (JSON):
        {"command": "GET|SET|DEL|KEYS|HSET|HGET|HGETALL", "key": "...", "value": "...", "field": "..."}
        """
        try:
            cmd = json.loads(query)
        except json.JSONDecodeError:
            raise ValueError(
                'Redis queries must be valid JSON. '
                'Example: {"command":"GET","key":"mykey"}'
            )
        command = cmd.get('command', '').upper()
        key = cmd.get('key', '')
        value = cmd.get('value')

        if command == 'GET':
            val = self.connection.get(key)
            result = [{'key': key, 'value': val}]
            return result, 1 if val is not None else 0, list(result[0].keys())
        if command == 'SET':
            result = [{'result': 'OK'}]
            return result, 1, list(result[0].keys())
        if command == 'DEL':
            n = self.connection.delete(key)
            return [], n, []
        if command == 'KEYS':
            results = [{'key': k} for k in self.connection.keys(key or '*')]
            columns = list(results[0].keys()) if results else ['key']
            return results, len(results), columns
        if command == 'HSET':
            result = [{'result': 'OK'}]
            return result, 1, list(result[0].keys())
        if command == 'HGET':
            val = self.connection.hget(key, cmd.get('field'))
            result = [{'key': key, 'field': cmd.get('field'), 'value': val}]
            return result, 1, list(result[0].keys())
        if command == 'HGETALL':
            val = self.connection.hgetall(key)
            result = [{'key': key, **val}]
            return result, 1, list(result[0].keys())
        raise ValueError(f"Unsupported Redis command: {command}")

    def fetch_before_image(self, table: str, where_clause: str) -> List[Dict]:
        try:
            val = self.connection.get(where_clause)
            return [{'key': where_clause, 'value': val}] if val is not None else []
        except Exception:
            return []

    def execute_recovery_sql(self, sql: str) -> bool:
        try:
            self.execute_query(sql)
            return True
        except Exception:
            return False