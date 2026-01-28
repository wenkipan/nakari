# Test Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Establish a TDD-ready testing framework with Redis DB 9-15 isolation for behavior and state verification.

**Architecture:** pytest-based framework with fixtures for DB isolation (9-15), unit tests for individual components, integration tests for end-to-end workflows, CI/CD integration.

**Tech Stack:** pytest, pytest-asyncio, pytest-cov, redis, pytest-mock

---

## Phase 1: Setup and Infrastructure

### Task 1: Create tests directory structure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/redis_fixtures.py`
- Create: `tests/fixtures/persona_fixtures.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_context.py`
- Create: `tests/unit/test_graph_nodes.py`
- Create: `tests/unit/test_persona.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_conversation.py`
- Create: `tests/integration/test_reflection.py`
- Create: `tests/integration/test_persona_switch.py`

**Steps:**

1. Create directory structure
   ```bash
   mkdir -p tests/fixtures tests/unit tests/integration
   touch tests/__init__.py tests/fixtures/__init__.py tests/unit/__init__.py tests/integration/__init__.py
   ```

2. Run to verify structure
   ```bash
   tree tests/
   # Expected:
   # tests/
   # ├── __init__.py
   # ├── conftest.py
   # ├── fixtures/
   # │   ├── __init__.py
   # │   ├── redis_fixtures.py
   # │   └── persona_fixtures.py
   # ├── unit/
   # │   ├── __init__.py
   # │   ├── test_context.py
   # │   ├── test_graph_nodes.py
   # │   └── test_persona.py
   # └── integration/
   #     ├── __init__.py
   #     ├── test_conversation.py
   #     ├── test_reflection.py
   #     └── test_persona_switch.py
   ```

3. Commit
   ```bash
   git add tests/
   git commit -m "chore: create test directory structure"
   ```

---

### Task 2: Add pytest configuration

**Files:**
- Modify: `pytest.ini`

**Steps:**

1. Create pytest.ini
   ```ini
   [pytest]
   markers =
       unit: unit tests (fast, no external deps)
       integration: integration tests
       slow: slow tests (e.g., mocked LLM)

   asyncio_mode = auto
   addopts =
       -v
       --tb=short
       --strict-markers
   ```

2. Verify pytest.ini
   ```bash
   cat pytest.ini
   ```

3. Commit
   ```bash
   git add pytest.ini
   git commit -m "chore: add pytest configuration"
   ```

---

### Task 3: Add test dependencies

**Files:**
- Modify: `requirements.txt`

**Steps:**

1. Add to requirements.txt
   ```txt
   # Test dependencies
   pytest>=7.4.0
   pytest-asyncio>=0.21.0
   pytest-cov>=4.1.0
   pytest-mock>=3.12.0
   ```

2. Verify
   ```bash
   grep -A 4 "Test dependencies" requirements.txt
   ```

3. Commit
   ```bash
   git add requirements.txt
   git commit -m "chore: add test dependencies"
   ```

---

## Phase 2: Core Unit Tests

### Task 4: Implement conftest.py with DB isolation

**Files:**
- Modify: `tests/conftest.py`

**Steps:**

1. Create conftest.py
   ```python
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
   ```

2. Verify
   ```bash
   python -c "import sys; sys.path.insert(0, '.'); from tests import conftest"
   # Should run without errors
   ```

3. Commit
   ```bash
   git add tests/conftest.py
   git commit -m "feat: implement conftest.py with DB isolation"
   ```

---

### Task 5: Implement redis_fixtures.py

**Files:**
- Create: `tests/fixtures/redis_fixtures.py`

**Steps:**

1. Create redis_fixtures.py
   ```python
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
   ```

2. Verify
   ```bash
   python -c "import sys; sys.path.insert(0, '.'); from tests.fixtures.redis_fixtures import mock_redis"
   ```

3. Commit
   ```bash
   git add tests/fixtures/redis_fixtures.py
   git commit -m "feat: add Redis fixtures for testing"
   ```

---

### Task 6: Implement test_context.py

**Files:**
- Create: `tests/unit/test_context.py`

**Steps:**

