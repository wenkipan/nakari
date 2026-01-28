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

from unittest.mock import patch
from context.manager import ContextManager


class TestAddMessage:
    """Test cases for add_message functionality."""

    def test_add_single_message(self, mock_redis):
        """Test adding a single message to context."""
        cm = ContextManager(mock_redis)
        result = cm.add_message("user", "Hello")

        assert result is True
        assert mock_redis.lpush.assert_called_once_with("context:user", "Hello")
        assert mock_redis.lpush.assert_called_with("context:user", "user")

    def test_add_multiple_messages(self, mock_redis):
        """Test adding multiple messages to context."""
        cm = ContextManager(mock_redis)
        result = cm.add_message("assistant", "How can I help you?")

        assert result is True
        assert mock_redis.lpush.call_count == 2
        assert mock_redis.lpush.call_args_list == [
            (("context:user", "user"), {}),
            (("context:user", "How can I help you?"), {}),
        ]

    def test_add_message_with_long_content(self, mock_redis):
        """Test adding a message with long content that triggers compression."""
        cm = ContextManager(mock_redis)
        long_message = "This is a very long message that exceeds the context limit and will trigger compression." * 10

        result = cm.add_message("user", long_message)

        assert result is True
        assert mock_redis.llen("context:user") == 2  # User + compressed summary
        assert "compressed" in mock_redis.lindex("context:user", 0).decode("utf-8").lower()

    def test_add_message_to_different_user(self, mock_redis):
        """Test adding messages to different user contexts."""
        cm = ContextManager(mock_redis)

        cm.add_message("user1", "Hello user 1")
        cm.add_message("user2", "Hello user 2")

        assert mock_redis.llen("context:user1") == 2
        assert mock_redis.llen("context:user2") == 2
        assert mock_redis.lindex("context:user1", 0).decode("utf-8") == "user1"
        assert mock_redis.lindex("context:user2", 0).decode("utf-8") == "user2"

    def test_add_message_after_compression(self, mock_redis):
        """Test adding messages after context has been compressed."""
        cm = ContextManager(mock_redis)

        # Add enough messages to trigger compression
        for i in range(15):
            cm.add_message("user", f"Message {i}")

        # Add a new message after compression
        cm.add_message("user", "New message after compression")

        # Verify the message was added
        assert mock_redis.lpush("context:user", "New message after compression") is True


class TestContextCompression:
    """Test cases for automatic context compression."""

    def test_compression_threshold(self, mock_redis):
        """Test that compression happens at the threshold."""
        cm = ContextManager(mock_redis)

        # Add messages up to the compression threshold
        for i in range(10):
            cm.add_message("user", f"Message {i}")

        # Add one more message to trigger compression
        cm.add_message("user", "Trigger message")

        # Verify compression occurred
        assert mock_redis.lindex("context:user", 0).decode("utf-8") == "compressed"

    def test_compresses_to_summary(self, mock_redis):
        """Test that compressed context is replaced by a summary."""
        cm = ContextManager(mock_redis)

        # Add multiple messages
        for i in range(12):
            cm.add_message("user", f"Message {i}")

        # Get the compressed summary
        compressed = mock_redis.lindex("context:user", 0).decode("utf-8")

        # Verify it's a summary message
        assert len(compressed) > 0
        assert "compressed" in compressed.lower()
        assert "original_messages" in compressed.lower()


