import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from database.init_wal_db import get_db_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WALService:
    def log_begin(self, tid: str, protocol: str, engine_id: str):
        db = get_db_connection()
        db.execute(
            'INSERT INTO wal_entries (tid,operation,table_name,before_image,after_image,timestamp,engine_id,original_query)'
            " VALUES (?,'BEGIN','-','-','-',?,?,'BEGIN')",
            (tid, _now(), engine_id),
        )
        db.commit()
        db.close()

    def log_operation(self, tid: str, operation: str, table_name: str,
                      before_image, engine_id: str, original_query: str) -> int:
        before_str = json.dumps(before_image) if before_image else '-'
        db = get_db_connection()
        cur = db.execute(
            'INSERT INTO wal_entries (tid,operation,table_name,before_image,after_image,timestamp,engine_id,original_query)'
            ' VALUES (?,?,?,?,?,?,?,?)',
            (tid, operation, table_name or '-', before_str, '-', _now(), engine_id, original_query),
        )
        entry_id = cur.lastrowid
        db.commit()
        db.close()
        return entry_id

    def update_after_image(self, entry_id: int, after_image):
        after_str = json.dumps(after_image) if after_image else '-'
        db = get_db_connection()
        db.execute('UPDATE wal_entries SET after_image=? WHERE id=?', (after_str, entry_id))
        db.commit()
        db.close()

    def log_commit(self, tid: str, engine_id: str):
        db = get_db_connection()
        db.execute(
            'INSERT INTO wal_entries (tid,operation,table_name,before_image,after_image,timestamp,engine_id,original_query)'
            " VALUES (?,'COMMIT','-','-','-',?,?,'COMMIT')",
            (tid, _now(), engine_id),
        )
        db.execute(
            "UPDATE transactions SET status='COMMITTED', end_ts=? WHERE tid=?",
            (_now(), tid),
        )
        db.commit()
        db.close()

    def log_abort(self, tid: str, engine_id: str):
        db = get_db_connection()
        db.execute(
            'INSERT INTO wal_entries (tid,operation,table_name,before_image,after_image,timestamp,engine_id,original_query)'
            " VALUES (?,'ABORT','-','-','-',?,?,'ABORT')",
            (tid, _now(), engine_id),
        )
        db.execute(
            "UPDATE transactions SET status='ABORTED', end_ts=? WHERE tid=?",
            (_now(), tid),
        )
        db.commit()
        db.close()

    def get_entries(self, tid: Optional[str] = None, operation: Optional[str] = None,
                    start_ts: Optional[str] = None, end_ts: Optional[str] = None,
                    client_id: Optional[str] = None) -> List[Dict]:
        if client_id is not None:
            sql = ('SELECT w.* FROM wal_entries w '
                   'JOIN transactions t ON w.tid = t.tid '
                   'WHERE t.client_id=?')
            params: list = [client_id]
        else:
            sql = 'SELECT * FROM wal_entries WHERE 1=1'
            params = []

        if tid:
            sql += ' AND w.tid=?' if client_id is not None else ' AND tid=?'
            params.append(tid)
        if operation:
            sql += ' AND w.operation=?' if client_id is not None else ' AND operation=?'
            params.append(operation)
        if start_ts:
            sql += ' AND w.timestamp>=?' if client_id is not None else ' AND timestamp>=?'
            params.append(start_ts)
        if end_ts:
            sql += ' AND w.timestamp<=?' if client_id is not None else ' AND timestamp<=?'
            params.append(end_ts)
        sql += ' ORDER BY w.id ASC' if client_id is not None else ' ORDER BY id ASC'

        db = get_db_connection()
        rows = db.execute(sql, params).fetchall()
        db.close()
        return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, row) -> Dict:
        return {
            'id': row['id'],
            'tid': row['tid'],
            'op': row['operation'],
            'tabla': row['table_name'],
            'before': row['before_image'],
            'after': row['after_image'],
            'timestamp': row['timestamp'],
            'engine_id': row['engine_id'],
            'original_query': row['original_query'],
        }

    def count_entries(self) -> int:
        db = get_db_connection()
        n = db.execute('SELECT COUNT(*) FROM wal_entries').fetchone()[0]
        db.close()
        return n


wal_service = WALService()