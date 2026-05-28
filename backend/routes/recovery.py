from fastapi import APIRouter, HTTPException, Request
from models.schemas import RecoveryRequest, SimulateFailureRequest
from services.recovery_service import recovery_service
from services.transaction_manager import transaction_manager
from services.db_manager import db_manager

router = APIRouter(prefix='/recovery', tags=['recovery'])


@router.post('/simulate-failure/{tid}', response_model=dict)
def simulate_failure(tid: str, request: Request):
    try:
        txn = transaction_manager.get_transaction(tid, request.state.client_id)
        if not txn:
            raise HTTPException(status_code=404, detail=f'Transaction {tid} not found')
        return recovery_service.simulate_failure(tid)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/run/{tid}', response_model=dict)
def run_recovery(tid: str, payload: RecoveryRequest, request: Request):
    try:
        txn = transaction_manager.get_transaction(tid, request.state.client_id)
        if not txn:
            raise HTTPException(status_code=404, detail=f'Transaction {tid} not found')

        adapter = None
        engine_id = txn.get('engine_id')
        if engine_id:
            adapter = db_manager.get_adapter(engine_id, request.state.client_id)

        return recovery_service.run_recovery(tid, payload.protocol, adapter)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/status/{tid}', response_model=dict)
def recovery_status(tid: str, request: Request):
    txn = transaction_manager.get_transaction(tid, request.state.client_id)
    if not txn:
        raise HTTPException(status_code=404, detail=f'Transaction {tid} not found')

    from database.init_wal_db import get_db_connection
    db = get_db_connection()
    row = db.execute(
        'SELECT * FROM recovery_snapshots WHERE tid=? ORDER BY id DESC LIMIT 1', (tid,)
    ).fetchone()
    db.close()
    if not row:
        return {'tid': tid, 'status': 'no_recovery_run'}
    return {
        'tid': tid,
        'protocol': row['protocol'],
        'before_state': row['before_state'],
        'after_state': row['after_state'],
        'timestamp': row['timestamp'],
    }
