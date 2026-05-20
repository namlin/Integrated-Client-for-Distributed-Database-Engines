from fastapi import APIRouter, Query
from typing import Optional
from services.wal_service import wal_service

router = APIRouter(prefix='/wal', tags=['wal'])


@router.get('', response_model=list)
def get_wal(
    tid: Optional[str] = Query(None),
    op: Optional[str] = Query(None),
    start_ts: Optional[str] = Query(None),
    end_ts: Optional[str] = Query(None),
):
    return wal_service.get_entries(tid=tid, operation=op, start_ts=start_ts, end_ts=end_ts)


@router.get('/entries/{tid}', response_model=list)
def get_wal_for_transaction(tid: str):
    return wal_service.get_entries(tid=tid)
