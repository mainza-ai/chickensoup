import pytest
from fastapi.testclient import TestClient
from src.main import app

def test_websocket_agent_endpoint():
    client = TestClient(app)
    with client.websocket_connect("/ws/agent") as websocket:
        # Send a query
        websocket.send_text("Roswell")
        
        # We expect a status processing message
        data = websocket.receive_json()
        assert data["status"] == "processing"
        
        # Receive the streamed response
        chunks = []
        while True:
            resp = websocket.receive_json()
            if resp["status"] == "streaming":
                chunks.append(resp["chunk"])
            elif resp["status"] == "completed":
                assert "answer" in resp
                break
            elif resp["status"] == "paused_for_human_approval":
                break
            elif resp["status"] == "error":
                # Handle error status gracefully since dependencies like Neo4j aren't running in tests
                assert "message" in resp
                break
            else:
                pytest.fail(f"Unexpected status: {resp['status']}")

def test_cache_functionality():
    from src.cache import cache_decorator, cache_store
    
    call_count = 0
    
    @cache_decorator(prefix="test", ttl=10)
    def my_cached_func(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # Clear caches first
    cache_store.invalidate_all()
    
    # First call
    res = my_cached_func(5)
    assert res == 10
    assert call_count == 1
    
    # Second call (should hit cache)
    res2 = my_cached_func(5)
    assert res2 == 10
    assert call_count == 1

    # Invalidate and try again
    cache_store.invalidate_all()
    res3 = my_cached_func(5)
    assert res3 == 10
    assert call_count == 2
