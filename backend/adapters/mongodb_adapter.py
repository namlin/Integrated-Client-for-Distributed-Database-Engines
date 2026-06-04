import json
from typing import Dict, List, Tuple, Optional
from .base_adapter import BaseAdapter

class MongoDBAdapter(BaseAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.session = None

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
        if hasattr(self, 'session') and self.session:
            try:
                self.session.end_session()
            except Exception:
                pass
            self.session = None
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

    def execute_query(self, query: str) -> Tuple[List[Dict], int, List[str]]:
        """
        Query format (JSON):
        {"collection": "name", "operation": "find|insertOne|updateOne|deleteOne|deleteMany",
         "filter": {}, "document": {}, "update": {}}
        
        For UPDATE/DELETE operations, returns metadata with '_before' key for WAL capture.
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

        session = self.session if (hasattr(self, 'session') and self.session) else None

        if op == 'find':
            docs = list(col.find(cmd.get('filter', {}), session=session))
            for d in docs:
                d['_id'] = str(d['_id'])
            columns = list(docs[0].keys()) if docs else []
            return docs, len(docs), columns
        
        if op == 'insertone':
            r = col.insert_one(cmd.get('document', {}), session=session)
            result = [{'inserted_id': str(r.inserted_id)}]
            return result, 1, list(result[0].keys())
        
        # Capturar before_image para updateone:
        if op == 'updateone':
            filter_doc = cmd.get('filter', {})
            update_doc = cmd.get('update', {})
            before_doc = col.find_one(filter_doc, session=session)
            r = col.update_one(filter_doc, update_doc, session=session)

            # Normalizar _id a string y retornar en metadata para el WAL:
            if before_doc and '_id' in before_doc:
                before_doc['_id'] = str(before_doc['_id'])
            result = [{'modified_count': r.modified_count, '_before': before_doc}] if before_doc else []

            columns = list(result[0].keys()) if result else []
            return result, r.modified_count, columns
        
        # Capturar before_image para deleteone:
        if op == 'deleteone':
            filter_doc = cmd.get('filter', {})
            before_doc = col.find_one(filter_doc, session=session)
            r = col.delete_one(filter_doc, session=session)

            # Normalizar _id a string y retornar en metadata para el WAL:
            if before_doc and '_id' in before_doc:
                before_doc['_id'] = str(before_doc['_id'])
            result = [{'deleted_count': r.deleted_count, '_before': before_doc}] if before_doc else []

            columns = list(result[0].keys()) if result else []
            return result, r.deleted_count, columns
        
        # Capturar before_image para deletemany:
        if op == 'deletemany':
            filter_doc = cmd.get('filter', {})
            before_docs = list(col.find(filter_doc, session=session))
            r = col.delete_many(filter_doc, session=session)

            # Normalizar _id a string en todos los docs:
            for doc in before_docs:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            result = [{'deleted_count': r.deleted_count, '_before': before_docs}] if before_docs else []

            columns = list(result[0].keys()) if result else []
            return result, r.deleted_count, columns
        
        raise ValueError(f"Unknown MongoDB operation: {op}")

    def fetch_before_image(self, table: str, where_clause: str) -> List[Dict]:
        try:
            col = self.connection[table]
            f = json.loads(where_clause) if where_clause else {}
            if '_id' in f and isinstance(f['_id'], str) and len(f['_id']) == 24:
                docs = list(col.find(f))
                if not docs:
                    from bson import ObjectId
                    try:
                        f_copy = dict(f)
                        f_copy['_id'] = ObjectId(f['_id'])
                        docs = list(col.find(f_copy))
                    except Exception:
                        pass
            else:
                docs = list(col.find(f))
            for d in docs:
                d['_id'] = str(d['_id'])
            return docs
        except Exception:
            return []

    def start_transaction(self) -> bool:
        if self.connection is not None and hasattr(self, 'client') and self.client:
            try:
                res = self.client.admin.command('isMaster')
                is_replica_set = 'setName' in res or res.get('msg') == 'isdbgrid'
                if not is_replica_set:
                    self.session = None
                    return False

                if self.session:
                    try:
                        self.session.end_session()
                    except Exception:
                        pass
                self.session = self.client.start_session()
                self.session.start_transaction()
                return True
            except Exception:
                self.session = None
                pass
        return False

    def commit_transaction(self) -> bool:
        if hasattr(self, 'session') and self.session:
            try:
                self.session.commit_transaction()
                return True
            except Exception:
                raise
            finally:
                self.session.end_session()
                self.session = None
        return False

    def rollback_transaction(self) -> bool:
        if hasattr(self, 'session') and self.session:
            try:
                self.session.abort_transaction()
                return True
            except Exception:
                raise
            finally:
                self.session.end_session()
                self.session = None
        return False

    def execute_recovery_sql(self, sql: str) -> bool:
        """Fallback para SQL. No debería usarse para Mongo recovery."""
        try:
            self.execute_query(sql)
            return True
        except Exception:
            return False

    def execute_mongo_recovery(self, operation: str, collection: str, 
                               filter_doc: Dict, document: Optional[Dict] = None, 
                               update_doc: Optional[Dict] = None) -> bool:
        """
        Ejecuta operaciones de recuperación en Mongo usando compensaciones.
        
        Args:
            operation: 'insertOne', 'updateOne', 'deleteOne'
            collection: nombre de la colección
            filter_doc: filtro para find/delete/update
            document: documento a insertar (para insertOne)
            update_doc: operador de update (para updateOne)
        
        Returns:
            bool: True si la operación fue exitosa
        """
        try:
            col = self.connection[collection]
            
            if operation == 'insertOne':
                if document:
                    col.insert_one(document)
                return True
            
            if operation == 'updateOne':
                if update_doc:
                    col.update_one(filter_doc, update_doc)
                return True
            
            if operation == 'deleteOne':
                col.delete_one(filter_doc)
                return True
            
            return False
        except Exception:
            return False