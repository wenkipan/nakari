import random
from typing import Dict

import pytest

# Test markers registration
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: unit tests (fast, no external deps)"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: slow tests (e.g., mocked LLM)"
    )

@pytest.fixture(scope="function")
def db_index():
    """Assign random DB index between 9-15 for function-level isolation"""
    return random.randint(9, 15)

@pytest.fixture(scope="class")
def db_index_class(cls):
    """Assign random DB index between 9-15 for class-level isolation"""
    return random.randint(9, 15)

def assert_redis_state(redis_client, expected_keys: Dict[str, str]):
    """Validate Redis DB state against expected key-value pairs"""
    for key, expected_value in expected_keys.items():
        actual_value = redis_client.get(key)
        assert actual_value == expected_value, \
            f"Key {key}: expected {expected_value}, got {actual_value}"

def assert_redis_key_exists(redis_client, key: str):
    """Assert a key exists in Redis"""
    assert redis_client.exists(key), f"Key {key} should exist"

def assert_redis_key_not_exists(redis_client, key: str):
    """Assert a key does not exist in Redis"""
    assert not redis_client.exists(key), f"Key {key} should not exist"
