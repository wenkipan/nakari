def test_fake_embedder_is_deterministic():
    from memory.embedding import FakeEmbeddingProvider

    e = FakeEmbeddingProvider(dim=3)
    v1 = e.embed("hello")
    v2 = e.embed("hello")
    v3 = e.embed("world")

    assert v1 == v2
    assert len(v1) == 3
    assert v1 != v3
