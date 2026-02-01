import math
from datetime import datetime

from memory.models import Atom, RetrievalWeights


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
