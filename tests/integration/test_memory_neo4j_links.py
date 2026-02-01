from datetime import datetime, timezone


def test_create_and_get_link_roundtrip() -> None:
    from memory.config import MemoryConfig
    from memory.models import Atom
    from memory.neo4j_store import Neo4jMemoryStore

    cfg = MemoryConfig.from_env()
    store = Neo4jMemoryStore(cfg)
    store.reset_all()
    store.ensure_schema()

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.create_atom(
        Atom(
            content="A",
            embedding=[0, 0, 0],
            type="concept",
            strength=0.1,
            timestamp=now,
        )
    )
    store.create_atom(
        Atom(
            content="B",
            embedding=[0, 0, 0],
            type="concept",
            strength=0.1,
            timestamp=now,
        )
    )

    store.create_link("A", "B", weight=0.3, timestamp=now)
    link = store.get_link("A", "B")
    assert link is not None
    assert link.weight == 0.3
