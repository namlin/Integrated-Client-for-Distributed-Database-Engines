import sqlite3
import os

WAL_DB_PATH = os.path.join(os.path.dirname(__file__), 'wal.db')


def init_db():
    conn = sqlite3.connect(WAL_DB_PATH)
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS connections (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            engine TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            username TEXT,
            password TEXT,
            database_name TEXT,
            status TEXT DEFAULT 'disconnected',
            node TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            tid TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            protocol TEXT NOT NULL,
            engine_id TEXT,
            start_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_ts TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS wal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tid TEXT NOT NULL,
            operation TEXT NOT NULL,
            table_name TEXT,
            before_image TEXT,
            after_image TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            engine_id TEXT,
            original_query TEXT
        );

        CREATE TABLE IF NOT EXISTS recovery_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tid TEXT NOT NULL,
            protocol TEXT NOT NULL,
            recovery_actions TEXT,
            before_state TEXT,
            after_state TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(WAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
