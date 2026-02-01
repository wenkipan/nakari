import math
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from memory.embedding import EmbeddingProvider
from memory.models import Atom, RetrievalWeights
from memory.neo4j_store import Neo4jMemoryStore


def score_candidate(
    *,
    atom: Atom,
    semantic_similarity: float,
    edge_weight: float,
    emotion_boost: float,
    now_ts: datetime,
    weights: RetrievalWeights,
    decay_rate: float,
) -> float:
    hours = (now_ts - atom.timestamp).total_seconds() / 3600.0
    node_strength = atom.strength * math.exp(-decay_rate * hours)
    time_factor = math.exp(-decay_rate * hours)

    return (
        weights.semantic_similarity * float(semantic_similarity)
        + weights.node_strength * float(node_strength)
        + weights.edge_weight * float(edge_weight)
        + weights.emotion_boost * float(emotion_boost)
        + weights.time_factor * float(time_factor)
    )


def retrieve(
    *,
    store: Neo4jMemoryStore,
    embedder: EmbeddingProvider,
    query: str,
    weights: RetrievalWeights,
    top_k: int,
) -> List[Atom]:
    now = datetime.now(tz=timezone.utc)
    q_emb = embedder.embed(query)
    seeds = store.vector_search(q_emb, k=max(10, int(top_k)))

    candidates: Dict[str, Tuple[Atom, float, float, float]] = {}
    for node, sim in seeds:
        atom = store._node_to_atom(node)
        candidates[atom.content] = (atom, float(sim), 1.0, 0.0)
        for n in store.neighbors_1hop(atom.content):
            a2 = store._node_to_atom(n)
            if a2.content not in candidates:
                candidates[a2.content] = (a2, 0.0, 0.5, 0.0)

    scored: List[Tuple[float, Atom]] = []
    for atom, sim, edge_w, emo_b in candidates.values():
        scored.append(
            (
                score_candidate(
                    atom=atom,
                    semantic_similarity=sim,
                    edge_weight=edge_w,
                    emotion_boost=emo_b,
                    now_ts=now,
                    weights=weights,
                    decay_rate=0.01,
                ),
                atom,
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[: int(top_k)]]
