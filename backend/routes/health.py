from fastapi import APIRouter, Request
from services.db_manager import db_manager
from services.wal_service import wal_service
from services.transaction_manager import transaction_manager

router = APIRouter(prefix='/health', tags=['health'])


@router.get('', response_model=dict)
def health(request: Request):
    connections = db_manager.get_connections(request.state.client_id)
    return {
        'status': 'ok',
        'connections': len(connections),
        'active_connections': sum(1 for c in connections if c['status'] == 'connected'),
        'wal_entries': wal_service.count_entries(),
        'active_transactions': transaction_manager.count_active(),
    }
