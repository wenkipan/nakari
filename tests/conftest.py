"""pytest configuration for the tests directory."""

import pytest
import redis

# Redis DB indices for isolation
DB_INDEXES = range(9, 16)

@pytest.fixture(scope="class", params=DB_INDEXES)
def db_index(request):
    """Assign random DB index between 9-15 for class-level isolation"""
    return request.param

# Mock Redis URL fixture for unit tests
@pytest.fixture
def mock_redis_url():
    """Provide a Redis URL for ContextManager (DB 9 for isolation)"""
    return "redis://localhost:6379/9"

# Persona fixtures
@pytest.fixture
def mock_persona():
    """Mock persona data for testing"""
    return {
        "name": "Helpful Assistant",
        "traits": ["friendly", "knowledgeable"],
        "style": "conversational",
    }

# Mock persona loader fixture
@pytest.fixture
def mock_persona_loader():
    """Mock persona_loader for testing"""
    from unittest.mock import MagicMock
    return MagicMock()

# Mock context manager fixture
@pytest.fixture
def mock_context_manager():
    """Mock context_manager for testing"""
    from unittest.mock import MagicMock
    return MagicMock()

# Mock Redis client fixture
@pytest.fixture
def mock_redis():
    """Create an in-memory Redis client for testing"""
    import redis
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.flushdb()
    yield r
    r.flushdb()

# Redis state assertion helpers
def assert_redis_state(redis_client, expected_keys: dict):
    """Validate Redis DB state against expected key-value pairs"""
    for key, expected_value in expected_keys.items():
        actual_value = redis_client.get(key)
        assert actual_value == expected_value, f"Key {key}: expected {expected_value}, got {actual_value}"

def assert_redis_key_exists(redis_client, key: str):
    """Assert a key exists in Redis"""
    assert redis_client.exists(key), f"Key {key} should exist"

def assert_redis_key_not_exists(redis_client, key: str):
    """Assert a key does not exist in Redis"""
    assert not redis_client.exists(key), f"Key {key} should not exist"
