import pytest
import json
from services.wal_service import wal_service
from services.transaction_manager import transaction_manager
from services.recovery_service import recovery_service
from adapters.mongodb_adapter import MongoDBAdapter


@pytest.fixture
def mongo_adapter(monkeypatch):
    """Fixture para un adaptador Mongo mockeado."""
    from pymongo import MongoClient
    
    # Usar instancia local de MongoDB (asume que corre en localhost:27017)
    try:
        adapter = MongoDBAdapter({
            'host': 'localhost',
            'port': 27017,
            'username': 'mongo',
            'password': 'password',
            'database': 'test_recovery',
        })
        adapter.connect()
        # Limpiar colecciones de prueba
        adapter.connection['test_collection'].drop()
        yield adapter
        # Cleanup
        adapter.connection['test_collection'].drop()
        adapter.disconnect()
    except Exception:
        pytest.skip("MongoDB not available at localhost:27017")


def test_mongo_before_image_update(mongo_adapter):
    """Verifica que UPDATE en Mongo captura before_image en WAL."""
    col = mongo_adapter.connection['test_collection']
    col.insert_one({'_id': 'doc1', 'name': 'Alice', 'score': 90})
    
    tid = transaction_manager.begin('mongo-conn-id', 'Undo/Redo')
    
    # Execute UPDATE
    query = json.dumps({
        'collection': 'test_collection',
        'operation': 'updateOne',
        'filter': {'_id': 'doc1'},
        'update': {'$set': {'score': 95}}
    })
    
    rows, affected, columns = mongo_adapter.execute_query(query)
    
    # Log a WAL (simulando lo que hace query_executor)
    before = rows[0].pop('_before') if rows and '_before' in rows[0] else None
    after_query = json.dumps({'_id': 'doc1', 'name': 'Alice', 'score': 95})
    
    entry_id = wal_service.log_operation(
        tid=tid, operation='UPDATE', table_name='test_collection',
        before_image=before, engine_id='mongo-conn-id', original_query=query,
    )
    wal_service.update_after_image(entry_id, [{'_id': 'doc1', 'name': 'Alice', 'score': 95}])
    
    # Verificar WAL tiene before y after
    entries = wal_service.get_entries(tid=tid)
    update_entry = [e for e in entries if e['op'] == 'UPDATE'][0]
    
    before_loaded = json.loads(update_entry['before'])
    after_loaded = json.loads(update_entry['after'])
    
    # Normalize: after_loaded puede ser dict o list
    after_doc = after_loaded if isinstance(after_loaded, dict) else (after_loaded[0] if after_loaded else {})
    
    assert before_loaded.get('score') == 90, f"Before image should have score 90, got {before_loaded}"
    assert after_doc.get('score') == 95, f"After image should have score 95, got {after_loaded}"
    
    transaction_manager.mark_failed(tid)


def test_mongo_before_image_delete(mongo_adapter):
    """Verifica que DELETE en Mongo captura before_image en WAL."""
    col = mongo_adapter.connection['test_collection']
    col.insert_one({'_id': 'doc2', 'name': 'Bob', 'grade': 85})
    
    tid = transaction_manager.begin('mongo-conn-id', 'Undo/Redo')
    
    query = json.dumps({
        'collection': 'test_collection',
        'operation': 'deleteOne',
        'filter': {'_id': 'doc2'}
    })
    
    rows, affected, columns = mongo_adapter.execute_query(query)
    before = rows[0].pop('_before') if rows and '_before' in rows[0] else None
    
    entry_id = wal_service.log_operation(
        tid=tid, operation='DELETE', table_name='test_collection',
        before_image=before, engine_id='mongo-conn-id', original_query=query,
    )
    
    # Verificar WAL tiene el documento antes
    entries = wal_service.get_entries(tid=tid)
    delete_entry = [e for e in entries if e['op'] == 'DELETE'][0]
    
    before_loaded = json.loads(delete_entry['before'])
    assert before_loaded.get('name') == 'Bob', f"Before image should have name Bob, got {before_loaded}"
    assert before_loaded.get('grade') == 85
    
    transaction_manager.mark_failed(tid)


def test_mongo_undo_update_recovery(mongo_adapter):
    """Verifica que UNDO restaura un UPDATE en Mongo."""
    col = mongo_adapter.connection['test_collection']
    col.insert_one({'_id': 'doc3', 'name': 'Charlie', 'score': 80})
    
    tid = transaction_manager.begin('mongo-conn-id', 'Undo/Redo')
    
    # Update
    query = json.dumps({
        'collection': 'test_collection',
        'operation': 'updateOne',
        'filter': {'_id': 'doc3'},
        'update': {'$set': {'score': 100}}
    })
    
    rows, affected, columns = mongo_adapter.execute_query(query)
    before = rows[0].pop('_before') if rows and '_before' in rows[0] else None
    
    entry_id = wal_service.log_operation(
        tid=tid, operation='UPDATE', table_name='test_collection',
        before_image=before, engine_id='mongo-conn-id', original_query=query,
    )
    wal_service.update_after_image(entry_id, [{'_id': 'doc3', 'name': 'Charlie', 'score': 100}])
    
    # Simulate failure
    transaction_manager.mark_failed(tid)
    
    # Run recovery with UNDO
    result = recovery_service.run_recovery(tid, 'Undo/Redo', mongo_adapter)
    
    # Verificar que el UNDO se aplicó
    recovered_doc = col.find_one({'_id': 'doc3'})
    assert recovered_doc is not None, "Document should exist after UNDO"
    assert recovered_doc['score'] == 80, f"Score should be restored to 80, got {recovered_doc['score']}"
    assert 'UNDO' in str(result['recovery_actions']), "Recovery should have UNDO actions"


