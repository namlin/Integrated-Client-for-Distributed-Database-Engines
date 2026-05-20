from fastapi import APIRouter, HTTPException
from models.schemas import ConnectionCreate, ConnectionResponse
from services.db_manager import db_manager

router = APIRouter(prefix='/connections', tags=['connections'])


@router.get('', response_model=list)
def list_connections():
    return db_manager.get_connections()


@router.post('', response_model=dict, status_code=201)
def create_connection(data: ConnectionCreate):
    try:
        return db_manager.register_connection(data.model_dump())
    except ConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/{conn_id}/disconnect', response_model=dict)
def disconnect(conn_id: str):
    try:
        return db_manager.disconnect_connection(conn_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/{conn_id}', response_model=dict)
def delete_connection(conn_id: str):
    try:
        return db_manager.delete_connection(conn_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{conn_id}/status', response_model=dict)
def connection_status(conn_id: str):
    connections = db_manager.get_connections()
    conn = next((c for c in connections if c['id'] == conn_id), None)
    if not conn:
        raise HTTPException(status_code=404, detail='Connection not found')
    return conn