1. Create test_context.py
   ```python
   import pytest
   from context.manager import ContextManager

   class TestAddMessage:
       """Test ContextManager.add_message() behavior and state"""

       @pytest.fixture
       def ctx(self, db_index):
           """Create ContextManager with isolated Redis DB"""
           redis_url = f"redis://localhost:6379/{db_index}"
           return ContextManager(redis_url=redis_url)

       def test_add_message_creates_key(self, ctx, db_index):
           """Test that add_message creates the correct Redis key"""
           ctx.add_message("s1", "user", "Hello")
           redis_client = redis.Redis(host="localhost", port=6379, db=db_index)
           assert_redis_key_exists(redis_client, "nakari:context:s1")

       def test_add_message_structure(self, ctx):
           """Test that add_message creates proper message structure"""
           ctx.add_message("s1", "user", "Hello", meta={"source": "mic"})

           messages = ctx.get_context("s1")
           assert len(messages) == 1
           assert messages[0]["role"] == "user"
           assert messages[0]["content"] == "Hello"
           assert messages[0]["meta"]["source"] == "mic"

       def test_add_message_increments_count(self, ctx):
           """Test that multiple messages increase context length"""
           ctx.add_message("s1", "user", "M1")
           ctx.add_message("s1", "assistant", "M2")
           ctx.add_message("s1", "user", "M3")

           messages = ctx.get_context("s1")
           assert len(messages) == 3

       def test_add_message_sets_ttl(self, ctx, db_index):
           """Test that add_message sets 24-hour TTL"""
           ctx.add_message("s1", "user", "Hello")

           redis_client = redis.Redis(host="localhost", port=6379, db=db_index)
           ttl = redis_client.ttl("nakari:context:s1")
           assert ttl > 0 and ttl <= 3600 * 24

       def test_get_context_returns_list(self, ctx):
           """Test that get_context returns a list"""
           ctx.add_message("s1", "user", "Hello")
           messages = ctx.get_context("s1")
           assert isinstance(messages, list)

   class TestContextCompression:
       """Test automatic context compression when exceeding limit"""

       @pytest.fixture
       def ctx(self, db_index):
           redis_url = f"redis://localhost:6379/{db_index}"
           return ContextManager(redis_url=redis_url, max_history_len=2)

       def test_compression_removes_old_messages(self, ctx):
           """Test that compression removes oldest messages"""
           ctx.add_message("s1", "user", "M1")
           ctx.add_message("s1", "assistant", "M2")
           ctx.add_message("s1", "user", "M3")  # Should trigger compression

           messages = ctx.get_context("s1")
           assert len(messages) == 2

       def test_compression_keeps_newest(self, ctx):
           """Test that compression keeps the newest messages"""
           ctx.add_message("s1", "user", "M1")
           ctx.add_message("s1", "assistant", "M2")
           ctx.add_message("s1", "user", "M3")  # Should trigger compression

           messages = ctx.get_context("s1")
           assert messages[0]["content"] == "M3"
           assert messages[1]["content"] == "M2"

   class TestInsights:
       """Test long-term insight storage"""

       @pytest.fixture
       def ctx(self, db_index):
           redis_url = f"redis://localhost:6379/{db_index}"
           return ContextManager(redis_url=redis_url)

       def test_save_insight(self, ctx):
           """Test that save_insight stores insight correctly"""
           ctx.save_insight("s1", "User likes cats")

           insights = ctx.get_insights("s1")
           assert len(insights) == 1
           assert insights[0] == "User likes cats"

       def test_get_insights_with_limit(self, ctx):
           """Test that get_insights respects limit parameter"""
           ctx.save_insight("s1", "I1")
           ctx.save_insight("s1", "I2")
           ctx.save_insight("s1", "I3")

           insights = ctx.get_insights("s1", limit=2)
           assert len(insights) == 2

       def test_get_insights_order(self, ctx):
           """Test that get_insights returns newest first"""
           ctx.save_insight("s1", "I1")
           ctx.save_insight("s1", "I2")
           ctx.save_insight("s1", "I3")

           insights = ctx.get_insights("s1")
           assert insights[0] == "I3"
           assert insights[1] == "I2"
           assert insights[2] == "I1"

       def test_get_insights_empty(self, ctx):
           """Test that get_insights returns empty list for no insights"""
           insights = ctx.get_insights("s1")
           assert insights == []

   class TestPersona:
       """Test persona storage and retrieval"""

       @pytest.fixture
       def ctx(self, db_index):
           redis_url = f"redis://localhost:6379/{db_index}"
           return ContextManager(redis_url=redis_url)

       def test_set_active_persona(self, ctx):
           """Test that set_active_persona stores persona name"""
           ctx.set_active_persona("s1", "test_persona")

           persona = ctx.get_active_persona("s1")
           assert persona == "test_persona"

       def test_get_active_persona_default(self, ctx):
           """Test that get_active_persona returns default when not set"""
           persona = ctx.get_active_persona("s1")
           assert persona == "default"

       def test_set_persona_template(self, ctx):
           """Test that set_persona_template stores template"""
           template = {"name": "TestBot", "traits": ["Fast", "Precise"]}
           ctx.set_persona_template("test_bot", template)

           retrieved = ctx.get_persona_template("test_bot")
           assert retrieved == template

       def test_get_persona_template_not_found(self, ctx):
           """Test that get_persona_template returns None for missing template"""
           retrieved = ctx.get_persona_template("nonexistent")
           assert retrieved is None

   class TestClearContext:
       """Test context clearing functionality"""

       @pytest.fixture
       def ctx(self, db_index):
           redis_url = f"redis://localhost:6379/{db_index}"
           return ContextManager(redis_url=redis_url)

       def test_clear_context(self, ctx):
           """Test that clear_context removes all context"""
           ctx.add_message("s1", "user", "M1")
           ctx.add_message("s2", "user", "M2")
           ctx.clear_context("s1")

           assert len(ctx.get_context("s1")) == 0
           assert len(ctx.get_context("s2")) == 1
   ```

