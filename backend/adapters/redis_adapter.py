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

    def execute_query(self, query: str) -> Tuple[List[Dict], int]:
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
            return [{'key': key, 'value': val}], 1 if val is not None else 0
        if command == 'SET':
            self.connection.set(key, value)
            return [{'result': 'OK'}], 1
        if command == 'DEL':
            n = self.connection.delete(key)
            return [], n
        if command == 'KEYS':
            keys = self.connection.keys(key or '*')
            return [{'key': k} for k in keys], len(keys)
        if command == 'HSET':
            self.connection.hset(key, cmd.get('field'), value)
            return [{'result': 'OK'}], 1
        if command == 'HGET':
            val = self.connection.hget(key, cmd.get('field'))
            return [{'key': key, 'field': cmd.get('field'), 'value': val}], 1
        if command == 'HGETALL':
            val = self.connection.hgetall(key)
            return [{'key': key, **val}], 1
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
