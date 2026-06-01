from fastapi import APIRouter, HTTPException, Request
from models.schemas import TransactionBegin, TransactionResponse
from services.db_manager import db_manager
from services.query_executor import query_executor
from services.transaction_manager import transaction_manager

router = APIRouter(prefix='/transactions', tags=['transactions'])


@router.post('/begin', response_model=dict)
def begin_transaction(payload: TransactionBegin, request: Request):
    try:
        tid = transaction_manager.begin(payload.connectionId, payload.protocol, request.state.client_id)
        txn = transaction_manager.get_transaction(tid)
        return txn
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('', response_model=list)
def list_transactions(request: Request):
    return transaction_manager.get_all(request.state.client_id)


@router.get('/{tid}', response_model=dict)
def get_transaction(tid: str, request: Request):
    txn = transaction_manager.get_transaction(tid, request.state.client_id)
    if not txn:
        raise HTTPException(status_code=404, detail=f'Transaction {tid} not found')
    return txn


@router.put('/{tid}/commit', response_model=dict)
def commit(tid: str, request: Request):
    try:
        transaction_manager.commit(tid, request.state.client_id)
        return {'tid': tid, 'status': 'COMMITTED', 'message': f'Transaction {tid} committed'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/{tid}/rollback', response_model=dict)
def rollback(tid: str, request: Request):
    try:
        txn = transaction_manager.get_transaction(tid, request.state.client_id)
        if not txn:
            raise HTTPException(status_code=404, detail=f'Transaction {tid} not found')
        transaction_manager.rollback(tid, request.state.client_id)
        if txn.get('protocol', '') in ('Undo/No-Redo', 'Undo/Redo'):
            adapter = db_manager.get_adapter(txn.get('engine_id', ''), request.state.client_id)
            if adapter:
                query_executor._apply_undo(tid, adapter)
        return {'tid': tid, 'status': 'ABORTED', 'message': f'Transaction {tid} rolled back'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
