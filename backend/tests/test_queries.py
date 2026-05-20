import pytest


def test_execute_no_connection(client):
    r = client.post('/api/queries/execute', json={
        'connectionId': 'nonexistent',
        'query': 'SELECT 1',
    })
    assert r.status_code == 400
    assert 'No active connection' in r.json()['detail']


def test_execute_select(client, mock_pg_adapter):
    r = client.post('/api/connections', json={
        'name': 'Query Test', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']

    r2 = client.post('/api/queries/execute', json={
        'connectionId': conn_id,
        'query': 'SELECT * FROM students',
        'protocol': 'Undo/Redo',
    })
    assert r2.status_code == 200
    data = r2.json()
    assert 'results' in data
    assert 'columns' in data
    assert 'txn_id' in data
    assert 'timestamp' in data

    client.delete(f'/api/connections/{conn_id}')


def test_execute_with_begin(client, mock_pg_adapter):
    r = client.post('/api/connections', json={
        'name': 'Begin Test', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']

    r2 = client.post('/api/queries/execute', json={
        'connectionId': conn_id,
        'query': 'BEGIN',
        'protocol': 'No-Undo/No-Redo',
    })
    assert r2.status_code == 200
    assert r2.json()['txn_id'] is not None

    client.delete(f'/api/connections/{conn_id}')


def test_health(client):
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
