import pytest


def test_begin_commit_cycle(client, mock_pg_adapter):
    r = client.post('/api/connections', json={
        'name': 'TXN Test', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']

    # Begin
    r2 = client.post('/api/transactions/begin', json={
        'connectionId': conn_id, 'protocol': 'Undo/Redo'
    })
    assert r2.status_code == 200
    tid = r2.json()['tid']
    assert tid.startswith('TXN-')

    # Commit
    r3 = client.put(f'/api/transactions/{tid}/commit')
    assert r3.status_code == 200
    assert r3.json()['status'] == 'COMMITTED'

    # List contains the transaction
    r4 = client.get('/api/transactions')
    tids = [t['id'] for t in r4.json()]
    assert tid in tids

    client.delete(f'/api/connections/{conn_id}')


def test_begin_rollback_cycle(client, mock_pg_adapter):
    r = client.post('/api/connections', json={
        'name': 'Rollback Test', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']

    r2 = client.post('/api/transactions/begin', json={
        'connectionId': conn_id, 'protocol': 'Undo/No-Redo'
    })
    tid = r2.json()['tid']

    r3 = client.put(f'/api/transactions/{tid}/rollback')
    assert r3.status_code == 200
    assert r3.json()['status'] == 'ABORTED'

    client.delete(f'/api/connections/{conn_id}')


def test_commit_nonexistent(client):
    r = client.put('/api/transactions/TXN-9999/commit')
    assert r.status_code == 404


def test_inline_begin_in_query(client, mock_pg_adapter):
    r = client.post('/api/connections', json={
        'name': 'Inline TXN', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']

    r2 = client.post('/api/queries/execute', json={
        'connectionId': conn_id,
        'query': 'BEGIN; SELECT 1',
        'protocol': 'No-Undo/Redo',
    })
    assert r2.status_code == 200
    assert r2.json()['txn_id'] is not None

    client.delete(f'/api/connections/{conn_id}')