2. Verify
   ```bash
   pytest tests/unit/test_context.py -v
   # Expected: No tests to run (Redis not running), but syntax valid
   ```

3. Commit
   ```bash
   git add tests/unit/test_context.py
   git commit -m "feat: add ContextManager unit tests"
   ```

---

### Task 7: Implement test_graph_nodes.py

**Files:**
- Create: `tests/unit/test_graph_nodes.py`

**Steps:**

1. Create test_graph_nodes.py
   ```python
   import pytest
   from unittest.mock import patch, MagicMock

   @patch('context.manager.context_manager')
   @patch('utils.persona.persona_loader')
   def test_retrieve_memory_calls_persona(mock_loader, mock_cm):
       """Test that retrieve_memory loads and formats persona"""
       mock_cm.get_active_persona.return_value = "test_persona"
       mock_loader.load_persona.return_value = {
           "name": "TestBot",
           "bio": "A test bot",
           "traits": ["Friendly"],
           "core_beliefs": ["Test"]
       }

       from llm.graph import retrieve_long_term_memory
       state = {"user_id": "u1", "messages": []}

       result = retrieve_long_term_memory(state)

       mock_cm.get_active_persona.assert_called_once_with("u1")
       mock_loader.load_persona.assert_called_once_with("test_persona")
       assert len(result["messages"]) == 1
       assert isinstance(result["messages"][0].type, str)

   def test_manage_context_trims_messages():
       """Test that manage_context trims context appropriately"""
       from llm.graph import manage_context
       from langchain_core.messages import HumanMessage, AIMessage

       state = {
           "messages": [
               HumanMessage(content="M1"),
               AIMessage(content="M2"),
               HumanMessage(content="M3"),
               AIMessage(content="M4"),
               HumanMessage(content="M5"),
           ]
       }

       result = manage_context(state)

       assert "context_window" in result
       # Should keep last messages, not exceed max_tokens
       assert len(result["context_window"]) <= 5

   @patch('llm.graph.llm')
   def test_generate_response_with_reflection(mock_llm):
       """Test that generate_response detects [[REFLECT]] signal"""
       from llm.graph import generate_response
       from langchain_core.messages import HumanMessage, AIMessage

       mock_response = AIMessage(content="[[REFLECT]] Response text")
       mock_llm.invoke.return_value = mock_response

       state = {"context_window": [], "messages": []}

       result = generate_response(state)

       assert result["should_reflect"] is True
       assert "[[REFLECT]]" not in result["response"]
       assert result["response"] == "Response text"

   @patch('llm.graph.llm')
   def test_generate_response_without_reflection(mock_llm):
       """Test that generate_response works without reflection signal"""
       from llm.graph import generate_response
       from langchain_core.messages import HumanMessage, AIMessage

       mock_response = AIMessage(content="Normal response")
       mock_llm.invoke.return_value = mock_response

       state = {"context_window": [], "messages": []}

       result = generate_response(state)

       assert result["should_reflect"] is False
       assert result["response"] == "Normal response"

   @patch('llm.graph.llm')
   def test_generate_response_handles_error(mock_llm):
       """Test that generate_response handles errors gracefully"""
       from llm.graph import generate_response

       mock_llm.invoke.side_effect = Exception("LLM error")

       state = {"context_window": [], "messages": []}

       result = generate_response(state)

       assert result["response"] is not None
       assert "sorry" in result["response"].lower()
   ```

