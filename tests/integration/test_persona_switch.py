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
