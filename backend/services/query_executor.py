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
    try:
        cmd = json.loads(query)
        op = cmd.get('operation', '').upper()
        if op == 'FIND':
            return 'SELECT'
        elif op == 'INSERTONE':
            return 'INSERT'
        elif op == 'UPDATEONE':
            return 'UPDATE'
        elif op in ('DELETEONE', 'DELETEMANY'):
            return 'DELETE'
    except Exception:
        pass
    return 'UNKNOWN'


def _extract_table(query: str) -> Optional[str]:
    try:
        cmd = json.loads(query)
        if 'collection' in cmd:
            return cmd['collection'].lower()
    except Exception:
        pass

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
    try:
        cmd = json.loads(query)
        if 'filter' in cmd:
            return json.dumps(cmd['filter'])
    except Exception:
        pass

    m = re.search(r'\bWHERE\b\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|;|$)',
                  query, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def _parse_literal(value: str):
    token = value.strip()
    if token.upper() == 'NULL':
        return None
    if token.upper() == 'TRUE':
        return True
    if token.upper() == 'FALSE':
        return False
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return token[1:-1]
    try:
        if '.' in token:
            return float(token)
        return int(token)
    except ValueError:
        return token


def _split_csv(text: str) -> List[str]:
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


def _row_matches_where(row: Dict, where_clause: Optional[str]) -> bool:
    if not where_clause:
        return True
    conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
    for condition in conditions:
        match = re.match(r'^(\w+)\s*=\s*(.+)$', condition.strip())
        if not match:
            return False
        column, raw_value = match.groups()
        expected = _parse_literal(raw_value)
        if row.get(column) != expected:
            return False
    return True


def _parse_update_assignments(query: str) -> tuple[Optional[str], Dict[str, object]]:
    match = re.match(r'^UPDATE\s+\w+\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$', query, re.IGNORECASE | re.DOTALL)
    if not match:
        return None, {}
    set_clause, where_clause = match.groups()
    assignments: Dict[str, object] = {}
    for part in _split_csv(set_clause):
        assignment = re.match(r'^(\w+)\s*=\s*(.+)$', part.strip())
        if assignment:
            column, raw_value = assignment.groups()
            assignments[column] = _parse_literal(raw_value)
    return where_clause.strip() if where_clause else None, assignments


def _parse_insert_row(query: str) -> Optional[Dict[str, object]]:
    match = re.match(
        r'^INSERT\s+INTO\s+\w+\s*\((.+?)\)\s*VALUES\s*\((.+?)\)$',
        query,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    columns_text, values_text = match.groups()
    columns = [column.strip() for column in columns_text.split(',') if column.strip()]
    values = [_parse_literal(value) for value in _split_csv(values_text)]
    if len(columns) != len(values):
        return None
    return dict(zip(columns, values))


def _apply_query_to_rows(rows: List[Dict], query: str, qtype: str) -> List[Dict]:
    if qtype == 'UPDATE':
        where_clause, assignments = _parse_update_assignments(query)
        updated_rows = []
        for row in rows:
            next_row = dict(row)
            if _row_matches_where(next_row, where_clause):
                next_row.update(assignments)
            updated_rows.append(next_row)
        return updated_rows

    if qtype == 'DELETE':
        where_clause = _extract_where(query)
        return [dict(row) for row in rows if not _row_matches_where(row, where_clause)]

    if qtype == 'INSERT':
        new_row = _parse_insert_row(query)
        if new_row:
            return [dict(row) for row in rows] + [new_row]

    return [dict(row) for row in rows]


def _project_pending_rows(rows: List[Dict], query: str, tid: Optional[str], protocol: str) -> List[Dict]:
    # DEPRECATED: No longer used. SELECT queries always read from disk, not from pending operations.
    # This function is kept for reference but is no longer called.
    if not tid or protocol not in ('No-Undo/No-Redo', 'No-Undo/Redo'):
        return rows

    table = _extract_table(query)
    if not table:
        return rows

    projected = [dict(row) for row in rows]
    for operation in transaction_manager.pending_operations.get(tid, []):
        if operation.get('table') != table:
            continue
        operation_query = operation.get('query', '')
        operation_type = operation.get('qtype') or _parse_type(operation_query)
        projected = _apply_query_to_rows(projected, operation_query, operation_type)
    return projected


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
                protocol: str = 'Undo/Redo', tid: Optional[str] = None,
                client_id: str = '') -> Dict:
        adapter = db_manager.get_adapter(connection_id, client_id)
        if not adapter:
            raise ValueError(f"No active connection: {connection_id}")

        statements = [s.strip() for s in re.split(r';', query) if s.strip()
                      and not s.strip().startswith('--')]

        all_results: List[Dict] = []
        all_columns: List[str] = []
        rows_affected = 0
        message_parts: List[str] = []
        current_tid = tid
        final_tid_override = None

        for stmt in statements:
            qtype = _parse_type(stmt)
            # For write operations without explicit TID, create independent transactions
            # Don't carry over auto-started TID to next statement
            stmt_tid = current_tid if current_tid else None
            
            res = self._exec_stmt(adapter, connection_id, stmt, protocol, stmt_tid, client_id)
            all_results.extend(res.get('results', []))
            rows_affected += res.get('rowsAffected', 0)
            # Capture columns from the statement response
            stmt_columns = res.get('columns', [])
            if stmt_columns:
                all_columns = stmt_columns
            
            # Track any auto-started or explicitly started transaction ID to return to client
            res_tid = res.get('tid')
            if res_tid:
                if current_tid or qtype == 'BEGIN':
                    current_tid = res_tid
                else:
                    final_tid_override = res_tid
            if res.get('message'):
                message_parts.append(res['message'])

        return {
            'results': all_results,
            'columns': all_columns,
            'rowsAffected': rows_affected,
            'txn_id': current_tid if current_tid else final_tid_override,
            'auto_started': current_tid is None and final_tid_override is not None,
            'timestamp': _now(),
            'message': ' | '.join(message_parts) if message_parts else None,
        }

    def _exec_stmt(self, adapter: BaseAdapter, connection_id: str,
                   query: str, protocol: str, tid: Optional[str],
                   client_id: str = '') -> Dict:
        qtype = _parse_type(query)

        if qtype == 'BEGIN':
            new_tid = transaction_manager.begin(connection_id, protocol, client_id)
            try:
                adapter.start_transaction()
            except Exception:
                pass
            return {'results': [], 'rowsAffected': 0, 'tid': new_tid, 'message': f'Transaction {new_tid} started'}

        if qtype == 'COMMIT':
            if tid:
                transaction_manager.commit(tid, client_id)
                try:
                    adapter.commit_transaction()
                except Exception:
                    pass
            return {'results': [], 'rowsAffected': 0, 'message': f'Transaction {tid} committed'}

        if qtype == 'ROLLBACK':
            if tid:
                transaction_manager.rollback(tid, client_id)
                try:
                    adapter.rollback_transaction()
                except Exception:
                    pass
                self._apply_undo(tid, adapter)
            return {'results': [], 'rowsAffected': 0, 'message': f'Transaction {tid} rolled back'}

        if qtype == 'SELECT':
            # SELECT queries disk, then projects pending operations for this transaction (read your own writes)
            rows, count, columns = adapter.execute_query(query)
            rows = _project_pending_rows(rows, query, tid, protocol)
            return {'results': rows, 'rowsAffected': len(rows) if rows else count, 'columns': columns}

        if qtype in ('INSERT', 'UPDATE', 'DELETE'):
            return self._exec_write(adapter, connection_id, query, qtype, tid, protocol, client_id)

        # SELECT and DDL:
        rows, count, columns = adapter.execute_query(query)
        message = None
        if qtype in ('CREATE', 'DROP', 'ALTER'):
            message = f"Query executed successfully: {qtype} command completed"
        return {'results': rows, 'rowsAffected': count, 'columns': columns, 'message': message}

    def _exec_write(self, adapter: BaseAdapter, connection_id: str,
                    query: str, qtype: str, tid: Optional[str], protocol: str,
                    client_id: str = '') -> Dict:
        table = _extract_table(query)
        where = _extract_where(query)

        # Auto-start a transaction when a write runs without an explicit TID:
        auto_started = False
        if not tid:
            try:
                tid = transaction_manager.begin(connection_id, protocol, client_id)
                auto_started = True
                try:
                    adapter.start_transaction()
                except Exception:
                    pass
            except Exception:
                tid = None

        # Capture before-image:
        before = None
        engine_type = adapter.__class__.__name__  # 'MongoDBAdapter', 'PostgreSQLAdapter', etc.

        if qtype in ('UPDATE', 'DELETE') and table and where and engine_type != 'MongoDBAdapter':
            try:
                rows = adapter.fetch_before_image(table, where)
                if rows:
                    before = rows[0] if len(rows) == 1 else rows
            except Exception:
                pass

        # Check if this transaction uses No-Steal policy (No-Undo protocols)
        is_no_steal = protocol in ('No-Undo/No-Redo', 'No-Undo/Redo')
        after = None

        if is_no_steal:
            # NO-STEAL: Buffer the operation, don't execute immediately:
            if tid not in transaction_manager.pending_operations:
                transaction_manager.pending_operations[tid] = []
            transaction_manager.pending_operations[tid].append({
                'adapter': adapter,
                'query': query,
                'qtype': qtype,
                'table': table,
            })
            rows = []
            affected = 0

            # Compute before & after-image for MongoDB No-Steal
            if engine_type == 'MongoDBAdapter':
                try:
                    cmd = json.loads(query)
                    if qtype == 'INSERT':
                        after = cmd.get('document', {})
                    elif qtype == 'UPDATE':
                        before_docs = adapter.fetch_before_image(table, where)
                        if before_docs:
                            before = before_docs[0] if len(before_docs) == 1 else before_docs
                            update_op = cmd.get('update', {})
                            doc = dict(before) if isinstance(before, dict) else dict(before[0]) if before else {}
                            if '$set' in update_op:
                                doc.update(update_op['$set'])
                            after = doc
                    elif qtype == 'DELETE':
                        before_docs = adapter.fetch_before_image(table, where)
                        if before_docs:
                            before = before_docs[0] if len(before_docs) == 1 else before_docs
                except Exception:
                    pass
            else:
                # Compute after-image from the parsed SQL query
                if qtype == 'INSERT':
                    parsed = _parse_insert_row(query)
                    if parsed:
                        after = parsed
                elif qtype == 'UPDATE' and before:
                    _, assignments = _parse_update_assignments(query)
                    if assignments:
                        merged = dict(before) if isinstance(before, dict) else dict(before[0]) if before else {}
                        merged.update(assignments)
                        after = merged
                elif qtype == 'DELETE':
                    after = None
        else:
            # STEAL: Execute immediately (Undo/* protocols):
            rows, affected, _ = adapter.execute_query(query)

            if engine_type == 'MongoDBAdapter' and qtype in ('UPDATE', 'DELETE'):
                if rows and isinstance(rows[0], dict) and '_before' in rows[0]:
                    before_raw = rows[0].pop('_before')
                    if before_raw:
                        before = before_raw if isinstance(before_raw, list) else [before_raw]

            # Capturar after-image:
            if rows:
                after = rows[0] if len(rows) == 1 else rows

            if engine_type == 'MongoDBAdapter':
                if qtype == 'UPDATE' and table and where:
                    try:
                        updated_docs = adapter.fetch_before_image(table, where)
                        if updated_docs:
                            after = updated_docs[0] if len(updated_docs) == 1 else updated_docs
                    except Exception:
                        pass
                elif qtype == 'INSERT' and table and rows:
                    inserted_id = rows[0].get('inserted_id')
                    if inserted_id:
                        try:
                            docs = adapter.fetch_before_image(table, json.dumps({'_id': inserted_id}))
                            if docs:
                                after = docs[0]
                        except Exception:
                            pass
            else:
                if qtype == 'INSERT' and table:
                    try:
                        post = adapter.fetch_before_image(table, None)
                        if post:
                            after = post[-1]
                    except Exception:
                        pass

        # Log to WAL (single entry per operation):
        entry_id = None
        if tid:
            entry_id = wal_service.log_operation(
                tid=tid, operation=qtype, table_name=table,
                before_image=before, engine_id=connection_id, original_query=query,
            )
            if entry_id and after:
                wal_service.update_after_image(entry_id, after)

        result = {'results': rows, 'rowsAffected': affected}

        if tid:
            result['tid'] = tid
            if auto_started:
                result['message'] = f'Transaction {tid} auto-started'
                result['auto_started'] = True
            if is_no_steal:
                result['message'] = f'Operation buffered (No-Steal policy). Will execute on COMMIT.'
        return result

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
