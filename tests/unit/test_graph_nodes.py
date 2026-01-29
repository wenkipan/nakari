"""Unit tests for LangGraph nodes.

This module provides comprehensive tests for the LangGraph workflow nodes:
- retrieve_long_term_memory: Persona loading and insight retrieval
- manage_context: Context window trimming and message compression
- generate_response: LLM response generation with reflection signal handling

The tests verify:
- Persona loading and integration with context manager
- Context window trimming with token management
- Reflection signal detection in LLM responses
- Error handling during generation

All tests use Redis DBs 9-15 for isolation from other tests.
"""

from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from llm.graph import (
    retrieve_long_term_memory,
    manage_context,
    generate_response,
    NakariState,
)


class TestRetrieveMemoryCallsPersona:
    """Test cases for retrieve_long_term_memory node."""

    @patch("llm.graph.context_manager")
    @patch("llm.graph.persona_loader")
    def test_calls_persona_loader(self, mock_persona_loader, mock_context_manager, mock_redis):
        """Test that retrieve_memory loads persona using persona_loader."""
        # Setup mocks
        mock_context_manager.get_active_persona.return_value = "test_persona"
        mock_persona_data = {"name": "Test Persona", "traits": ["friendly"]}
        mock_persona_loader.load_persona.return_value = mock_persona_data
        mock_persona_loader.format_persona_prompt.return_value = "You are Test Persona"

        # Create state
        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = retrieve_long_term_memory(state)

        # Verify persona loader was called
        mock_persona_loader.load_persona.assert_called_once_with("test_persona")

    @patch("llm.graph.context_manager")
    @patch("llm.graph.persona_loader")
    def test_uses_default_persona_when_none_loaded(self, mock_persona_loader, mock_context_manager, mock_redis):
        """Test that default persona is used when persona_loader returns None."""
        # Setup mocks
        mock_context_manager.get_active_persona.return_value = "nonexistent"
        mock_persona_loader.load_persona.return_value = None
        mock_context_manager.get_insights.return_value = []

        # Create state
        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = retrieve_long_term_memory(state)

        # Verify default persona content is in result
        system_msg = result["messages"][0]
        assert "Nakari" in system_msg.content
        assert "memory and reflection" in system_msg.content.lower()

    @patch("llm.graph.context_manager")
    @patch("llm.graph.persona_loader")
    def test_includes_insights_in_system_prompt(self, mock_persona_loader, mock_context_manager, mock_redis):
        """Test that retrieved insights are included in the system prompt."""
        # Setup mocks
        mock_context_manager.get_active_persona.return_value = "test_persona"
        mock_persona_loader.load_persona.return_value = {"name": "Test Persona"}
        mock_persona_loader.format_persona_prompt.return_value = "You are Test Persona"
        mock_context_manager.get_insights.return_value = ["Insight 1", "Insight 2"]

        # Create state
        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = retrieve_long_term_memory(state)

        # Verify insights are in system prompt
        system_msg = result["messages"][0]
        assert "Insight 1" in system_msg.content
        assert "Insight 2" in system_msg.content


