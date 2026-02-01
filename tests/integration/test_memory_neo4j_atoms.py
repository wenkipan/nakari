from datetime import datetime, timezone


def test_create_and_get_atom_roundtrip() -> None:
    from memory.config import MemoryConfig
    from memory.models import Atom
    from memory.neo4j_store import Neo4jMemoryStore

    cfg = MemoryConfig.from_env()
    store = Neo4jMemoryStore(cfg)
    store.reset_all()  # test isolation
    store.ensure_schema()

    atom = Atom(
        content="Wenki stayed up late",
        embedding=[0.0, 1.0, 0.0],
        type="fact",
        strength=0.2,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        extensions={"source": "test"},
    )

    store.create_atom(atom)
    loaded = store.get_atom("Wenki stayed up late")
    assert loaded is not None
    assert loaded.content == atom.content
    assert loaded.type == "fact"
