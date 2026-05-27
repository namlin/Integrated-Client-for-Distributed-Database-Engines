from datetime import datetime, timezone
from platform import node
from typing import Dict, List, Optional

from database.init_wal_db import get_db_connection
from services.wal_service import wal_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TransactionManager:
    pending_operations = dict()

    def _generate_tid(self) -> str:
        db = get_db_connection()
        count = db.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        db.close()
        return f"TXN-{str(count + 1).zfill(4)}"

    def begin(self, engine_id: str, protocol: str) -> str:
        tid = self._generate_tid()
        db = get_db_connection()
        db.execute(
            'INSERT INTO transactions (tid,status,protocol,engine_id,start_ts) VALUES (?,?,?,?,?)',
            (tid, 'ACTIVE', protocol, engine_id, _now()),
        )
        db.commit()
        db.close()
        wal_service.log_begin(tid, protocol, engine_id)
        transaction_manager.pending_operations[tid] = []
        return tid

    def commit(self, tid: str):
        txn = self.get_transaction(tid)
        if not txn:
            raise ValueError(f"Transaction {tid} not found")
        wal_service.log_commit(tid, txn.get('engine_id', ''))
        if(txn.get('protocol', '') in ('No-Undo/No-Redo', 'No-Undo/Redo')):
            self.pending_operations.pop(tid)

    def rollback(self, tid: str):
        txn = self.get_transaction(tid)
        if not txn:
            raise ValueError(f"Transaction {tid} not found")
        wal_service.log_abort(tid, txn.get('engine_id', ''))
        
        if(txn.get('protocol', '') in ('No-Undo/No-Redo', 'No-Undo/Redo')):
            self.pending_operations.pop(tid)

    def mark_failed(self, tid: str):
        db = get_db_connection()
        db.execute("UPDATE transactions SET status='FAILED' WHERE tid=?", (tid,))
        db.commit()
        db.close()

    def get_transaction(self, tid: str) -> Optional[Dict]:
        db = get_db_connection()
        row = db.execute('SELECT * FROM transactions WHERE tid=?', (tid,)).fetchone()
        db.close()
        return dict(row) if row else None

    def get_all(self) -> List[Dict]:
        db = get_db_connection()
        rows = db.execute(
            'SELECT * FROM transactions ORDER BY start_ts DESC LIMIT 50'
        ).fetchall()
        db.close()
        result = []
        for row in rows:
            status = row['status']
            badge = ('green' if status == 'COMMITTED'
                     else 'orange' if status == 'ACTIVE'
                     else 'red' if status == 'FAILED'
                     else 'gray')
            result.append({
                'id': row['tid'],
                'status': status,
                'badge': badge,
                'protocol': row['protocol'],
                'engine_id': row['engine_id'],
                'start_ts': row['start_ts'],
                'end_ts': row['end_ts'],
            })
        return result

    def count_active(self) -> int:
        db = get_db_connection()
        n = db.execute(
            "SELECT COUNT(*) FROM transactions WHERE status='ACTIVE'"
        ).fetchone()[0]
        db.close()
        return n


transaction_manager = TransactionManager()
