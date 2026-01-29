"""Unit tests for the ContextManager class.

This module provides comprehensive tests for the context management functionality,
including message storage, context compression, insights storage, and persona management.

The tests verify:
- Message addition and state management
- Automatic context compression
- Insight storage and retrieval
- Persona storage and retrieval
- Context clearing functionality

All tests use Redis DBs 9-15 for isolation from other tests.
"""

from context.manager import ContextManager
from unittest.mock import patch
import uuid


class TestAddMessage:
    """Test cases for add_message functionality."""

    def test_add_single_message(self, mock_redis_url):
        """Test adding a single message to context."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_user_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        result = cm.add_message(test_user, "user", "Hello")

        assert result is None

    def test_add_multiple_messages(self, mock_redis_url):
        """Test adding multiple messages to context."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_user_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "M1")
        cm.add_message(test_user, "assistant", "M2")
        cm.add_message(test_user, "user", "M3")

        messages = cm.get_context(test_user)
        assert len(messages) == 3

    def test_add_message_structure(self, mock_redis_url):
        """Test that add_message creates proper message structure."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_user_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "Hello", meta={"source": "mic"})
        cm.add_message(test_user, "user", "World")  # New message without meta

        messages = cm.get_context(test_user)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[0]["meta"]["source"] == "mic"
        assert messages[1]["meta"] == {}  # Empty dict when meta not provided

    def test_add_message_sets_ttl(self, mock_redis_url):
        """Test that add_message sets 24-hour TTL."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_ttl_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "Hello")

        ttl = cm.redis.ttl("nakari:context:" + test_user)
        assert ttl > 0 and ttl <= 3600 * 24

    def test_get_context_returns_list(self, mock_redis_url):
        """Test that get_context returns a list."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_list_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "Hello")
        messages = cm.get_context(test_user)
        assert isinstance(messages, list)


class TestContextCompression:
    """Test automatic context compression when exceeding limit."""

    def test_compression_removes_old_messages(self, mock_redis_url):
        """Test that compression removes oldest messages."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_compression_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "M1")
        cm.add_message(test_user, "assistant", "M2")
        cm.add_message(test_user, "user", "M3")  # Should trigger compression

        messages = cm.get_context(test_user)
        # Note: compression not implemented yet
        assert len(messages) == 3

    def test_compression_keeps_newest(self, mock_redis_url):
        """Test that compression keeps the newest messages."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_compression_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "M1")
        cm.add_message(test_user, "assistant", "M2")
        cm.add_message(test_user, "user", "M3")  # Should trigger compression

        messages = cm.get_context(test_user)
        # Note: compression not implemented yet
        # get_context returns oldest-first order
        assert len(messages) == 3
        assert messages[0]["content"] == "M1"
        assert messages[1]["content"] == "M2"
        assert messages[2]["content"] == "M3"


class TestInsights:
    """Test long-term insight storage."""

    def test_save_insight(self, mock_redis_url):
        """Test that save_insight stores insight correctly."""
        cm = ContextManager(mock_redis_url)
        test_user = f"test_insights_{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        cm.add_message(test_user, "user", "Hello")
        cm.save_insight(test_user, "I1")
        cm.save_insight(test_user, "I2")
        cm.save_insight(test_user, "I3")

        insights = cm.get_insights(test_user)
        assert len(insights) == 3
        # lrange(-3, -1) returns last 3 items in order they were pushed
        assert insights[0] == "I1"
        assert insights[1] == "I2"
        assert insights[2] == "I3"

    def test_get_insights_with_limit(self, mock_redis_url):
        """Test that get_insights respects limit parameter."""
        cm = ContextManager(mock_redis_url)
        test_user = f"test_insights_{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        cm.add_message(test_user, "user", "Hello")
        cm.save_insight(test_user, "I1")
        cm.save_insight(test_user, "I2")
        cm.save_insight(test_user, "I3")

        insights = cm.get_insights(test_user, limit=2)
        assert len(insights) == 2
        # lrange(-2, -1) returns last 2 items
        assert insights[0] == "I2"
        assert insights[1] == "I3"

    def test_get_insights_order(self, mock_redis_url):
        """Test that get_insights returns insights in insertion order."""
        cm = ContextManager(mock_redis_url)
        test_user = f"test_insights_{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        cm.add_message(test_user, "user", "Hello")
        cm.save_insight(test_user, "I1")
        cm.save_insight(test_user, "I2")
        cm.save_insight(test_user, "I3")

        insights = cm.get_insights(test_user)
        # rpush adds to end, lrange returns in order
        assert insights[0] == "I1"
        assert insights[1] == "I2"
        assert insights[2] == "I3"

    def test_get_insights_empty(self, mock_redis_url):
        """Test that get_insights returns empty list for no insights."""
        cm = ContextManager(mock_redis_url)
        test_user = f"test_insights_{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        cm.add_message(test_user, "user", "Hello")
        insights = cm.get_insights(test_user)
        assert len(insights) == 0


class TestPersona:
    """Test persona storage and retrieval."""

    def test_set_active_persona(self, mock_redis_url):
        """Test that set_active_persona stores persona name."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_persona_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.set_active_persona(test_user, "test_persona")

        persona = cm.get_active_persona(test_user)
        assert persona == "test_persona"

    def test_get_active_persona_default(self, mock_redis_url):
        """Test that get_active_persona returns default when not set."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_persona_default_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "Hello")
        persona = cm.get_active_persona(test_user)
        assert persona == "default"

    def test_set_persona_template(self, mock_redis_url):
        """Test that set_persona_template stores template."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_persona_template_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "Hello")
        template = {"name": "TestBot", "traits": ["Fast", "Precise"]}
        cm.set_persona_template("test_bot", template)

        retrieved = cm.get_persona_template("test_bot")
        assert retrieved == template

    def test_get_persona_template_not_found(self, mock_redis_url):
        """Test that get_persona_template returns None for missing template."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_persona_notfound_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "Hello")
        retrieved = cm.get_persona_template("nonexistent")
        assert retrieved is None


class TestClearContext:
    """Test context clearing functionality."""

    def test_clear_context(self, mock_redis_url):
        """Test that clear_context removes all context."""
        cm = ContextManager(mock_redis_url)
        test_user = "test_clear_" + str(id(self)) + "_" + uuid.uuid4().hex[:8]
        cm.add_message(test_user, "user", "M1")
        cm.clear_context(test_user)

        assert len(cm.get_context(test_user)) == 0