2. Verify
   ```bash
   pytest tests/unit/test_graph_nodes.py -v
   # Expected: PASS
   ```

3. Commit
   ```bash
   git add tests/unit/test_graph_nodes.py
   git commit -m "feat: add LangGraph node tests"
   ```

---

### Task 8: Implement test_persona.py

**Files:**
- Create: `tests/unit/test_persona.py`

**Steps:**

1. Create test_persona.py
   ```python
   import os
   import tempfile
   from unittest.mock import patch

   def test_persona_loader_loads_yaml():
       """Test that persona loader reads YAML correctly"""
       from utils.persona import PersonaLoader

       with tempfile.TemporaryDirectory() as tmpdir:
           persona_path = os.path.join(tmpdir, "test.yaml")
           persona_content = """
           name: TestBot
           bio: A test bot
           traits:
             - Fast
             - Precise
           core_beliefs:
             - Testing is life
           tone: Friendly
           """
           with open(persona_path, "w") as f:
               f.write(persona_content)

           loader = PersonaLoader(personas_dir=tmpdir)
           data = loader.load_persona("test")

           assert data["name"] == "TestBot"
           assert data["bio"] == "A test bot"
           assert data["traits"] == ["Fast", "Precise"]
           assert data["core_beliefs"] == ["Testing is life"]
           assert data["tone"] == "Friendly"

   def test_persona_loader_format_prompt():
       """Test that persona prompt is formatted correctly"""
       from utils.persona import PersonaLoader

       persona_data = {
           "name": "TestBot",
           "bio": "A test bot",
           "traits": ["Fast", "Precise"],
           "core_beliefs": ["Testing is life"],
           "tone": "Friendly"
       }

       loader = PersonaLoader()
       prompt = loader.format_persona_prompt(persona_data)

       assert "You are TestBot" in prompt
       assert "A test bot" in prompt
       assert "Fast" in prompt
       assert "Testing is life" in prompt

   @patch('utils.persona.persona_loader')
   def test_persona_loader_with_missing_yaml(mock_loader):
       """Test fallback when persona YAML is missing"""
       from utils.persona import PersonaLoader

       loader = PersonaLoader()

       result = loader.load_persona("nonexistent")

       assert result is None

   def test_persona_loader_invalid_yaml():
       """Test that invalid YAML returns None"""
       from utils.persona import PersonaLoader

       with tempfile.TemporaryDirectory() as tmpdir:
           persona_path = os.path.join(tmpdir, "invalid.yaml")
           invalid_content = "{ invalid yaml: [unclosed"
           with open(persona_path, "w") as f:
               f.write(invalid_content)

           loader = PersonaLoader(personas_dir=tmpdir)
           result = loader.load_persona("invalid")

           assert result is None
   ```

2. Verify
   ```bash
   pytest tests/unit/test_persona.py -v
   # Expected: PASS
   ```

3. Commit
   ```bash
   git add tests/unit/test_persona.py
   git commit -m "feat: add PersonaLoader tests"
   ```

---

## Phase 3: Integration Tests

### Task 9: Implement test_conversation.py

**Files:**
- Create: `tests/integration/test_conversation.py`

**Steps:**

