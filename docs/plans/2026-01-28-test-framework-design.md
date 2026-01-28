# Test Framework Design

**Date:** 2026-01-28
**Topic:** Establish TDD-ready testing framework for Nakari

## Overview

Create a comprehensive testing framework that supports both behavior verification (mock dependencies) and state verification (Redis data). The framework uses Redis database indexing (DB 9-15) for test isolation.

## Requirements

### Core Requirements
1. **Behavior Verification**: Mock dependencies (Redis/Celery/LLM), verify function calls, parameters, and return formats
2. **State Verification**: Verify system state (Redis data, session state) after multi-step operations
3. **Test Isolation**: Each test has independent Redis state without manual cleanup
4. **TDD Readiness**: Automated validation with clear pass/fail criteria

### Constraints
- Use Redis DB 9-15 for test isolation
- Support both unit and integration tests
- Minimize dependencies on external services during unit tests

## Architecture

### Test Infrastructure

#### 1. Configuration
- **pytest.ini**: Test configuration and markers
- **conftest.py**: Global fixtures and DB isolation setup

#### 2. DB Index Strategy

| Test Level | Redis DB | Range | Purpose |
|------------|----------|-------|---------|
| Function | DB i | 9-15 | Complete isolation, auto-cleanup via new DB |
| Class | DB i | 9-15 | Shared within class, isolated from other classes |
| Session | DB i | 9-15 | Optional sharing for stable resources (persona files) |

#### 3. Fixtures

**Core Fixtures:**
- `db_index`: Random DB assignment (9-15) per function/class
- `ctx`: ContextManager instance with isolated Redis connection
- `clean_redis_state`: (Alternative: not needed with DB isolation, can remove)

**Mock Fixtures:**
- `mock_redis`: Redis client instance
- `mock_persona`: Persona loader with test data
- `mock_llm`: ChatOpenAI mock for LangGraph tests

**State Verification:**
- `assert_redis_state()`: Validate key-value pairs
- `assert_redis_key_exists()`: Validate key presence
- `assert_redis_key_not_exists()`: Validate key absence

### Test Organization

```
tests/
├── conftest.py              # Global fixtures & DB isolation
├── fixtures/
│   ├── redis_fixtures.py    # Redis mock & DB index fixtures
│   └── persona_fixtures.py  # Persona file loader
├── unit/
│   ├── test_context.py      # ContextManager tests
│   ├── test_graph_nodes.py  # LangGraph node tests
│   └── test_persona.py      # Persona loader tests
├── integration/
│   ├── test_conversation.py # End-to-end conversation flow
│   ├── test_reflection.py   # Reflection signal flow
│   └── test_persona_switch.py # Persona switching
└── __init__.py
```

### Test Categories

#### 1. Unit Tests (Fast, No External Deps)
- Core function logic
- Mock all dependencies
- Fast execution (<1s per test)

#### 2. Integration Tests (May Need Redis)
- Component interaction
- Redis state verification
- Complete workflows

#### 3. Performance Tests (Optional)
- Redis latency benchmarks
- LLM response time
- Context window processing

## Implementation Plan

### Phase 1: Setup and Infrastructure
1. Create `tests/` directory structure
2. Add `pytest.ini` configuration
3. Create `conftest.py` with DB isolation fixtures
4. Add dependencies to `requirements.txt`

### Phase 2: Core Unit Tests
1. Implement `tests/fixtures/redis_fixtures.py`
2. Implement `tests/unit/test_context.py`
3. Implement `tests/unit/test_graph_nodes.py`
4. Implement `tests/unit/test_persona.py`

### Phase 3: Integration Tests
1. Implement `tests/integration/test_conversation.py`
2. Implement `tests/integration/test_reflection.py`
3. Implement `tests/integration/test_persona_switch.py`

### Phase 4: CI/CD Integration
1. Add GitHub Actions workflow
2. Configure test coverage reporting
3. Add pre-commit hooks

### Phase 5: Documentation
1. Update README with testing guide
2. Document test patterns and conventions
3. Create troubleshooting guide

## Test Coverage Targets

| Module | Target Coverage | Notes |
|--------|-----------------|-------|
| `context/manager.py` | 90%+ | Core storage logic |
| `llm/graph.py` | 85%+ | Workflow nodes |
| `utils/persona.py` | 80%+ | Loading logic |
| `tasks/` | 70%+ | Celery tasks |

## Redis DB Isolation Details

### Test Execution
```python
@pytest.fixture(scope="function")
def db_index():
    """Assign random DB index between 9-15"""
    return random.randint(9, 15)

@pytest.fixture
def ctx(db_index):
    """ContextManager with isolated Redis connection"""
    redis_url = f"redis://localhost:6379/{db_index}"
    return ContextManager(redis_url=redis_url)
```

### Usage Example
```python
def test_add_message(db_index, ctx):
    # Test runs in isolated DB
    ctx.add_message("s1", "user", "Hello")

    # Verify isolation
    other_ctx = ContextManager(redis_url="redis://localhost:6379/0")
    assert "nakari:context:s1" not in other_ctx.redis.keys()
```

### Debugging
```bash
# View test data in specific DB
redis-cli -n 12

# List all test DBs
redis-cli --scan --pattern "nakari:context:*" -n 9
redis-cli --scan --pattern "nakari:context:*" -n 10
# ... etc
```

## Dependencies

```txt
# requirements.txt (new)
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
redis>=5.0.0
pytest-mock>=3.12.0
```

## Success Criteria

1. All new code changes include corresponding tests
2. Test execution completes in <30s
3. Code coverage >80% for core modules
4. CI pipeline passes on all PRs
5. Zero test flakiness after 100 runs
