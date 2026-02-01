from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


AtomType = Literal["fact", "concept", "emotion"]


class Atom(BaseModel):
    """Discrete Atom Network (DAN) node."""

    content: str
    embedding: List[float] = Field(default_factory=list)
    type: AtomType
    strength: float = 0.0
    timestamp: datetime
    extensions: Dict[str, Any] = Field(default_factory=dict)


class Link(BaseModel):
    """Relationship between atoms."""

    source: str
    target: str
    weight: float
    timestamp: datetime


class RetrievalWeights(BaseModel):
    """Weights for unified retrieval scoring."""

    semantic_similarity: float = 1.0
    node_strength: float = 0.2
    edge_weight: float = 0.1
    emotion_boost: float = 0.2
    time_factor: float = 0.1