1. Create test_conversation.py
   ```python
   import pytest
   import redis

   @pytest.mark.integration
   def test_full_conversation_flow(db_index):
       """Test complete conversation from user input to LLM response"""
       from context.manager import ContextManager
       from llm.graph import retrieve_long_term_memory, manage_context, generate_response
       from langchain_core.messages import HumanMessage

       redis_url = f"redis://localhost:6379/{db_index}"
       ctx = ContextManager(redis_url=redis_url)

       # Setup
       state = {
           "user_id": "conv_test",
           "messages": [HumanMessage(content="Hello, who are you?")],
           "context_window": []
       }

       # Execute: retrieve_memory
       state = retrieve_long_term_memory(state)
       assert len(state["messages"]) == 1
       assert isinstance(state["messages"][0].type, str)

       # Execute: manage_context
       state = manage_context(state)
       assert "context_window" in state
       assert len(state["context_window"]) <= 5

       # Execute: generate_response
       state = generate_response(state)
       assert state["response"] is not None
       assert len(state["response"]) > 0

       # Verify context is saved
       messages = ctx.get_context("conv_test")
       assert len(messages) > 0

   @pytest.mark.integration
   def test_isolation_across_conversations(db_index):
       """Test that conversations in different DBs remain isolated"""
       from context.manager import ContextManager

       ctx1 = ContextManager(redis_url=f"redis://localhost:6379/{db_index}")
       ctx2 = ContextManager(redis_url=f"redis://localhost:6379/{db_index + 1}")

       ctx1.add_message("session1", "user", "Hello from DB9")
       ctx2.add_message("session1", "user", "Hello from DB10")

       # DB9 should only have its messages
       db9_messages = ctx1.get_context("session1")
       assert len(db9_messages) == 1
       assert db9_messages[0]["content"] == "Hello from DB9"

       # DB10 should only have its messages
       db10_messages = ctx2.get_context("session1")
       assert len(db10_messages) == 1
       assert db10_messages[0]["content"] == "Hello from DB10"
   ```

2. Verify
   ```bash
   pytest tests/integration/test_conversation.py -v -m integration
   # Expected: PASS (requires Redis running)
   ```

3. Commit
   ```bash
   git add tests/integration/test_conversation.py
   git commit -m "feat: add conversation flow integration tests"
   ```

---

### Task 10: Implement test_reflection.py

**Files:**
- Create: `tests/integration/test_reflection.py`

**Steps:**

1. Create test_reflection.py
   ```python
   import pytest
   from unittest.mock import patch

   @pytest.mark.integration
   @patch('context.manager.context_manager')
   @patch('llm.graph.llm')
   def test_reflection_signal_flow(mock_llm, mock_cm, db_index):
       """Test that [[REFLECT]] signal is detected and processed"""
       from llm.graph import retrieve_long_term_memory, generate_response

       # Mock LLM to return reflection signal
       mock_llm.invoke.return_value.content = "[[REFLECT]] I should remember this"

       # Setup state
       state = {
           "user_id": "reflection_test",
           "messages": [],
           "context_window": []
       }

       # Execute: generate should detect signal
       result = generate_response(state)

       assert result["should_reflect"] is True
       assert "[[REFLECT]]" not in result["response"]

       # Execute: save_insight should be called (mock implementation)
       ctx = ContextManager(redis_url=f"redis://localhost:6379/{db_index}")
       ctx.save_insight("reflection_test", "I should remember this")
       insights = ctx.get_insights("reflection_test")
       assert len(insights) == 1
   ```

2. Verify
   ```bash
   pytest tests/integration/test_reflection.py -v -m integration
   # Expected: PASS
   ```

3. Commit
   ```bash
   git add tests/integration/test_reflection.py
   git commit -m "feat: add reflection signal integration tests"
   ```

---

### Task 11: Implement test_persona_switch.py

**Files:**
- Create: `tests/integration/test_persona_switch.py`

**Steps:**

