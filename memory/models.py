"""DAN Memory Models - Pydantic models for Discrete Atom Network.

This module defines the core data models for the DAN memory system:
- AtomType: Enum for different types of atoms (Fact, Concept, Emotion)
- Atom: Node in the memory graph representing a piece of knowledge
- Edge: Connection between atoms
- DecayRates: Constants for Ebbinghaus forgetting curve simulation
- BoostValues: Constants for memory reinforcement
- RetrievalWeights: Configuration for retrieval scoring
- RetrievalConfig: Configuration for retrieval behavior
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AtomType(str, Enum):
    """Types of atoms in the DAN memory system.

    - FACT: Specific situations/events with complete semantics (like hippocampal episodic traces)
    - CONCEPT: Semantic anchors for indexing (like cortical concept neurons)
    - EMOTION: Emotional nodes (like amygdala), strength indicates activation level
    """

    FACT = "fact"
    CONCEPT = "concept"
    EMOTION = "emotion"


class Atom(BaseModel):
    """An atom (node) in the DAN memory graph.

    Attributes:
        id: Optional database identifier
        content: The semantic content of this atom
        atom_type: The type of this atom (Fact, Concept, or Emotion)
        embedding: Optional vector embedding for semantic search
        weight: Importance weight in [0.0, 1.0], decays over time
        timestamp: Last access time for lazy decay calculation
        extensions: Optional extension data
    """

    id: Optional[str] = None
    content: str
    atom_type: AtomType
    embedding: Optional[List[float]] = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    extensions: Optional[Dict[str, Any]] = None

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Ensure weight is in valid range [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")
        return v


class Edge(BaseModel):
    """An edge (connection) between two atoms in the DAN memory graph.

    Attributes:
        source_id: ID of the source atom
        target_id: ID of the target atom
        weight: Connection strength in [0.0, 1.0], decays over time
        timestamp: Last access time for lazy decay calculation
    """

    source_id: str
    target_id: str
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Ensure weight is in valid range [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")
        return v


class DecayRates:
    """Decay rate constants for Ebbinghaus forgetting curve simulation.

    Formula: weight = weight × exp(-decay_rate × hours)
    """

    FACT = 0.01  # Memory fades
    CONCEPT = 0.005  # Concepts are relatively stable
    EMOTION = 0.05  # Emotions fluctuate quickly (current state)
    NORMAL_EDGE = 0.005  # Associations are stable
    EMOTION_EDGE = 0.001  # Personality evolves slowly


class BoostValues:
    """Boost constants for memory reinforcement.

    Used to simulate repeated memorization counteracting the forgetting curve.
    Formula: weight = weight + boost
    """

    FACT = 0.1
    CONCEPT = 0.1
    EMOTION = 0.1
    NORMAL_EDGE = 0.1
    EMOTION_EDGE = 0.1


class RetrievalWeights(BaseModel):
    """Configuration for retrieval scoring.

    final_score =
        semantic_similarity * semantic_similarity +
        (is_Fact ? fact_weight : 0) * weight +
        (is_Concept ? concept_weight : 0) * weight +
        (is_Emotion ? emotion_weight : 0) * weight
    """

    semantic_similarity: float = 1.0
    fact_weight: float = 0.1
    concept_weight: float = 0.1
    emotion_weight: float = 0.2


class RetrievalConfig(BaseModel):
    """Configuration for retrieval behavior.

    Attributes:
        n_hops: Number of hops to expand from seed atoms (default: 2)
        top_k: Number of top-scoring atoms to return (default: 3)
    """

    n_hops: int = 2
    top_k: int = 3
