"""DAN Memory Decay - Lazy evaluation and boost operations.

This module implements the Ebbinghaus forgetting curve simulation
using lazy evaluation strategy, and boost operations for memory reinforcement.

Core formulas:
- Decay: weight = weight × exp(-decay_rate × hours)
- Boost: weight = min(1.0, weight + boost_value)
"""

import math
from datetime import datetime
from typing import Union

from memory.models import (
    Atom,
    AtomType,
    BoostValues,
    DecayRates,
    Edge,
)


def apply_decay(weight: float, decay_rate: float, hours_elapsed: float) -> float:
    """Apply Ebbinghaus forgetting curve decay to a weight value.

    Formula: weight = weight × exp(-decay_rate × hours_elapsed)

    Args:
        weight: The current weight value (must be >= 0).
        decay_rate: The decay rate constant.
        hours_elapsed: Time elapsed in hours since last access.

    Returns:
        The decayed weight value (clamped to >= 0).

    Raises:
        ValueError: If weight is negative.
    """
    if weight < 0:
        raise ValueError("weight must be non-negative")

    decayed = weight * math.exp(-decay_rate * hours_elapsed)
    return max(0.0, decayed)


def get_decay_rate_for_atom(atom_type: AtomType) -> float:
    """Get the appropriate decay rate for an atom type.

    Args:
        atom_type: The type of atom.

    Returns:
        The decay rate constant for this atom type.
    """
    decay_rates = {
        AtomType.FACT: DecayRates.FACT,
        AtomType.CONCEPT: DecayRates.CONCEPT,
        AtomType.EMOTION: DecayRates.EMOTION,
    }
    return decay_rates[atom_type]


def get_boost_value_for_atom(atom_type: AtomType) -> float:
    """Get the appropriate boost value for an atom type.

    Args:
        atom_type: The type of atom.

    Returns:
        The boost value constant for this atom type.
    """
    boost_values = {
        AtomType.FACT: BoostValues.FACT,
        AtomType.CONCEPT: BoostValues.CONCEPT,
        AtomType.EMOTION: BoostValues.EMOTION,
    }
    return boost_values[atom_type]


def decay_atom(atom: Atom, now: datetime = None) -> Atom:
    """Apply lazy decay to an atom and update its timestamp.

    This implements the lazy evaluation strategy: decay is only calculated
    when the atom is accessed, based on time since last access.

    Args:
        atom: The atom to decay.
        now: Current time (default: datetime.now()).

    Returns:
        A new Atom with updated weight and timestamp.
    """
    if now is None:
        now = datetime.now()

    hours_elapsed = (now - atom.timestamp).total_seconds() / 3600.0
    decay_rate = get_decay_rate_for_atom(atom.atom_type)
    new_weight = apply_decay(atom.weight, decay_rate, hours_elapsed)

    return Atom(
        id=atom.id,
        content=atom.content,
        atom_type=atom.atom_type,
        embedding=atom.embedding,
        weight=new_weight,
        timestamp=now,
        extensions=atom.extensions,
    )


def decay_edge(edge: Edge, is_emotion_edge: bool, now: datetime = None) -> Edge:
    """Apply lazy decay to an edge and update its timestamp.

    Args:
        edge: The edge to decay.
        is_emotion_edge: True if either endpoint is an Emotion atom.
        now: Current time (default: datetime.now()).

    Returns:
        A new Edge with updated weight and timestamp.
    """
    if now is None:
        now = datetime.now()

    hours_elapsed = (now - edge.timestamp).total_seconds() / 3600.0
    decay_rate = DecayRates.EMOTION_EDGE if is_emotion_edge else DecayRates.NORMAL_EDGE
    new_weight = apply_decay(edge.weight, decay_rate, hours_elapsed)

    return Edge(
        source_id=edge.source_id,
        target_id=edge.target_id,
        weight=new_weight,
        timestamp=now,
    )


def boost_atom(atom: Atom) -> Atom:
    """Apply boost to an atom's weight.

    Boost simulates memory reinforcement through repetition.
    Formula: weight = min(1.0, weight + boost_value)

    Args:
        atom: The atom to boost.

    Returns:
        A new Atom with boosted weight.
    """
    boost_value = get_boost_value_for_atom(atom.atom_type)
    new_weight = min(1.0, atom.weight + boost_value)

    return Atom(
        id=atom.id,
        content=atom.content,
        atom_type=atom.atom_type,
        embedding=atom.embedding,
        weight=new_weight,
        timestamp=atom.timestamp,
        extensions=atom.extensions,
    )


def boost_edge(edge: Edge, is_emotion_edge: bool) -> Edge:
    """Apply boost to an edge's weight.

    Args:
        edge: The edge to boost.
        is_emotion_edge: True if either endpoint is an Emotion atom.

    Returns:
        A new Edge with boosted weight.
    """
    boost_value = (
        BoostValues.EMOTION_EDGE if is_emotion_edge else BoostValues.NORMAL_EDGE
    )
    new_weight = min(1.0, edge.weight + boost_value)

    return Edge(
        source_id=edge.source_id,
        target_id=edge.target_id,
        weight=new_weight,
        timestamp=edge.timestamp,
    )