class TestManageContextTrimsMessages:
    """Test cases for manage_context node."""

    def test_trims_messages_to_max_tokens(self, mock_redis):
        """Test that context is trimmed to max_tokens limit."""
        # Create many messages (simulating long conversation)
        messages = [HumanMessage(content=f"Message {i}") for i in range(50)]

        state = NakariState(
            messages=messages,
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = manage_context(state)

        # Verify context was trimmed
        trimmed_messages = result["context_window"]
        # Should have system + some recent messages
        assert len(trimmed_messages) <= 5  # System + at most 4 recent messages

    def test_includes_system_message(self, mock_redis):
        """Test that system message is preserved in trimmed context."""
        # Create messages
        messages = [HumanMessage(content="Message 1"), HumanMessage(content="Message 2")]

        state = NakariState(
            messages=messages,
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = manage_context(state)

        # Verify system message is in context
        context_messages = result["context_window"]
        system_messages = [m for m in context_messages if isinstance(m, SystemMessage)]
        assert len(system_messages) == 1

    def test_starts_with_human_message(self, mock_redis):
        """Test that trimmed context starts with a human message."""
        # Create messages
        messages = [
            SystemMessage(content="System message"),
            HumanMessage(content="Message 1"),
            HumanMessage(content="Message 2"),
            HumanMessage(content="Message 3"),
        ]

        state = NakariState(
            messages=messages,
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = manage_context(state)

        # Verify context starts with human message
        context_messages = result["context_window"]
        first_human_idx = next(i for i, m in enumerate(context_messages) if isinstance(m, HumanMessage))
        assert first_human_idx == 1  # System at 0, first human at 1


class TestGenerateResponseWithReflection:
    """Test cases for generate_response node with reflection signal."""

    @patch("llm.graph.llm")
    def test_detects_reflection_signal(self, mock_llm, mock_redis):
        """Test that reflection signal is detected in LLM response."""
        # Setup mock
        mock_llm.invoke.return_value = AIMessage(
            content="[[REFLECT]] I've noted that for future reference."
        )

        state = NakariState(
            messages=[
                HumanMessage(content="My name is Alice"),
                AIMessage(content="Hello Alice!"),
                SystemMessage(content="You are Nakari."),
            ],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = generate_response(state)

        # Verify reflection signal was detected
        assert result["should_reflect"] is True
        assert "[[REFLECT]]" not in result["response"]

    @patch("llm.graph.llm")
    def test_strips_reflection_tag_from_response(self, mock_llm, mock_redis):
        """Test that reflection tag is stripped from final response."""
        # Setup mock
        mock_llm.invoke.return_value = AIMessage(
            content="[[REFLECT]] Nice to meet you, Alice! I'll remember that."
        )

        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = generate_response(state)

        # Verify tag was stripped
        assert result["response"] == "Nice to meet you, Alice! I'll remember that."
        assert "[[REFLECT]]" not in result["response"]


class TestGenerateResponseWithoutReflection:
    """Test cases for generate_response node without reflection signal."""

    @patch("llm.graph.llm")
    def test_normal_response_no_signal(self, mock_llm, mock_redis):
        """Test normal response generation without reflection signal."""
        # Setup mock
        mock_llm.invoke.return_value = AIMessage(
            content="Hello! How can I help you today?"
        )

        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = generate_response(state)

        # Verify normal response
        assert result["should_reflect"] is False
        assert result["response"] == "Hello! How can I help you today?"

    @patch("llm.graph.llm")
    def test_empty_signal_results_in_normal_response(self, mock_llm, mock_redis):
        """Test that response with only reflection tag (not at start) is treated normally."""
        # Setup mock
        mock_llm.invoke.return_value = AIMessage(
            content="Some text [[REFLECT]] at the end."
        )

        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = generate_response(state)

        # Verify reflection signal not detected (tag not at start)
        assert result["should_reflect"] is False


class TestGenerateResponseHandlesError:
    """Test cases for error handling in generate_response node."""

    @patch("llm.graph.llm")
    def test_returns_error_message_on_exception(self, mock_llm, mock_redis):
        """Test that error message is returned when LLM call fails."""
        # Setup mock to raise exception
        mock_llm.invoke.side_effect = Exception("LLM connection failed")

        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = generate_response(state)

        # Verify error message was returned
        assert result["should_reflect"] is False
        assert "trouble connecting" in result["response"].lower()

    @patch("llm.graph.llm")
    def test_sets_should_reflect_false_on_error(self, mock_llm, mock_redis):
        """Test that should_reflect is False when error occurs."""
        # Setup mock to raise exception
        mock_llm.invoke.side_effect = Exception("LLM error")

        state = NakariState(
            messages=[HumanMessage(content="Hello")],
            context_window=[],
            user_id="test_user",
            response="",
            should_reflect=False
        )

        # Execute node
        result = generate_response(state)

        # Verify should_reflect remains False on error
        assert result["should_reflect"] is False
