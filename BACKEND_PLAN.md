# Backend Development Plan - DB Client Project

## Discovery Findings
- Frontend: React + Vite with global context (DBClientContext)
- Manages: Multiple DB engines (PostgreSQL, MongoDB, MySQL, Redis), transactions, recovery protocols, query execution
- Key operations: execute queries, manage transactions (BEGIN/COMMIT/ROLLBACK), view WAL entries
- Recovery protocols: 4 types (No-Undo/No-Redo, No-Undo/Redo, Undo/No-Redo, Undo/Redo)
- Decisions: Connect to existing DB instances, fully functional protocols, SQLite for WAL storage

## Alignment Decisions
1. **Scope**: Connect to existing DB instances (no Docker Compose orchestration)
2. **Recovery Protocols**: Fully functional with real undo/redo logic
3. **WAL Storage**: SQLite database for persistence and easy querying

---

# Implementation Plan for Claude Code

## Plan: Python Backend for Distributed DB Client

**TL;DR:** Build a Python FastAPI backend with multi-engine DB connectors, transaction management, Write-Ahead Log (WAL) using SQLite, and four recovery protocols. Structure: FastAPI + SQLAlchemy + per-engine adapters + WAL manager.

---

## Steps

### Phase 1: Project Structure & Foundation
1. Create Python backend folder structure:
   ```
   backend/
   ├── app.py (FastAPI main app)
   ├── requirements.txt
   ├── config.py (DB connection configs)
   ├── .env.example
   ├── models/
   │   ├── __init__.py
   │   ├── schemas.py (Pydantic models for API)
   │   ├── wal_model.py (WAL database model)
   │   └── recovery_models.py (Protocol state models)
   ├── services/
   │   ├── __init__.py
   │   ├── db_manager.py (Multi-engine DB coordinator)
   │   ├── query_executor.py (Query parsing & execution)
   │   ├── transaction_manager.py (Transaction state machine)
   │   ├── wal_service.py (Write-Ahead Log manager)
   │   └── recovery_service.py (4 recovery protocols)
   ├── adapters/
   │   ├── __init__.py
   │   ├── postgresql_adapter.py
   │   ├── mongodb_adapter.py
   │   ├── mysql_adapter.py
   │   ├── redis_adapter.py
   │   └── base_adapter.py (Abstract base)
   ├── routes/
   │   ├── __init__.py
   │   ├── connections.py (GET, POST connections)
   │   ├── queries.py (Execute, GET results)
   │   ├── transactions.py (BEGIN, COMMIT, ROLLBACK)
   │   ├── wal.py (Query WAL, filter by TID/time)
   │   ├── recovery.py (Run recovery, simulate failures)
   │   └── health.py (Connection status)
   ├── utils/
   │   ├── __init__.py
   │   ├── logger.py
   │   └── errors.py (Custom exceptions)
   └── database/
       ├── wal.db (SQLite - created on first run)
       └── init_wal_db.py (Schema initialization)
   ```

2. Set up FastAPI app with CORS (for React frontend)
3. Initialize SQLite for WAL storage with schema: `transactions`, `wal_entries`, `recovery_states`

### Phase 2: Multi-Engine Connection Layer (*parallel with Phase 3*)
4. Create base adapter class with interface: `connect()`, `disconnect()`, `execute_query()`, `get_schema()`
5. Implement DB-specific adapters:
   - **PostgreSQL adapter**: psycopg2 + parameterized queries
   - **MongoDB adapter**: pymongo + document mapping to results
   - **MySQL adapter**: mysql-connector-python
   - **Redis adapter**: redis-py (key-value operations)
6. Create DB Manager service that:
   - Maintains connection pool per engine
   - Routes queries to correct engine based on context
   - Handles connection failures gracefully (return error status)
   - Exposes: `get_connection(engine_name)`, `list_connections()`, `test_connection(engine_name)`

### Phase 3: Transaction & WAL Management (*parallel with Phase 2*)
7. Build Transaction Manager that tracks:
   - Transaction ID (auto-generated: TXN-NNNN)
   - Status (ACTIVE, COMMITTED, ABORTED, ROLLING_BACK, RECOVERING)
   - Active transaction per session/user
   - Associated recovery protocol
   - Timestamps (BEGIN, END, ABORT time)

8. Implement WAL Service:
   - **Log format per entry**: `tid`, `operation` (BEGIN/INSERT/UPDATE/DELETE/COMMIT/ABORT), `table`, `before_image` (JSON), `after_image` (JSON), `timestamp`, `db_engine`
   - **Write path**: All write operations logged BEFORE execution (Write-Ahead)
   - **Persistence**: SQLite (3 tables):
     - `wal_entries` (tid, op, table, before, after, ts, engine, protocol_type)
     - `transactions` (tid, status, protocol, start_ts, end_ts)
     - `recovery_snapshots` (tid, protocol, state_before_recovery, state_after_recovery)
   - **Read API**: `get_wal(tid=None, start_ts=None, end_ts=None, operation=None)` → filtered results

