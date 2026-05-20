import uuid
from typing import Dict, List, Optional

from adapters.base_adapter import BaseAdapter
from adapters.postgresql_adapter import PostgreSQLAdapter
from adapters.mongodb_adapter import MongoDBAdapter
from adapters.mysql_adapter import MySQLAdapter
from adapters.redis_adapter import RedisAdapter
from database.init_wal_db import get_db_connection

ADAPTER_MAP = {
    'PostgreSQL': PostgreSQLAdapter,
    'MongoDB': MongoDBAdapter,
    'MySQL': MySQLAdapter,
    'Redis': RedisAdapter,
}

STATUS_COLOR = {
    'connected': 'green',
    'desconectado': 'gray',
    'error': 'red',
    'disconnected': 'gray',
}


class DBManager:
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}

    def _make_id(self, name: str) -> str:
        slug = name.lower().replace(' ', '-')
        return f"{slug}-{uuid.uuid4().hex[:8]}"

    def register_connection(self, data: dict) -> dict:
        engine = data['engine']
        if engine not in ADAPTER_MAP:
            raise ValueError(f"Unsupported engine: {engine}")

        conn_id = self._make_id(data['name'])
        adapter = ADAPTER_MAP[engine](data)
        adapter.connect()
        self._adapters[conn_id] = adapter

        node = f"nodo-{len(self._adapters)}"
        address = f"{data['host']}:{data['port']}"

        db = get_db_connection()
        db.execute(
            '''INSERT INTO connections
               (id, name, engine, host, port, username, password, database_name, status, node)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (conn_id, data['name'], engine, data['host'], data['port'],
             data.get('username'), data.get('password'), data.get('database'),
             'connected', node),
        )
        db.commit()
        db.close()

        return {'id': conn_id, 'name': data['name'], 'engine': engine,
                'status': 'connected', 'color': 'green', 'address': address, 'node': node}

    def disconnect_connection(self, conn_id: str) -> dict:
        db = get_db_connection()
        row = db.execute('SELECT * FROM connections WHERE id=?', (conn_id,)).fetchone()
        if not row:
            db.close()
            raise ValueError(f"Connection {conn_id} not found")

        if conn_id in self._adapters:
            self._adapters[conn_id].disconnect()
            del self._adapters[conn_id]

        db.execute("UPDATE connections SET status='desconectado' WHERE id=?", (conn_id,))
        db.commit()
        db.close()

        return {'id': conn_id, 'name': row['name'], 'engine': row['engine'],
                'status': 'desconectado', 'color': 'gray',
                'address': f"{row['host']}:{row['port']}", 'node': row['node'] or ''}

    def delete_connection(self, conn_id: str) -> dict:
        if conn_id in self._adapters:
            self._adapters[conn_id].disconnect()
            del self._adapters[conn_id]

        db = get_db_connection()
        db.execute('DELETE FROM connections WHERE id=?', (conn_id,))
        db.commit()
        db.close()
        return {'message': f'Connection {conn_id} deleted'}

    def get_connections(self) -> List[dict]:
        db = get_db_connection()
        rows = db.execute('SELECT * FROM connections').fetchall()
        db.close()
        result = []
        for row in rows:
            active = (row['id'] in self._adapters
                      and self._adapters[row['id']].test_connection())
            status = 'connected' if active else row['status']
            color = STATUS_COLOR.get(status, 'gray')
            result.append({'id': row['id'], 'name': row['name'], 'engine': row['engine'],
                           'status': status, 'color': color,
                           'address': f"{row['host']}:{row['port']}",
                           'node': row['node'] or ''})
        return result

    def get_adapter(self, conn_id: str) -> Optional[BaseAdapter]:
        return self._adapters.get(conn_id)

    def find_connection_id_by_name(self, name: str) -> Optional[str]:
        db = get_db_connection()
        row = db.execute(
            'SELECT id FROM connections WHERE name=? OR engine=?', (name, name)
        ).fetchone()
        db.close()
        return row['id'] if row else None


db_manager = DBManager()
