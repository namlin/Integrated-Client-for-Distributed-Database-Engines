from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class ConnectionCreate(BaseModel):
    name: str
    engine: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: str
    name: str
    engine: str
    status: str
    color: str
    address: str
    node: str


class QueryExecute(BaseModel):
    connectionId: str
    query: str
    protocol: Optional[str] = 'Undo/Redo'
    tid: Optional[str] = None


class QueryResult(BaseModel):
    results: List[Dict[str, Any]]
    columns: List[str]
    rowsAffected: int
    txn_id: Optional[str] = None
    timestamp: str
    message: Optional[str] = None


class TransactionBegin(BaseModel):
    connectionId: str
    protocol: str


class TransactionResponse(BaseModel):
    tid: str
    status: str
    protocol: str
    engine_id: str
    start_ts: str


class WALEntryResponse(BaseModel):
    id: Optional[int] = None
    tid: str
    op: str
    tabla: str
    before: str
    after: str
    timestamp: str
    engine_id: Optional[str] = None


class RecoveryRequest(BaseModel):
    protocol: str


class RecoveryResponse(BaseModel):
    tid: str
    protocol: str
    status: str
    recovery_actions: List[str]
    before_state: str
    after_state: str


class SimulateFailureRequest(BaseModel):
    tid: str