class TestInsights:
    """Test cases for insight storage and retrieval."""

    def test_store_insight(self, mock_redis):
        """Test storing insights."""
        cm = ContextManager(mock_redis)

        cm.add_insight("The user likes Python programming")
        cm.add_insight("User is studying computer science")

        # Verify insights were stored
        assert mock_redis.lindex("insights", 0).decode("utf-8") == "The user likes Python programming"
        assert mock_redis.lindex("insights", 1).decode("utf-8") == "User is studying computer science"

    def test_store_multiple_insights(self, mock_redis):
        """Test storing multiple insights."""
        cm = ContextManager(mock_redis)

        insights = [
            "Insight 1",
            "Insight 2",
            "Insight 3",
            "Insight 4",
        ]

        for insight in insights:
            cm.add_insight(insight)

        # Verify all insights were stored
        for i, insight in enumerate(insights):
            assert mock_redis.lindex("insights", i).decode("utf-8") == insight

    def test_retrieve_insights(self, mock_redis):
        """Test retrieving insights."""
        cm = ContextManager(mock_redis)

        # Add insights
        cm.add_insight("Test insight 1")
        cm.add_insight("Test insight 2")

        # Retrieve insights
        all_insights = cm.get_insights()

        assert len(all_insights) == 2
        assert "Test insight 1" in all_insights
        assert "Test insight 2" in all_insights

    def test_clear_insights(self, mock_redis):
        """Test clearing all insights."""
        cm = ContextManager(mock_redis)

        # Add insights
        cm.add_insight("Insight 1")
        cm.add_insight("Insight 2")

        # Clear insights
        cm.clear_insights()

        # Verify insights were cleared
        assert mock_redis.llen("insights") == 0


class TestPersona:
    """Test cases for persona storage and retrieval."""

    def test_set_persona(self, mock_redis):
        """Test setting a persona."""
        cm = ContextManager(mock_redis)

        persona_data = {
            "name": "Helpful Assistant",
            "traits": ["friendly", "knowledgeable"],
            "style": "conversational",
        }

        cm.set_persona(persona_data)

        # Verify persona was stored
        stored = mock_redis.hgetall("persona:current")
        assert stored[b"name"] == b"Helpful Assistant"
        assert stored[b"traits"] == b'["friendly", "knowledgeable"]'
        assert stored[b"style"] == b"conversational"

    def test_get_persona(self, mock_redis):
        """Test retrieving current persona."""
        cm = ContextManager(mock_redis)

        # Set a persona
        persona_data = {
            "name": "Helpful Assistant",
            "traits": ["friendly", "knowledgeable"],
            "style": "conversational",
        }

        cm.set_persona(persona_data)

        # Retrieve the persona
        retrieved = cm.get_persona()

        assert retrieved["name"] == "Helpful Assistant"
        assert retrieved["traits"] == ["friendly", "knowledgeable"]
        assert retrieved["style"] == "conversational"

    def test_update_persona(self, mock_redis):
        """Test updating an existing persona."""
        cm = ContextManager(mock_redis)

        # Set initial persona
        cm.set_persona({"name": "Assistant", "traits": ["friendly"]})

        # Update persona
        cm.set_persona({"name": "Helpful Assistant", "traits": ["friendly", "knowledgeable"]})

        # Verify update occurred
        retrieved = cm.get_persona()
        assert retrieved["name"] == "Helpful Assistant"
        assert retrieved["traits"] == ["friendly", "knowledgeable"]

    def test_persona_default(self, mock_redis):
        """Test retrieving default persona when none is set."""
        cm = ContextManager(mock_redis)

        # Retrieve persona without setting one
        retrieved = cm.get_persona()

        assert retrieved is not None
        assert retrieved["name"] is not None
        assert "traits" in retrieved
        assert "style" in retrieved


class TestClearContext:
    """Test cases for clearing context."""

    def test_clear_user_context(self, mock_redis):
        """Test clearing user context."""
        cm = ContextManager(mock_redis)

        # Add messages
        cm.add_message("user", "Hello")
        cm.add_message("assistant", "Hi there")

        # Clear context
        cm.clear_context()

        # Verify context was cleared
        assert mock_redis.llen("context:user") == 0

    def test_clear_clears_insights(self, mock_redis):
        """Test that clearing context also clears insights."""
        cm = ContextManager(mock_redis)

        # Add messages and insights
        cm.add_message("user", "Hello")
        cm.add_insight("User likes Python")

        # Clear context
        cm.clear_context()

        # Verify both context and insights were cleared
        assert mock_redis.llen("context:user") == 0
        assert mock_redis.llen("insights") == 0
