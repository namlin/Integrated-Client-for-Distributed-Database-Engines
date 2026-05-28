import pytest
from services.transaction_manager import transaction_manager


def test_no_steal_buffers_writes_no_undo_no_redo(client, mock_pg_adapter):
    """Verify No-Undo/No-Redo protocol buffers writes instead of executing immediately."""
    protocol = 'No-Undo/No-Redo'
    
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'NoSteal Test 1', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']
    
    try:
        # Start transaction
        r1 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'BEGIN',
            'protocol': protocol,
        })
        tid = r1.json()['txn_id']
        assert tid is not None
        
        # Execute UPDATE (should be buffered, not executed)
        r2 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'UPDATE test_table SET value = 20 WHERE id = 1',
            'protocol': protocol,
            'tid': tid
        })
        
        # Verify operation was buffered (pending_operations should have entry)
        assert tid in transaction_manager.pending_operations
        assert len(transaction_manager.pending_operations[tid]) > 0
        
    finally:
        client.delete(f'/api/connections/{conn_id}')


def test_no_steal_executes_on_commit_no_undo_no_redo(client, mock_pg_adapter):
    """Verify No-Undo/No-Redo writes execute on COMMIT."""
    protocol = 'No-Undo/No-Redo'
    
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'NoSteal Test 2', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']
    
    try:
        # Start transaction
        r1 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'BEGIN',
            'protocol': protocol,
        })
        tid = r1.json()['txn_id']
        
        # Execute UPDATE (buffered)
        r2 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'UPDATE test_table SET value = 25 WHERE id = 1',
            'protocol': protocol,
            'tid': tid
        })
        
        # Verify it's buffered
        assert len(transaction_manager.pending_operations[tid]) > 0
        
        # Commit transaction
        r3 = client.put(f'/api/transactions/{tid}/commit')
        assert r3.status_code == 200
        
        # Verify buffer was cleared after commit
        assert len(transaction_manager.pending_operations.get(tid, [])) == 0
        
    finally:
        client.delete(f'/api/connections/{conn_id}')


def test_no_steal_discards_on_rollback_no_undo_no_redo(client, mock_pg_adapter):
    """Verify No-Undo/No-Redo rollback discards buffered writes without executing."""
    protocol = 'No-Undo/No-Redo'
    
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'NoSteal Test 3', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']
    
    try:
        # Start transaction
        r1 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'BEGIN',
            'protocol': protocol,
        })
        tid = r1.json()['txn_id']
        
        # Execute UPDATE (buffered)
        r2 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'UPDATE test_table SET value = 999 WHERE id = 1',
            'protocol': protocol,
            'tid': tid
        })
        
        # Verify it's buffered
        assert len(transaction_manager.pending_operations[tid]) > 0
        
        # Rollback transaction
        r3 = client.put(f'/api/transactions/{tid}/rollback')
        assert r3.status_code == 200
        
        # Verify buffer was cleared after rollback
        assert len(transaction_manager.pending_operations.get(tid, [])) == 0
        
    finally:
        client.delete(f'/api/connections/{conn_id}')


def test_no_steal_multiple_operations_no_undo_redo(client, mock_pg_adapter):
    """Verify No-Undo/Redo buffers and executes multiple operations."""
    protocol = 'No-Undo/Redo'
    
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'NoSteal Test 4', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']
    
    try:
        # Start transaction
        r1 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'BEGIN',
            'protocol': protocol,
        })
        tid = r1.json()['txn_id']
        
        # Execute multiple operations (all should be buffered)
        r2 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'UPDATE test_table SET value = 50 WHERE id = 1',
            'protocol': protocol,
            'tid': tid
        })
        
        r3 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'INSERT INTO test_table (name, value) VALUES ("new", 100)',
            'protocol': protocol,
            'tid': tid
        })
        
        # Verify both are buffered
        assert len(transaction_manager.pending_operations[tid]) == 2
        
        # Commit should execute both
        r4 = client.put(f'/api/transactions/{tid}/commit')
        assert r4.status_code == 200
        
        # Verify buffer was cleared
        assert len(transaction_manager.pending_operations.get(tid, [])) == 0
        
    finally:
        client.delete(f'/api/connections/{conn_id}')


def test_steal_executes_immediately_undo_redo(client, mock_pg_adapter):
    """Verify Undo/Redo protocol executes writes immediately (not buffered)."""
    protocol = 'Undo/Redo'
    
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'Steal Test 1', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']
    
    try:
        # Start transaction
        r1 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'BEGIN',
            'protocol': protocol,
        })
        tid = r1.json()['txn_id']
        
        # Execute UPDATE (should execute immediately, not buffer)
        r2 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'UPDATE test_table SET value = 77 WHERE id = 1',
            'protocol': protocol,
            'tid': tid
        })
        
        # Verify NOT buffered (empty or not present)
        assert len(transaction_manager.pending_operations.get(tid, [])) == 0
        
    finally:
        client.delete(f'/api/connections/{conn_id}')


def test_steal_executes_immediately_undo_no_redo(client, mock_pg_adapter):
    """Verify Undo/No-Redo protocol executes writes immediately (not buffered)."""
    protocol = 'Undo/No-Redo'
    
    # Create connection
    r = client.post('/api/connections', json={
        'name': 'Steal Test 2', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']
    
    try:
        # Start transaction
        r1 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'BEGIN',
            'protocol': protocol,
        })
        tid = r1.json()['txn_id']
        
        # Execute UPDATE (should execute immediately, not buffer)
        r2 = client.post('/api/queries/execute', json={
            'connectionId': conn_id,
            'query': 'UPDATE test_table SET value = 88 WHERE id = 1',
            'protocol': protocol,
            'tid': tid
        })
        
        # Verify NOT buffered (empty or not present)
        assert len(transaction_manager.pending_operations.get(tid, [])) == 0
        
    finally:
        client.delete(f'/api/connections/{conn_id}')