### Phase 4: Recovery Protocol Implementation
9. Implement **RecoveryService** with 4 protocols as separate classes:
   - **NoUndoNoRedo**: On crash, ignore uncommitted txns, keep committed ones
   - **NoUndoRedo**: Redo all committed changes from WAL, ignore uncommitted
   - **UndoNoRedo**: Undo all uncommitted changes before crash, ignore committed
   - **UndoRedo**: Undo uncommitted + Redo committed changes
   
   Each protocol exposes: `recover(tx_id, wal_entries) → recovery_actions`

10. Implement recovery logic:
    - Parse WAL entries for target transaction
    - Generate undo/redo SQL commands based on before/after images
    - Execute recovery actions in order
    - Update recovery_snapshots table with before/after state

### Phase 5: API Endpoints
11. **Connections** (`/api/connections/`):
    - `GET /`: List all registered connections with status
    - `POST /`: Add new connection (engine, host, port, credentials)
    - `GET /{engine_name}/status`: Check if connected
    - `DELETE /{engine_name}`: Close connection

12. **Transactions** (`/api/transactions/`):
    - `POST /begin`: Start transaction, return TID + set recovery protocol
    - `POST /{tid}/commit`: Commit transaction (flush to DB)
    - `POST /{tid}/rollback`: Rollback transaction (undo WAL entries)
    - `GET /active`: Get currently active transaction

13. **Queries** (`/api/queries/`):
    - `POST /execute`: Execute query on active engine
      - Input: `{sql, engine, tid, type: "SELECT|INSERT|UPDATE|DELETE"}`
      - Output: `{results, rowsAffected, txn_id, timestamp}`
    - `GET /results/{query_id}`: Retrieve cached results
    - `GET /schema/{engine}`: Get table schemas

14. **WAL** (`/api/wal/`):
    - `GET /`: All entries with optional filters
    - `GET /filter`: `?tid=TXN-0043&op=UPDATE&start_ts=...&end_ts=...`
    - `GET /{tid}`: All entries for transaction
    - `DELETE /{tid}`: Clear entries (admin only)

15. **Recovery** (`/api/recovery/`):
    - `POST /simulate-failure`: Set transaction to FAILED state
    - `POST /run/{tid}`: Execute recovery for transaction + protocol
      - Input: `{protocol: "No-Undo/Redo", tid}`
      - Output: `{status, recovery_actions, before_state, after_state}`
    - `GET /status/{tid}`: Check recovery progress

16. **Health** (`/api/health/`):
    - `GET /`: System status (all connections, active transactions)

### Phase 6: Testing & Documentation
17. Create `.env.example` with connection templates (PostgreSQL, MongoDB, etc.)
18. Create backend README with:
    - Installation steps
    - Environment setup
    - How to run (`python app.py` or `uvicorn app:app --reload`)
    - API documentation (Swagger will auto-generate at `/docs`)
    - Example cURL/requests for each endpoint

---

## Relevant Files
- [Specifications](especificaciones.md) — Reference requirements RF-01 through RF-08
- [Frontend Context](client/src/contexts/DBClientContext.jsx) — See state shape: `activeEngine`, `activeTransaction`, `recoveryProtocol`, `queryContent`, `walEntries`, `resultsData`
- [Frontend Buttons](client/src/components/EditorPanel.jsx) — See "Ejecutar", "COMMIT", "ROLLBACK" actions

---

## Verification

1. **Phase 1**: `python -m pytest tests/test_project_structure.py` (imports work, config loads)
2. **Phase 2**: Connect to each DB engine (PostgreSQL, MongoDB) and run test queries
3. **Phase 3**: Log a transaction with 3 operations to WAL, verify SQLite entries
4. **Phase 4**: Trigger all 4 recovery protocols on same transaction, verify undo/redo actions differ
5. **Phase 5**: Use Swagger UI at `http://localhost:8000/docs` to test all endpoints
6. **End-to-end**: Execute transaction with recovery protocol, trigger failure, run recovery, verify data consistency

---

## Decisions
- **Python + FastAPI**: Async support, auto-generated API docs, modern framework
- **SQLAlchemy**: ORM for SQLite WAL, easier schema management
- **Environment variables (.env)**: Secure credential storage for DB connections
- **Per-engine adapters**: Abstraction layer enables easy addition of new engines
- **SQLite WAL DB**: Self-contained (no extra services), easy filtering/export
- **Recovery as post-processing**: Doesn't require real DB crashes, simulated via transaction state

---

## Further Considerations
1. **Error handling strategy**: Should failed queries roll back automatically or require explicit ROLLBACK? → Recommend: explicit (user controls transaction semantics)
2. **Query validation**: Should backend parse/validate SQL or pass through? → Recommend: Pass through to respect DB-specific syntax
3. **Concurrent transactions**: Should API support multiple active txns per session or one at a time? → Recommend: One active per session (simplifies state management, matches frontend UX)
