import pytest
from services.wal_service import WALService
from services.transaction_manager import TransactionManager


def test_wal_log_and_retrieve():
    svc = WALService()
    tm = TransactionManager()

    tid = tm.begin('conn-test', 'Undo/Redo')
    entry_id = svc.log_operation(
        tid=tid, operation='UPDATE', table_name='students',
        before_image={'id': 1, 'grade': 80},
        engine_id='conn-test', original_query="UPDATE students SET grade=90 WHERE id=1"
    )
    svc.update_after_image(entry_id, {'id': 1, 'grade': 90})

    entries = svc.get_entries(tid=tid)
    write_entries = [e for e in entries if e['op'] == 'UPDATE']
    assert len(write_entries) == 1
    assert write_entries[0]['tabla'] == 'students'
    assert '80' in write_entries[0]['before']
    assert '90' in write_entries[0]['after']


def test_wal_filter_by_operation():
    svc = WALService()
    tm = TransactionManager()

    tid = tm.begin('conn-filter', 'No-Undo/Redo')
    svc.log_operation(tid=tid, operation='INSERT', table_name='orders',
                      before_image=None, engine_id='conn-filter',
                      original_query="INSERT INTO orders VALUES (1,'item')")

    entries = svc.get_entries(tid=tid, operation='INSERT')
    assert all(e['op'] == 'INSERT' for e in entries)
    assert len(entries) >= 1


def test_wal_persistence_via_api(client, mock_pg_adapter):
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'WAL Test', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    assert r.status_code == 201
    conn_id = r.json()['id']

    # Begin transaction
    r2 = client.post('/api/transactions/begin', json={
        'connectionId': conn_id, 'protocol': 'Undo/Redo'
    })
    assert r2.status_code == 200
    tid = r2.json()['tid']

    # Execute write query
    client.post('/api/queries/execute', json={
        'connectionId': conn_id,
        'query': "UPDATE students SET grade=90 WHERE id=1",
        'protocol': 'Undo/Redo',
        'tid': tid
    })

    # WAL entries should exist for this tid
    r3 = client.get(f'/api/wal/entries/{tid}')
    assert r3.status_code == 200
    assert len(r3.json()) >= 1

    client.delete(f'/api/connections/{conn_id}')
