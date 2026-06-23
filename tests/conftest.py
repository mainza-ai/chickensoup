import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def mock_neo4j():
    with patch("src.main.neo4j_conn") as mock_conn:
        mock_driver = MagicMock()
        mock_conn.connect.return_value = mock_driver
        mock_conn.get_driver.return_value = mock_driver
        mock_conn.check_health.return_value = True
        yield mock_conn

@pytest.fixture(autouse=True)
def mock_redis():
    with patch("redis.from_url") as mock_from_url:
        mock_r = MagicMock()
        mock_r.ping.return_value = True
        
        # Implement a basic in-memory dict backend for Redis mock
        store = {}
        def mock_get(key):
            return store.get(key)
        def mock_set(key, val, ex=None):
            store[key] = val
            return True
        def mock_delete(*keys):
            count = 0
            for k in keys:
                if k in store:
                    del store[k]
                    count += 1
            return count
        def mock_keys(pattern):
            import fnmatch
            # Simple conversion of redis glob pattern to fnmatch
            return [k for k in store.keys() if fnmatch.fnmatch(k, pattern)]
            
        mock_r.get.side_effect = mock_get
        mock_r.set.side_effect = mock_set
        mock_r.delete.side_effect = mock_delete
        mock_r.keys.side_effect = mock_keys
        
        mock_from_url.return_value = mock_r
        
        # Force cache_store to re-initialize during testing so it uses this mock
        from src.cache import cache_store
        cache_store._initialize()
        
        yield mock_from_url

@pytest.fixture
def client():
    from src.main import app
    with TestClient(app) as c:
        yield c
