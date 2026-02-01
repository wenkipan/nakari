from datetime import datetime, timezone


def test_score_prefers_higher_semantic_similarity() -> None:
    from memory.models import Atom, RetrievalWeights
    from memory.retrieval import score_candidate

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    a1 = Atom(
        content="A1", embedding=[0, 0, 0], type="fact", strength=0.5, timestamp=now
    )
    a2 = Atom(
        content="A2", embedding=[0, 0, 0], type="fact", strength=0.5, timestamp=now
    )
    w = RetrievalWeights(
        semantic_similarity=1.0,
        node_strength=0.0,
        edge_weight=0.0,
        emotion_boost=0.0,
        time_factor=0.0,
    )

    s1 = score_candidate(
        atom=a1,
        semantic_similarity=0.9,
        edge_weight=1.0,
        emotion_boost=0.0,
        now_ts=now,
        weights=w,
        decay_rate=0.01,
    )
    s2 = score_candidate(
        atom=a2,
        semantic_similarity=0.1,
        edge_weight=1.0,
        emotion_boost=0.0,
        now_ts=now,
        weights=w,
        decay_rate=0.01,
    )
    assert s1 > s2
