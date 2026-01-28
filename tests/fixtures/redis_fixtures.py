import pytest
import redis

@pytest.fixture
def mock_redis():
    """Create an in-memory Redis client for testing"""
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.flushdb()
    yield r
    r.flushdb()

@pytest.fixture
def clean_redis_state():
    """
    Fixture to clean Redis state before/after test.
    Note: In production, use DB isolation instead of this fixture.
    """
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.flushdb()
    yield r
    r.flushdb()