def test_mongo_undo_delete_recovery(mongo_adapter):
    """Verifica que UNDO reinserta un documento DELETE-ado en Mongo."""
    col = mongo_adapter.connection['test_collection']
    col.insert_one({'_id': 'doc4', 'name': 'Diana', 'level': 42})
    
    tid = transaction_manager.begin('mongo-conn-id', 'Undo/Redo')
    
    # Delete
    query = json.dumps({
        'collection': 'test_collection',
        'operation': 'deleteOne',
        'filter': {'_id': 'doc4'}
    })
    
    rows, affected, columns = mongo_adapter.execute_query(query)
    before = rows[0].pop('_before') if rows and '_before' in rows[0] else None
    
    entry_id = wal_service.log_operation(
        tid=tid, operation='DELETE', table_name='test_collection',
        before_image=before, engine_id='mongo-conn-id', original_query=query,
    )
    
    # Simulate failure
    transaction_manager.mark_failed(tid)
    
    # Run recovery with UNDO
    result = recovery_service.run_recovery(tid, 'Undo/Redo', mongo_adapter)
    
    # Verificar que el documento fue reinsertado
    recovered_doc = col.find_one({'_id': 'doc4'})
    assert recovered_doc is not None, "Deleted document should be restored"
    assert recovered_doc['name'] == 'Diana'
    assert recovered_doc['level'] == 42
    assert 'UNDO' in str(result['recovery_actions'])


def test_mongo_redo_committed_recovery(mongo_adapter):
    """Verifica que REDO aplica cambios en una transacción committed."""
    col = mongo_adapter.connection['test_collection']
    col.insert_one({'_id': 'doc5', 'name': 'Eve', 'status': 'active'})
    
    tid = transaction_manager.begin('mongo-conn-id', 'No-Undo/Redo')
    
    # Update
    query = json.dumps({
        'collection': 'test_collection',
        'operation': 'updateOne',
        'filter': {'_id': 'doc5'},
        'update': {'$set': {'status': 'inactive'}}
    })
    
    rows, affected, columns = mongo_adapter.execute_query(query)
    before = rows[0].pop('_before') if rows and '_before' in rows[0] else None
    
    entry_id = wal_service.log_operation(
        tid=tid, operation='UPDATE', table_name='test_collection',
        before_image=before, engine_id='mongo-conn-id', original_query=query,
    )
    wal_service.update_after_image(entry_id, [{'_id': 'doc5', 'name': 'Eve', 'status': 'inactive'}])
    
    # Commit (simulate via transaction_manager)
    transaction_manager.commit(tid)
    
    # Restore DB state before the change (simulate crash recovery)
    col.update_one({'_id': 'doc5'}, {'$set': {'status': 'active'}})
    
    # Run recovery with REDO (should reapply the update)
    result = recovery_service.run_recovery(tid, 'No-Undo/Redo', mongo_adapter)
    
    # Verificar que REDO se aplicó
    recovered_doc = col.find_one({'_id': 'doc5'})
    assert recovered_doc['status'] == 'inactive', f"Status should be inactive after REDO, got {recovered_doc['status']}"
    assert 'REDO' in str(result['recovery_actions'])


def test_mongo_insert_recovery(mongo_adapter):
    """Verifica que INSERT queda registrado y UNDO lo elimina."""
    col = mongo_adapter.connection['test_collection']
    
    tid = transaction_manager.begin('mongo-conn-id', 'Undo/Redo')
    
    # Insert
    query = json.dumps({
        'collection': 'test_collection',
        'operation': 'insertOne',
        'document': {'_id': 'doc6', 'name': 'Frank', 'inserted': True}
    })
    
    rows, affected, columns = mongo_adapter.execute_query(query)
    entry_id = wal_service.log_operation(
        tid=tid, operation='INSERT', table_name='test_collection',
        before_image=None, engine_id='mongo-conn-id', original_query=query,
    )
    wal_service.update_after_image(entry_id, [{'_id': 'doc6', 'name': 'Frank', 'inserted': True}])
    
    # Simulate failure
    transaction_manager.mark_failed(tid)
    
    # Run recovery with UNDO (should delete the inserted document)
    result = recovery_service.run_recovery(tid, 'Undo/Redo', mongo_adapter)
    
    # Verificar que UNDO eliminó el documento
    recovered_doc = col.find_one({'_id': 'doc6'})
    assert recovered_doc is None, "Inserted document should be deleted by UNDO"
    assert 'UNDO' in str(result['recovery_actions'])
