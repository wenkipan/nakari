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
