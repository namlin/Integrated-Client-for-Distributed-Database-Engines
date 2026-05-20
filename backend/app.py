from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.init_wal_db import init_db
from routes.connections import router as connections_router
from routes.queries import router as queries_router
from routes.transactions import router as transactions_router
from routes.wal import router as wal_router
from routes.recovery import router as recovery_router
from routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title='DBClient UCR — Backend',
    description='Integrated Client for Distributed Database Engines',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://localhost:3000', '*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

API_PREFIX = '/api'
app.include_router(connections_router, prefix=API_PREFIX)
app.include_router(queries_router, prefix=API_PREFIX)
app.include_router(transactions_router, prefix=API_PREFIX)
app.include_router(wal_router, prefix=API_PREFIX)
app.include_router(recovery_router, prefix=API_PREFIX)
app.include_router(health_router, prefix=API_PREFIX)


@app.get('/')
def root():
    return {'message': 'DBClient UCR Backend running', 'docs': '/docs'}
