import threading
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
        # client_id -> conn_id -> adapter
        self._adapters: Dict[str, Dict[str, BaseAdapter]] = {}
        # reverse map: conn_id -> client_id (kept even after disconnect for filtering)
        self._conn_to_client: Dict[str, str] = {}
        self._lock = threading.Lock()

    def _make_id(self, name: str) -> str:
        slug = name.lower().replace(' ', '-')
        return f"{slug}-{uuid.uuid4().hex[:8]}"

    def _client_conn_ids(self, client_id: str) -> set:
        with self._lock:
            return {cid for cid, owner in self._conn_to_client.items() if owner == client_id}

    def register_connection(self, data: dict, client_id: str) -> dict:
        engine = data['engine']
        if engine not in ADAPTER_MAP:
            raise ValueError(f"Unsupported engine: {engine}")

        conn_id = self._make_id(data['name'])
        adapter = ADAPTER_MAP[engine](data)
        adapter.connect()

        with self._lock:
            self._adapters.setdefault(client_id, {})[conn_id] = adapter
            self._conn_to_client[conn_id] = client_id
            total = len(self._conn_to_client)

        node = f"nodo-{total}"
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

    def disconnect_connection(self, conn_id: str, client_id: str) -> dict:
        db = get_db_connection()
        row = db.execute('SELECT * FROM connections WHERE id=?', (conn_id,)).fetchone()
        if not row:
            db.close()
            raise ValueError(f"Connection {conn_id} not found")

        with self._lock:
            client_adapters = self._adapters.get(client_id, {})
            if conn_id in client_adapters:
                client_adapters[conn_id].disconnect()
                del client_adapters[conn_id]
            # keep in _conn_to_client so the SQLite row remains visible to this client

        db.execute("UPDATE connections SET status='desconectado' WHERE id=?", (conn_id,))
        db.commit()
        db.close()

        return {'id': conn_id, 'name': row['name'], 'engine': row['engine'],
                'status': 'desconectado', 'color': 'gray',
                'address': f"{row['host']}:{row['port']}", 'node': row['node'] or ''}

    def reconnect_connection(self, conn_id: str, client_id: str) -> dict:
        db = get_db_connection()
        row = db.execute('SELECT * FROM connections WHERE id=?', (conn_id,)).fetchone()
        if not row:
            db.close()
            raise ValueError(f"Connection {conn_id} not found")

        engine = row['engine']
        if engine not in ADAPTER_MAP:
            db.close()
            raise ValueError(f"Unsupported engine: {engine}")

        # Build connection config from database row
        config = {
            'engine': engine,
            'host': row['host'],
            'port': row['port'],
            'username': row['username'],
            'password': row['password'],
            'database': row['database_name'],
            'name': row['name'],
        }

        # Create and test new adapter
        adapter = ADAPTER_MAP[engine](config)
        adapter.connect()

        with self._lock:
            self._adapters.setdefault(client_id, {})[conn_id] = adapter

        db.execute("UPDATE connections SET status='connected' WHERE id=?", (conn_id,))
        db.commit()
        db.close()

        return {'id': conn_id, 'name': row['name'], 'engine': engine,
                'status': 'connected', 'color': 'green',
                'address': f"{row['host']}:{row['port']}", 'node': row['node'] or ''}

    def delete_connection(self, conn_id: str, client_id: str) -> dict:
        with self._lock:
            client_adapters = self._adapters.get(client_id, {})
            if conn_id in client_adapters:
                client_adapters[conn_id].disconnect()
                del client_adapters[conn_id]
            self._conn_to_client.pop(conn_id, None)

        db = get_db_connection()
        db.execute('DELETE FROM connections WHERE id=?', (conn_id,))
        db.commit()
        db.close()
        return {'message': f'Connection {conn_id} deleted'}

    def get_connections(self, client_id: str) -> List[dict]:
        client_ids = self._client_conn_ids(client_id)

        db = get_db_connection()
        rows = db.execute('SELECT * FROM connections').fetchall()
        db.close()

        result = []
        for row in rows:
            if row['id'] not in client_ids:
                continue
            with self._lock:
                active = (row['id'] in self._adapters.get(client_id, {})
                          and self._adapters[client_id][row['id']].test_connection())
            status = 'connected' if active else row['status']
            color = STATUS_COLOR.get(status, 'gray')
            result.append({'id': row['id'], 'name': row['name'], 'engine': row['engine'],
                           'status': status, 'color': color,
                           'address': f"{row['host']}:{row['port']}",
                           'node': row['node'] or ''})
        return result

    def get_adapter(self, conn_id: str, client_id: str) -> Optional[BaseAdapter]:
        with self._lock:
            return self._adapters.get(client_id, {}).get(conn_id)

    def find_connection_id_by_name(self, name: str, client_id: str) -> Optional[str]:
        client_ids = self._client_conn_ids(client_id)
        if not client_ids:
            return None
        placeholders = ','.join('?' * len(client_ids))
        db = get_db_connection()
        row = db.execute(
            f'SELECT id FROM connections WHERE (name=? OR engine=?) AND id IN ({placeholders})',
            (name, name) + tuple(client_ids),
        ).fetchone()
        db.close()
        return row['id'] if row else None


db_manager = DBManager()
