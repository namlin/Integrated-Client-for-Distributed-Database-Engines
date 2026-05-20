import json
from typing import Dict, List, Tuple
from .base_adapter import BaseAdapter


class MongoDBAdapter(BaseAdapter):
    def connect(self) -> bool:
        try:
            from pymongo import MongoClient
            uri = "mongodb://"
            if self.config.get('username') and self.config.get('password'):
                uri += f"{self.config['username']}:{self.config['password']}@"
            uri += f"{self.config['host']}:{self.config['port']}"
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            db_name = self.config.get('database') or 'test'
            self.connection = self.client[db_name]
            return True
        except Exception as e:
            self.connection = None
            raise ConnectionError(f"MongoDB connection failed: {e}")

    def disconnect(self):
        if hasattr(self, 'client') and self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self.connection = None

    def test_connection(self) -> bool:
        try:
            if not self.connection:
                return False
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

    def execute_query(self, query: str) -> Tuple[List[Dict], int]:
        """
        Query format (JSON):
        {"collection": "name", "operation": "find|insertOne|updateOne|deleteOne|deleteMany",
         "filter": {}, "document": {}, "update": {}}
        """
        try:
            cmd = json.loads(query)
        except json.JSONDecodeError:
            raise ValueError(
                'MongoDB queries must be valid JSON. '
                'Example: {"collection":"users","operation":"find","filter":{}}'
            )
        col_name = cmd.get('collection')
        op = cmd.get('operation', 'find').lower()
        col = self.connection[col_name]

        if op == 'find':
            docs = list(col.find(cmd.get('filter', {})))
            for d in docs:
                d['_id'] = str(d['_id'])
            return docs, len(docs)
        if op == 'insertone':
            r = col.insert_one(cmd.get('document', {}))
            return [{'inserted_id': str(r.inserted_id)}], 1
        if op == 'updateone':
            r = col.update_one(cmd.get('filter', {}), cmd.get('update', {}))
            return [], r.modified_count
        if op == 'deleteone':
            r = col.delete_one(cmd.get('filter', {}))
            return [], r.deleted_count
        if op == 'deletemany':
            r = col.delete_many(cmd.get('filter', {}))
            return [], r.deleted_count
        raise ValueError(f"Unknown MongoDB operation: {op}")

    def fetch_before_image(self, table: str, where_clause: str) -> List[Dict]:
        try:
            col = self.connection[table]
            f = json.loads(where_clause) if where_clause else {}
            docs = list(col.find(f))
            for d in docs:
                d['_id'] = str(d['_id'])
            return docs
        except Exception:
            return []

    def execute_recovery_sql(self, sql: str) -> bool:
        try:
            self.execute_query(sql)
            return True
        except Exception:
            return False
