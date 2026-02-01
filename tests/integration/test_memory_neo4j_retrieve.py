from datetime import datetime, timezone


def test_retrieve_returns_top_k_atoms() -> None:
    from memory.config import MemoryConfig
    from memory.embedding import FakeEmbeddingProvider
    from memory.models import Atom, RetrievalWeights
    from memory.neo4j_store import Neo4jMemoryStore
    from memory.retrieval import retrieve

    cfg = MemoryConfig.from_env()
    cfg = type(cfg)(
        neo4j_uri=cfg.neo4j_uri,
        neo4j_username=cfg.neo4j_username,
        neo4j_password=cfg.neo4j_password,
        dan_embedding_dim=3,
    )

    store = Neo4jMemoryStore(cfg)
    store.reset_all()
    store.ensure_schema()
    store.ensure_vector_index()

    e = FakeEmbeddingProvider(dim=3)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    store.create_atom(
        Atom(
            content="I like cyberpunk",
            embedding=e.embed("I like cyberpunk"),
            type="fact",
            strength=0.2,
            timestamp=now,
        )
    )
    store.create_atom(
        Atom(
            content="I like nature",
            embedding=e.embed("I like nature"),
            type="fact",
            strength=0.2,
            timestamp=now,
        )
    )

    w = RetrievalWeights()
    out = retrieve(store=store, embedder=e, query="cyberpunk", weights=w, top_k=1)
    assert len(out) == 1
    assert out[0].content in {"I like cyberpunk", "I like nature"}
