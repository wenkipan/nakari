from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class Atom(BaseModel):
    """Discrete Atom Network (DAN) node."""

    content: str
    embedding: List[float]
    type: Literal["fact", "concept", "emotion"]
    strength: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    extensions: Dict[str, Any] = Field(default_factory=dict)


class Link(BaseModel):
    """Relationship between atoms."""

    weight: float = Field(ge=0.0, le=1.0)
    timestamp: datetime


class RetrievalWeights(BaseModel):
    """Weights for unified retrieval scoring."""

    w1: float
    w2: float
    w3: float
    w4: float
    w5: float
    decay_rate: float
