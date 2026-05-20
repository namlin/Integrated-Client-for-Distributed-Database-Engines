from fastapi import APIRouter, HTTPException
from models.schemas import TransactionBegin, TransactionResponse
from services.transaction_manager import transaction_manager

router = APIRouter(prefix='/transactions', tags=['transactions'])


@router.post('/begin', response_model=dict)
def begin_transaction(payload: TransactionBegin):
    try:
        tid = transaction_manager.begin(payload.connectionId, payload.protocol)
        txn = transaction_manager.get_transaction(tid)
        return txn
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('', response_model=list)
def list_transactions():
    return transaction_manager.get_all()


@router.get('/{tid}', response_model=dict)
def get_transaction(tid: str):
    txn = transaction_manager.get_transaction(tid)
    if not txn:
        raise HTTPException(status_code=404, detail=f'Transaction {tid} not found')
    return txn


@router.put('/{tid}/commit', response_model=dict)
def commit(tid: str):
    try:
        transaction_manager.commit(tid)
        return {'tid': tid, 'status': 'COMMITTED', 'message': f'Transaction {tid} committed'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/{tid}/rollback', response_model=dict)
def rollback(tid: str):
    try:
        transaction_manager.rollback(tid)
        return {'tid': tid, 'status': 'ABORTED', 'message': f'Transaction {tid} rolled back'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
