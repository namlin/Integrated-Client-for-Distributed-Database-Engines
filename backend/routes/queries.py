from fastapi import APIRouter, HTTPException
from models.schemas import QueryExecute, QueryResult
from services.query_executor import query_executor

router = APIRouter(prefix='/queries', tags=['queries'])


@router.post('/execute', response_model=dict)
def execute_query(payload: QueryExecute):
    try:
        result = query_executor.execute(
            connection_id=payload.connectionId,
            query=payload.query,
            protocol=payload.protocol or 'Undo/Redo',
            tid=payload.tid,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
