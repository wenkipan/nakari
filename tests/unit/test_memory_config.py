from __future__ import annotations


def test_memory_config_from_env_defaults() -> None:
    from memory.config import MemoryConfig

    config = MemoryConfig.from_env()

    assert config.neo4j_uri == "bolt://localhost:7687"
    assert config.neo4j_username == "neo4j"
    assert config.neo4j_password == "password"
    assert config.dan_embedding_dim == 1536


def test_memory_config_from_env_overrides(monkeypatch) -> None:
    from memory.config import MemoryConfig

    monkeypatch.setenv("NEO4J_URI", "bolt://db:7687")
    monkeypatch.setenv("NEO4J_USERNAME", "dan")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    monkeypatch.setenv("DAN_EMBEDDING_DIM", "2048")

    config = MemoryConfig.from_env()

    assert config.neo4j_uri == "bolt://db:7687"
    assert config.neo4j_username == "dan"
    assert config.neo4j_password == "secret"
    assert config.dan_embedding_dim == 2048
