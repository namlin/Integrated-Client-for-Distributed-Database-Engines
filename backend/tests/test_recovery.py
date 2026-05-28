import json
import pytest
from services.wal_service import WALService
from services.transaction_manager import TransactionManager
from services.recovery_service import RecoveryService
TEST_CLIENT_ID = 'test-session-001'


def _setup_transaction(protocol: str):
    tm = TransactionManager()
    svc = WALService()
    rs = RecoveryService()

    tid = tm.begin('conn-recovery', protocol, TEST_CLIENT_ID)
    entry_id = svc.log_operation(
        tid=tid, operation='UPDATE', table_name='accounts',
        before_image={'id': 1, 'balance': 500},
        engine_id='conn-recovery',
        original_query="UPDATE accounts SET balance=300 WHERE id=1"
    )
    svc.update_after_image(entry_id, {'id': 1, 'balance': 300})
    return tid, tm, svc, rs


def test_no_undo_no_redo_failed():
    tid, tm, svc, rs = _setup_transaction('No-Undo/No-Redo')
    tm.mark_failed(tid)
    result = rs.run_recovery(tid, 'No-Undo/No-Redo')
    assert result['status'] == 'completed'
    assert any('No-Undo/No-Redo' in a for a in result['recovery_actions'])
    assert not any(a.strip().startswith('UNDO') for a in result['recovery_actions'])
    assert not any(a.strip().startswith('REDO') for a in result['recovery_actions'])


def test_no_undo_redo_committed():
    tid, tm, svc, rs = _setup_transaction('No-Undo/Redo')
    tm.commit(tid, TEST_CLIENT_ID)
    result = rs.run_recovery(tid, 'No-Undo/Redo')
    assert result['status'] == 'completed'
    assert any('REDO' in a for a in result['recovery_actions'])
    assert not any('UNDO' in a for a in result['recovery_actions'])


def test_undo_no_redo_failed():
    tid, tm, svc, rs = _setup_transaction('Undo/No-Redo')
    tm.mark_failed(tid)
    result = rs.run_recovery(tid, 'Undo/No-Redo')
    assert result['status'] == 'completed'
    assert any('UNDO' in a for a in result['recovery_actions'])
    assert not any('REDO' in a for a in result['recovery_actions'])


def test_undo_redo_failed():
    tid, tm, svc, rs = _setup_transaction('Undo/Redo')
    tm.mark_failed(tid)
    result = rs.run_recovery(tid, 'Undo/Redo')
    assert result['status'] == 'completed'
    assert any('UNDO' in a for a in result['recovery_actions'])


def test_undo_redo_committed():
    tid, tm, svc, rs = _setup_transaction('Undo/Redo')
    tm.commit(tid, TEST_CLIENT_ID)
    result = rs.run_recovery(tid, 'Undo/Redo')
    assert result['status'] == 'completed'
    assert any('REDO' in a for a in result['recovery_actions'])


def test_simulate_failure_api(client, mock_pg_adapter):
    r = client.post('/api/connections', json={
        'name': 'Recovery Conn', 'engine': 'PostgreSQL',
        'host': 'localhost', 'port': 5432,
        'username': 'u', 'password': 'p', 'database': 'd'
    })
    conn_id = r.json()['id']

    r2 = client.post('/api/transactions/begin', json={
        'connectionId': conn_id, 'protocol': 'Undo/Redo'
    })
    tid = r2.json()['tid']

    r3 = client.post(f'/api/recovery/simulate-failure/{tid}')
    assert r3.status_code == 200
    assert r3.json()['status'] == 'FAILED'

    r4 = client.post(f'/api/recovery/run/{tid}', json={'protocol': 'Undo/Redo'})
    assert r4.status_code == 200
    assert r4.json()['status'] == 'completed'

    client.delete(f'/api/connections/{conn_id}')
