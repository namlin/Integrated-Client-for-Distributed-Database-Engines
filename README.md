# Cliente Integrado de Motores de Bases de Datos Distribuidas

**CI-0141 Bases de Datos Avanzadas — Universidad de Costa Rica, ECCI**
**I Ciclo 2026**

Sistema cliente unificado que se conecta simultáneamente a múltiples motores de bases de datos (relacionales y NoSQL), ejecuta consultas sobre ellos, mantiene una bitácora transaccional (Write-Ahead Log) y simula los cuatro protocolos de recuperación ante fallos: **No-Undo/No-Redo**, **No-Undo/Redo**, **Undo/No-Redo** y **Undo/Redo**.

---

## Tabla de contenidos

1. [Arquitectura general](#arquitectura-general)
2. [Requisitos previos](#requisitos-previos)
3. [Instalación](#instalación)
4. [Configuración con Docker Compose](#configuración-con-docker-compose)
5. [Ejecutar la aplicación](#ejecutar-la-aplicación)
6. [Ejecutar las pruebas](#ejecutar-las-pruebas)
7. [Variables de entorno](#variables-de-entorno)
8. [Referencia de la API](#referencia-de-la-api)
9. [Motores de bases de datos soportados](#motores-de-bases-de-datos-soportados)
10. [Protocolos de recuperación](#protocolos-de-recuperación)

---

## Arquitectura general

```
┌──────────────────────────────────────────────────────────┐
│                     Navegador                            │
│   React + Vite + Tailwind CSS  (puerto 5173)             │
│                                                          │
│  Header ─ Sidebar ─ EditorPanel ─ ResultsPanel           │
│              │                                           │
│         DBClientContext  ◄──── fetch/REST ──────┐        │
└─────────────────────────────────────────────────┼────────┘
                                                  │
┌─────────────────────────────────────────────────┼────────┐
│            FastAPI Backend  (puerto 8000)       │        │
│                                                 │        │
│  /api/connections   /api/queries                │        │
│  /api/transactions  /api/wal                    │        │
│  /api/recovery      /api/health                 │        │
│                                                          │
│  ┌──────────────────────────────────────────┐            │
│  │           Capa de servicios              │            │
│  │  DBManager │ WALService │ TxManager      │            │
│  │  QueryExecutor │ RecoveryService         │            │
│  └──────────────────────────────────────────┘            │
│                                                          │
│  ┌──────────────────────────────────────────┐            │
│  │         Adaptadores por motor            │            │
│  │  PostgreSQL │ MongoDB │ MySQL │ Redis    │            │
│  └──────────────────────────────────────────┘            │
│                                                          │
│  WAL persistido en SQLite  (database/wal.db)             │
└──────────────────────────────────────────────────────────┘
          │           │           │          │
     PostgreSQL   MongoDB      MySQL       Redis
```

---

## Requisitos previos

| Herramienta | Versión Recomendada | Uso |
|---|---|---|
| Python | 3.12 | Backend FastAPI |
| Node.js | 18 | Frontend React/Vite |
| npm | 9 | Gestión de paquetes frontend |
| Docker + Docker Compose | 24 | Nodos de bases de datos |

> **Nota:** Docker Compose es la forma recomendada de levantar los nodos de BD. Si ya tienes instancias de PostgreSQL/MongoDB corriendo, puedes saltarte esa sección.

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/namlin/Integrated-Client-for-Distributed-Database-Engines.git
cd Integrated-Client-for-Distributed-Database-Engines
```

### 2. Instalar dependencias del backend

```bash
cd backend

# Crear y activar el entorno virtual
python3.12 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Instalar dependencias del frontend

```bash
cd ../client
npm install
```

---

## Configuración con Docker Compose

La forma más sencilla de levantar los nodos de bases de datos es usando Docker Compose. Esto permite reproducir el entorno completo sin instalar PostgreSQL ni MongoDB manualmente.

```bash
# Desde docker/
docker compose up -d
```

Esto levanta:

| Servicio | Motor | Puerto | Usuario | Contraseña | Base de datos |
|---|---|---|---|---|---|
| `postgres` | PostgreSQL 16 | 5432 | `postgres` | `password` | `integrated-client` |
| `mongo` | MongoDB 7 | 27017 | `mongo` | `password` | `integrated-client` |
Para detener los nodos:

```bash
docker compose down
```

> Si prefieres usar instancias propias, agrega las conexiones directamente desde la interfaz al iniciar la aplicación.

---

## Ejecutar la aplicación

Abre **dos terminales** desde la raíz del repositorio.

### Terminal 1 — Backend

```bash
cd backend
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

uvicorn app:app --host 127.0.0.1 --port 8000 --reload --reload-dir . --reload-exclude venv
```

El servidor queda disponible en `http://localhost:8000`.

### Terminal 2 — Frontend

```bash
cd client
npm run dev
```

La aplicación queda disponible en `http://localhost:5173`.

### Flujo básico de uso

1. Abre `http://localhost:5173` en el navegador.
2. Haz clic en **"+ Nueva conexión"** y agrega tus credenciales de PostgreSQL o MongoDB.
3. Selecciona un protocolo de recuperación en el header (No-Undo/No-Redo, No-Undo/Redo, etc.).
4. Escribe una consulta en el editor, por ejemplo:
   ```sql
   BEGIN;
   UPDATE students SET grade = 95 WHERE id = 1;
   ```
5. Haz clic en **Ejecutar**.
6. Usa **COMMIT** o **ROLLBACK** para finalizar la transacción.
7. Haz clic en **Simular fallo** para interrumpir una transacción activa y luego ve a la pestaña **Recuperación** para ejecutar el proceso de recuperación.
8. La pestaña **Bitácora (WAL)** muestra todas las operaciones registradas con sus imágenes antes/después.

### Usar los nodos existentes en /docker

1. Haz clic en **"+ Nueva conexión"** y completa el formulario con las siguientes credenciales:

   **Para PostgreSQL:**
   * **Nombre de la Conexión:** (Ej. PostgreSQL Docker)
   * **Tipo de Motor:** PostgreSQL
   * **Host:** localhost
   * **Puerto:** 5432
   * **Usuario:** postgres
   * **Contraseña:** password
   * **Base de Datos:** integrated-client

   **Para MongoDB:**
   * **Nombre de la Conexión:** (Ej. MongoDB Docker)
   * **Tipo de Motor:** MongoDB
   * **Host:** localhost
   * **Puerto:** 27017
   * **Usuario:** mongo
   * **Contraseña:** password
   * **Base de Datos:** admin *(o déjalo en blanco si tu adaptador no lo requiere)*

---

## Ejecutar las pruebas

Las pruebas automatizadas cubren conexiones, WAL, transacciones y los cuatro protocolos de recuperación.

```bash
cd backend
source venv/bin/activate

# Ejecutar todas las pruebas
python -m pytest tests/ -v

# Ejecutar sólo las pruebas de recuperación
python -m pytest tests/test_recovery.py -v

# Con reporte de cobertura (requiere pytest-cov)
python -m pytest tests/ -v --tb=short
```

Resultado esperado: **21 pruebas, todas en verde**.

```
tests/test_connections.py::test_list_connections_empty         PASSED
tests/test_connections.py::test_create_connection_bad_engine   PASSED
tests/test_connections.py::test_create_and_disconnect          PASSED
tests/test_connections.py::test_disconnect_nonexistent         PASSED
tests/test_queries.py::test_execute_no_connection              PASSED
tests/test_queries.py::test_execute_select                     PASSED
tests/test_queries.py::test_execute_with_begin                 PASSED
tests/test_queries.py::test_health                             PASSED
tests/test_recovery.py::test_no_undo_no_redo_failed            PASSED
tests/test_recovery.py::test_no_undo_redo_committed            PASSED
tests/test_recovery.py::test_undo_no_redo_failed               PASSED
tests/test_recovery.py::test_undo_redo_failed                  PASSED
tests/test_recovery.py::test_undo_redo_committed               PASSED
tests/test_recovery.py::test_simulate_failure_api              PASSED
tests/test_transactions.py::test_begin_commit_cycle            PASSED
tests/test_transactions.py::test_begin_rollback_cycle          PASSED
tests/test_transactions.py::test_commit_nonexistent            PASSED
tests/test_transactions.py::test_inline_begin_in_query         PASSED
tests/test_wal.py::test_wal_log_and_retrieve                   PASSED
tests/test_wal.py::test_wal_filter_by_operation                PASSED
tests/test_wal.py::test_wal_persistence_via_api                PASSED
======================== 21 passed ========================
```

---

## Variables de entorno

El backend no requiere un archivo `.env` para funcionar. Las credenciales de conexión a las bases de datos se gestionan en tiempo de ejecución a través de la interfaz (POST `/api/connections`).

Para referencia, copia `.env.example`:

```bash
cp backend/.env.example backend/.env
```

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `WAL_DB_PATH` | Ruta del archivo SQLite para la bitácora | `backend/database/wal.db` |

---

## Referencia de la API

Con el backend corriendo, la documentación interactiva (Swagger UI) está disponible en:

```
http://localhost:8000/docs
```

### Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/connections` | Lista todas las conexiones registradas |
| `POST` | `/api/connections` | Registra y conecta un nuevo motor |
| `PUT` | `/api/connections/{id}/disconnect` | Desconecta sin eliminar la configuración |
| `DELETE` | `/api/connections/{id}` | Elimina una conexión permanentemente |
| `POST` | `/api/queries/execute` | Ejecuta una consulta en el motor activo |
| `POST` | `/api/transactions/begin` | Inicia una transacción con el protocolo indicado |
| `PUT` | `/api/transactions/{tid}/commit` | Confirma una transacción |
| `PUT` | `/api/transactions/{tid}/rollback` | Revierte una transacción |
| `GET` | `/api/wal` | Lista entradas de bitácora (filtros: `tid`, `op`, `start_ts`, `end_ts`) |
| `GET` | `/api/wal/entries/{tid}` | Entradas de bitácora para una transacción específica |
| `POST` | `/api/recovery/simulate-failure/{tid}` | Marca una transacción como FALLIDA |
| `POST` | `/api/recovery/run/{tid}` | Ejecuta la recuperación con el protocolo indicado |
| `GET` | `/api/health` | Estado general del sistema |

---

## Motores de bases de datos soportados

| Motor | Tipo | Driver Python | Puerto por defecto |
|---|---|---|---|
| PostgreSQL | Relacional | psycopg2-binary | 5432 |
| MySQL / MariaDB | Relacional | mysql-connector-python | 3306 |
| MongoDB | NoSQL (documentos) | pymongo | 27017 |
| Redis | NoSQL (clave-valor) | redis-py | 6379 |

### Formato de consultas por motor

**PostgreSQL / MySQL** — SQL estándar:
```sql
BEGIN;
INSERT INTO products (name, price) VALUES ('Laptop', 999.99);
UPDATE products SET price = 849.99 WHERE name = 'Laptop';
COMMIT;
```

**MongoDB** — JSON estructurado:
```json
{"collection": "products", "operation": "find", "filter": {"price": {"$gt": 500}}}
{"collection": "products", "operation": "insertOne", "document": {"name": "Laptop", "price": 999}}
{"collection": "products", "operation": "updateOne", "filter": {"name": "Laptop"}, "update": {"$set": {"price": 849}}}
```

**Redis** — JSON estructurado:
```json
{"command": "SET", "key": "session:123", "value": "active"}
{"command": "GET", "key": "session:123"}
{"command": "DEL", "key": "session:123"}
```

---

## Protocolos de recuperación

El sistema implementa los cuatro protocolos estándar de recuperación ante fallos:

| Protocolo | UNDO | REDO | Política de buffer |
|---|---|---|---|
| **No-Undo / No-Redo** | No | No | Steal=No, Force=Yes |
| **No-Undo / Redo** | No | Sí | Steal=No, Force=No |
| **Undo / No-Redo** | Sí | No | Steal=Yes, Force=Yes |
| **Undo / Redo** | Sí | Sí | Steal=Yes, Force=No |

### Cómo simular una recuperación

1. Selecciona un protocolo en el header de la aplicación.
2. Inicia una transacción (`BEGIN` en el editor o haciendo clic en Ejecutar con BEGIN en la consulta).
3. Ejecuta una o más operaciones de escritura (INSERT / UPDATE / DELETE).
4. Haz clic en **"Simular fallo"** — la transacción se marca como FALLIDA sin hacer COMMIT.
5. Ve a la pestaña **Recuperación**.
6. Haz clic en el botón de la transacción fallida para ejecutar la recuperación.
7. Observa las acciones UNDO/REDO generadas y el estado antes/después de los datos.

---

## Estructura del proyecto

```
.
├── backend/
│   ├── app.py                  # Punto de entrada FastAPI
│   ├── requirements.txt
│   ├── .env.example
│   ├── adapters/               # Adaptadores por motor de BD
│   │   ├── base_adapter.py
│   │   ├── postgresql_adapter.py
│   │   ├── mongodb_adapter.py
│   │   ├── mysql_adapter.py
│   │   └── redis_adapter.py
│   ├── services/               # Lógica de negocio
│   │   ├── db_manager.py
│   │   ├── wal_service.py
│   │   ├── transaction_manager.py
│   │   ├── query_executor.py
│   │   └── recovery_service.py
│   ├── routes/                 # Endpoints REST
│   │   ├── connections.py
│   │   ├── queries.py
│   │   ├── transactions.py
│   │   ├── wal.py
│   │   ├── recovery.py
│   │   └── health.py
│   ├── models/
│   │   └── schemas.py          # Modelos Pydantic
│   ├── database/
│   │   └── init_wal_db.py      # Esquema SQLite
│   └── tests/                  # 21 pruebas automatizadas
│       ├── conftest.py
│       ├── test_connections.py
│       ├── test_queries.py
│       ├── test_transactions.py
│       ├── test_wal.py
│       └── test_recovery.py
├── client/
│   ├── src/
│   │   ├── components/         # Componentes React
│   │   ├── contexts/
│   │   │   └── DBClientContext.jsx   # Estado global + llamadas API
│   │   └── config/
│   │       └── configApi.jsx   # Funciones fetch hacia el backend
│   └── package.json
├── docker-compose.yml          # Nodos de BD para desarrollo
└── README.md
```