1. Create test_persona_switch.py
   ```python
   import pytest
   import tempfile
   import os
   from unittest.mock import patch

   @pytest.mark.integration
   def test_persona_switch_isolation(db_index):
       """Test that persona switching works across sessions"""
       from context.manager import ContextManager
       from utils.persona import PersonaLoader

       redis_url = f"redis://localhost:6379/{db_index}"
       ctx = ContextManager(redis_url=redis_url)

       # Setup two personas
       with tempfile.TemporaryDirectory() as tmpdir:
           persona1 = os.path.join(tmpdir, "persona1.yaml")
           with open(persona1, "w") as f:
               f.write("""
               name: Alice
               bio: A friendly bot
               traits: [Friendly, Talkative]
               core_beliefs: [Love to chat]
               tone: Warm
               """)

           persona2 = os.path.join(tmpdir, "persona2.yaml")
           with open(persona2, "w") as f:
               f.write("""
               name: Bob
               bio: A serious bot
               traits: [Serious, Concise]
               core_beliefs: [Get to the point]
               tone: Formal
               """)

           loader = PersonaLoader(personas_dir=tmpdir)

           # Switch to Alice
           ctx.set_active_persona("s1", "persona1")
           ctx.save_insight("s1", "Alice likes talking")

           # Verify Alice is active
           persona = ctx.get_active_persona("s1")
           assert persona == "persona1"

           # Verify insights are saved
           insights = ctx.get_insights("s1")
           assert len(insights) == 1

           # Switch to Bob in different session
           ctx.set_active_persona("s2", "persona2")

           # Verify Bob is active for s2
           persona = ctx.get_active_persona("s2")
           assert persona == "persona2"

           # Verify s1 still has Alice
           persona = ctx.get_active_persona("s1")
           assert persona == "persona1"
   ```

2. Verify
   ```bash
   pytest tests/integration/test_persona_switch.py -v -m integration
   # Expected: PASS
   ```

3. Commit
   ```bash
   git add tests/integration/test_persona_switch.py
   git commit -m "feat: add persona switching integration tests"
   ```

---

## Phase 4: CI/CD Integration

### Task 12: Create GitHub Actions workflow

**Files:**
- Create: `.github/workflows/test.yml`

**Steps:**

1. Create workflow directory and file
   ```bash
   mkdir -p .github/workflows
   ```

2. Create test.yml
   ```yaml
   name: Tests

   on:
     push:
       branches: [core, main]
     pull_request:
       branches: [core, main]

   jobs:
     test:
       runs-on: ubuntu-latest

       services:
         redis:
           image: redis:7-alpine
           ports:
             - 6379:6379
           options: >-
             --health-cmd "redis-cli ping"
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5

       steps:
         - uses: actions/checkout@v4

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.10'

         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
             pip install pytest pytest-asyncio pytest-cov pytest-mock redis

         - name: Run unit tests
           run: |
             pytest tests/unit -v --cov=.context --cov=llm --cov=utils --cov-report=term-missing

         - name: Run integration tests
           run: |
             pytest tests/integration -v --cov=.context --cov=llm --cov=utils --cov-report=term-missing -m integration
   ```

3. Verify
   ```bash
   cat .github/workflows/test.yml
   ```

4. Commit
   ```bash
   git add .github/workflows/test.yml
   git commit -m "feat: add GitHub Actions CI/CD workflow"
   ```

---

## Phase 5: Final Verification

### Task 13: Run all tests and verify coverage

**Steps:**

1. Run unit tests
   ```bash
   pytest tests/unit -v
   # Expected: PASS, all tests passing
   ```

2. Run integration tests (requires Redis)
   ```bash
   redis-server --daemonize yes
   pytest tests/integration -v -m integration
   # Expected: PASS
   ```

3. Run coverage report
   ```bash
   pytest --cov=.context --cov=llm --cov=utils --cov-report=html
   open htmlcov/index.html
   ```

4. Verify core modules coverage
   ```bash
   grep -A 5 "context/manager.py" htmlcov/index.html
   # Check coverage >= 90%
   ```

5. Commit
   ```bash
   git add ./
   git commit -m "feat: complete test framework implementation"
   ```

---

## Summary

This implementation plan establishes a comprehensive testing framework with:

1. **DB Isolation**: Tests use Redis DB 9-15 for complete isolation
2. **Behavior Verification**: Mock dependencies to verify function calls
3. **State Verification**: Assert Redis state after operations
4. **Test Organization**: Unit tests for components, integration tests for workflows
5. **CI/CD**: GitHub Actions workflow for automated testing

**Total Tasks**: 13
**Estimated Time**: 2-3 hours

---

**Plan complete. Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
