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
