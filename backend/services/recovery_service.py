import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from adapters.base_adapter import BaseAdapter
from database.init_wal_db import get_db_connection
from services.wal_service import wal_service
from services.transaction_manager import transaction_manager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sql_val(v) -> str:
    if v is None:
        return 'NULL'
    if isinstance(v, str):
        return f"'{v.replace(chr(39), chr(39)*2)}'"
    if isinstance(v, bool):
        return 'TRUE' if v else 'FALSE'
    return str(v)


def _load_json(s: str):
    if not s or s == '-':
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def _build_undo(entry: dict) -> Optional[str]:
    op = entry['op']
    table = entry['tabla']
    before = _load_json(entry['before'])
    after = _load_json(entry['after'])

    if op == 'INSERT' and after:
        pk_col, pk_val = list(after.items())[0]
        return f"DELETE FROM {table} WHERE {pk_col} = {_sql_val(pk_val)}"

    if op == 'UPDATE' and before:
        ref = after or before
        pk_col, pk_val = list(ref.items())[0]
        sets = [f"{k} = {_sql_val(v)}" for k, v in before.items() if k != pk_col]
        if sets:
            return f"UPDATE {table} SET {', '.join(sets)} WHERE {pk_col} = {_sql_val(pk_val)}"

    if op == 'DELETE' and before:
        cols = ', '.join(before.keys())
        vals = ', '.join(_sql_val(v) for v in before.values())
        return f"INSERT INTO {table} ({cols}) VALUES ({vals})"

    return None


def _build_redo(entry: dict) -> Optional[str]:
    orig = entry.get('original_query', '')
    if orig and orig not in ('-', 'BEGIN', 'COMMIT', 'ABORT', 'ROLLBACK'):
        return orig

    op = entry['op']
    table = entry['tabla']
    after = _load_json(entry['after'])
    before = _load_json(entry['before'])

    if op == 'INSERT' and after:
        cols = ', '.join(after.keys())
        vals = ', '.join(_sql_val(v) for v in after.values())
        return f"INSERT INTO {table} ({cols}) VALUES ({vals})"

    if op == 'UPDATE' and after:
        pk_col, pk_val = list(after.items())[0]
        sets = [f"{k} = {_sql_val(v)}" for k, v in after.items() if k != pk_col]
        if sets:
            return f"UPDATE {table} SET {', '.join(sets)} WHERE {pk_col} = {_sql_val(pk_val)}"

    if op == 'DELETE' and before:
        pk_col, pk_val = list(before.items())[0]
        return f"DELETE FROM {table} WHERE {pk_col} = {_sql_val(pk_val)}"

    return None


class RecoveryService:
    def simulate_failure(self, tid: str) -> dict:
        txn = transaction_manager.get_transaction(tid)
        if not txn:
            raise ValueError(f"Transaction {tid} not found")
        transaction_manager.mark_failed(tid)
        wal_service.log_abort(tid, txn.get('engine_id', ''))
        return {'tid': tid, 'status': 'FAILED',
                'message': f'Transaction {tid} marked as FAILED (crash simulated)'}

    def run_recovery(self, tid: str, protocol: str,
                     adapter: Optional[BaseAdapter] = None) -> dict:
        txn = transaction_manager.get_transaction(tid)
        if not txn:
            raise ValueError(f"Transaction {tid} not found")

        entries = wal_service.get_entries(tid=tid)
        writes = [e for e in entries if e['op'] in ('INSERT', 'UPDATE', 'DELETE')]

        committed = txn['status'] == 'COMMITTED'
        failed = txn['status'] in ('FAILED', 'ABORTED', 'ACTIVE')

        actions: List[str] = []
        before_state = (f"Transaction {tid}: status={txn['status']}, "
                        f"{len(writes)} write operation(s) in WAL")

        if protocol == 'No-Undo/No-Redo':
            if committed:
                actions.append(
                    '[No-Undo/No-Redo] Transaction committed — pages were forced to disk '
                    'at commit time. Nothing to redo.')
            else:
                actions.append(
                    '[No-Undo/No-Redo] Transaction did not commit — no-steal policy means '
                    'dirty pages never reached disk. Nothing to undo.')

        elif protocol == 'No-Undo/Redo':
            if committed:
                actions.append('[No-Undo/Redo] Transaction committed — applying REDO from WAL:')
                for e in writes:
                    sql = _build_redo(e)
                    if sql:
                        actions.append(f'  REDO ({e["op"]} on {e["tabla"]}): {sql}')
                        self._try_exec(adapter, sql, actions)
            else:
                actions.append(
                    '[No-Undo/Redo] Transaction did not commit — no-steal means dirty '
                    'pages never hit disk. No UNDO needed.')

        elif protocol == 'Undo/No-Redo':
            if failed:
                actions.append('[Undo/No-Redo] Transaction did not commit — applying UNDO from WAL (reverse order):')
                for e in reversed(writes):
                    sql = _build_undo(e)
                    if sql:
                        actions.append(f'  UNDO ({e["op"]} on {e["tabla"]}): {sql}')
                        self._try_exec(adapter, sql, actions)
            else:
                actions.append(
                    '[Undo/No-Redo] Transaction committed — force policy guarantees all '
                    'pages were on disk at commit. No REDO needed.')

        elif protocol == 'Undo/Redo':
            if failed:
                actions.append('[Undo/Redo] Transaction did not commit — applying UNDO (reverse order):')
                for e in reversed(writes):
                    sql = _build_undo(e)
                    if sql:
                        actions.append(f'  UNDO ({e["op"]} on {e["tabla"]}): {sql}')
                        self._try_exec(adapter, sql, actions)
            else:
                actions.append('[Undo/Redo] Transaction committed — applying REDO:')
                for e in writes:
                    sql = _build_redo(e)
                    if sql:
                        actions.append(f'  REDO ({e["op"]} on {e["tabla"]}): {sql}')
                        self._try_exec(adapter, sql, actions)

        if not actions:
            actions.append('No recovery actions required for this transaction state.')

        applied = sum(1 for a in actions if a.strip().startswith(('UNDO', 'REDO', '  UNDO', '  REDO')))
        after_state = f"Recovery complete. {applied} operation(s) applied."

        db = get_db_connection()
        db.execute(
            'INSERT INTO recovery_snapshots (tid,protocol,recovery_actions,before_state,after_state,timestamp)'
            ' VALUES (?,?,?,?,?,?)',
            (tid, protocol, json.dumps(actions), before_state, after_state, _now()),
        )
        db.commit()
        db.close()

        return {'tid': tid, 'protocol': protocol, 'status': 'completed',
                'recovery_actions': actions, 'before_state': before_state,
                'after_state': after_state}

    def _try_exec(self, adapter: Optional[BaseAdapter], sql: str, actions: List[str]):
        if adapter:
            ok = adapter.execute_recovery_sql(sql)
            actions.append(f'    → {"Applied" if ok else "Failed (check DB state)"}')


recovery_service = RecoveryService()
