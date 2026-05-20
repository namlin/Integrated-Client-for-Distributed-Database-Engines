import pytest


def test_list_connections_empty(client):
    r = client.get('/api/connections')
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_connection_bad_engine(client):
    r = client.post('/api/connections', json={
        'name': 'bad', 'engine': 'Oracle', 'host': 'localhost', 'port': 1521
    })
    assert r.status_code == 400
    assert 'Unsupported engine' in r.json()['detail']


def test_create_and_disconnect(client, mock_pg_adapter):
    # Create
    r = client.post('/api/connections', json={
        'name': 'Test PG', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'test', 'password': 'test', 'database': 'testdb'
    })
    assert r.status_code == 201
    data = r.json()
    assert data['status'] == 'connected'
    assert data['color'] == 'green'
    conn_id = data['id']

    # List includes new connection
    r2 = client.get('/api/connections')
    ids = [c['id'] for c in r2.json()]
    assert conn_id in ids

    # Disconnect
    r3 = client.put(f'/api/connections/{conn_id}/disconnect')
    assert r3.status_code == 200
    assert r3.json()['status'] == 'desconectado'

    # Delete
    r4 = client.delete(f'/api/connections/{conn_id}')
    assert r4.status_code == 200


def test_disconnect_nonexistent(client):
    r = client.put('/api/connections/does-not-exist/disconnect')
    assert r.status_code == 404
