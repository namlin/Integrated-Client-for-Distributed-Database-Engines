import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from adapters.base_adapter import BaseAdapter
from services.db_manager import db_manager
from services.wal_service import wal_service
from services.transaction_manager import transaction_manager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_type(query: str) -> str:
    q = query.strip().upper()
    for kw in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'BEGIN', 'COMMIT', 'ROLLBACK',
               'CREATE', 'DROP', 'ALTER'):
        if q.startswith(kw):
            return kw
    return 'UNKNOWN'


def _extract_table(query: str) -> Optional[str]:
    patterns = [
        r'INSERT\s+INTO\s+(\w+)',
        r'UPDATE\s+(\w+)',
        r'DELETE\s+FROM\s+(\w+)',
        r'FROM\s+(\w+)',
    ]
    for p in patterns:
        m = re.search(p, query, re.IGNORECASE)
        if m:
            return m.group(1).lower()
    return None


def _extract_where(query: str) -> Optional[str]:
    m = re.search(r'\bWHERE\b\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|;|$)',
                  query, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def _sql_val(v) -> str:
    if v is None:
        return 'NULL'
    if isinstance(v, str):
        escaped = v.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(v, bool):
        return 'TRUE' if v else 'FALSE'
    return str(v)


def _build_undo(operation: str, table: str, before_str: str, after_str: str) -> Optional[str]:
    try:
        before = json.loads(before_str) if before_str and before_str != '-' else None
        after = json.loads(after_str) if after_str and after_str != '-' else None
    except Exception:
        return None

    if operation == 'INSERT' and after:
        pk_col, pk_val = list(after.items())[0]
        return f"DELETE FROM {table} WHERE {pk_col} = {_sql_val(pk_val)}"

    if operation == 'UPDATE' and before:
        ref = after or before
        pk_col, pk_val = list(ref.items())[0]
        sets = [f"{k} = {_sql_val(v)}" for k, v in before.items() if k != pk_col]
        if sets:
            return f"UPDATE {table} SET {', '.join(sets)} WHERE {pk_col} = {_sql_val(pk_val)}"

    if operation == 'DELETE' and before:
        cols = ', '.join(before.keys())
        vals = ', '.join(_sql_val(v) for v in before.values())
        return f"INSERT INTO {table} ({cols}) VALUES ({vals})"

    return None


class QueryExecutor:
    def execute(self, connection_id: str, query: str,
                protocol: str = 'Undo/Redo', tid: Optional[str] = None) -> Dict:
        adapter = db_manager.get_adapter(connection_id)
        if not adapter:
            raise ValueError(f"No active connection: {connection_id}")

        statements = [s.strip() for s in re.split(r';', query) if s.strip()
                      and not s.strip().startswith('--')]

        all_results: List[Dict] = []
        rows_affected = 0
        message_parts: List[str] = []
        current_tid = tid

        for stmt in statements:
            res = self._exec_stmt(adapter, connection_id, stmt, protocol, current_tid)
            all_results.extend(res.get('results', []))
            rows_affected += res.get('rowsAffected', 0)
            if res.get('tid'):
                current_tid = res['tid']
            if res.get('message'):
                message_parts.append(res['message'])

        return {
            'results': all_results,
            'columns': list(all_results[0].keys()) if all_results else [],
            'rowsAffected': rows_affected,
            'txn_id': current_tid,
            'timestamp': _now(),
            'message': ' | '.join(message_parts) if message_parts else None,
        }

    def _exec_stmt(self, adapter: BaseAdapter, connection_id: str,
                   query: str, protocol: str, tid: Optional[str]) -> Dict:
        qtype = _parse_type(query)

        if qtype == 'BEGIN':
            new_tid = transaction_manager.begin(connection_id, protocol)
            return {'results': [], 'rowsAffected': 0, 'tid': new_tid, 'message': f'Transaction {new_tid} started'}

        if qtype == 'COMMIT':
            if tid:
                transaction_manager.commit(tid)
            return {'results': [], 'rowsAffected': 0, 'message': f'Transaction {tid} committed'}

        if qtype == 'ROLLBACK':
            if tid:
                transaction_manager.rollback(tid)
                self._apply_undo(tid, adapter)
            return {'results': [], 'rowsAffected': 0, 'message': f'Transaction {tid} rolled back'}

        if qtype in ('INSERT', 'UPDATE', 'DELETE'):
            return self._exec_write(adapter, connection_id, query, qtype, tid)

        # SELECT and DDL
        rows, count = adapter.execute_query(query)
        return {'results': rows, 'rowsAffected': count}

    def _exec_write(self, adapter: BaseAdapter, connection_id: str,
                    query: str, qtype: str, tid: Optional[str]) -> Dict:
        table = _extract_table(query)
        where = _extract_where(query)

        # Capture before-image (WAL principle: log before applying change)
        before = None
        if qtype in ('UPDATE', 'DELETE') and table and where:
            try:
                rows = adapter.fetch_before_image(table, where)
                if rows:
                    before = rows[0] if len(rows) == 1 else rows
            except Exception:
                pass

        # Write WAL entry BEFORE executing
        entry_id = None
        if tid:
            entry_id = wal_service.log_operation(
                tid=tid, operation=qtype, table_name=table,
                before_image=before, engine_id=connection_id, original_query=query,
            )

        # Execute
        rows, affected = adapter.execute_query(query)

        # Capture after-image and update WAL
        after = None
        if rows:
            after = rows[0] if len(rows) == 1 else rows
        elif qtype == 'INSERT' and table:
            try:
                post = adapter.fetch_before_image(table, None)
                if post:
                    after = post[-1]
            except Exception:
                pass

        if tid and entry_id:
            wal_service.update_after_image(entry_id, after)

        return {'results': rows, 'rowsAffected': affected}

    def _apply_undo(self, tid: str, adapter: BaseAdapter):
        entries = wal_service.get_entries(tid=tid)
        for entry in reversed(entries):
            if entry['op'] in ('INSERT', 'UPDATE', 'DELETE'):
                sql = _build_undo(entry['op'], entry['tabla'], entry['before'], entry['after'])
                if sql:
                    try:
                        adapter.execute_recovery_sql(sql)
                    except Exception:
                        pass


query_executor = QueryExecutor()
