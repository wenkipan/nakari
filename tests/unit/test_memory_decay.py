"""TDD tests for DAN memory decay and boost calculations."""

import pytest
import math
from datetime import datetime, timedelta


class TestDecayCalculation:
    """Tests for lazy evaluation decay calculation."""

    def test_apply_decay_with_zero_hours(self):
        """No decay should occur when no time has passed."""
        from memory.decay import apply_decay

        result = apply_decay(weight=0.8, decay_rate=0.01, hours_elapsed=0)

        assert result == 0.8

    def test_apply_decay_formula(self):
        """Decay should follow formula: weight * exp(-decay_rate * hours)."""
        from memory.decay import apply_decay

        weight = 0.8
        decay_rate = 0.01
        hours = 10
        expected = weight * math.exp(-decay_rate * hours)

        result = apply_decay(weight, decay_rate, hours)

        assert abs(result - expected) < 1e-10

    def test_apply_decay_reduces_weight_over_time(self):
        """Weight should decrease as more time passes."""
        from memory.decay import apply_decay

        weight = 1.0
        decay_rate = 0.01

        after_1h = apply_decay(weight, decay_rate, 1)
        after_10h = apply_decay(weight, decay_rate, 10)
        after_100h = apply_decay(weight, decay_rate, 100)

        assert after_1h < weight
        assert after_10h < after_1h
        assert after_100h < after_10h

    def test_apply_decay_clamps_to_zero(self):
        """Weight should not go below 0."""
        from memory.decay import apply_decay

        result = apply_decay(weight=0.01, decay_rate=0.1, hours_elapsed=10000)

        assert result >= 0.0

    def test_apply_decay_with_negative_weight_raises_error(self):
        """Negative weight should raise ValueError."""
        from memory.decay import apply_decay

        with pytest.raises(ValueError):
            apply_decay(weight=-0.1, decay_rate=0.01, hours_elapsed=1)


class TestDecayAtom:
    """Tests for applying decay to Atom objects."""

    def test_decay_atom_updates_weight_and_timestamp(self):
        """decay_atom should update weight and timestamp."""
        from memory.models import Atom, AtomType
        from memory.decay import decay_atom

        old_time = datetime.now() - timedelta(hours=10)
        atom = Atom(
            content="test", atom_type=AtomType.FACT, weight=1.0, timestamp=old_time
        )

        before_weight = atom.weight
        result = decay_atom(atom)

        assert result.weight < before_weight
        assert result.timestamp > old_time

    def test_decay_atom_uses_correct_decay_rate_for_fact(self):
        """Fact atoms should use DecayRates.FACT = 0.01."""
        from memory.models import Atom, AtomType, DecayRates
        from memory.decay import decay_atom, apply_decay

        old_time = datetime.now() - timedelta(hours=24)
        atom = Atom(
            content="test", atom_type=AtomType.FACT, weight=1.0, timestamp=old_time
        )

        result = decay_atom(atom)
        expected_weight = apply_decay(1.0, DecayRates.FACT, 24)

        # Allow some tolerance for time calculation differences
        assert abs(result.weight - expected_weight) < 0.01

    def test_decay_atom_uses_correct_decay_rate_for_concept(self):
        """Concept atoms should use DecayRates.CONCEPT = 0.005."""
        from memory.models import Atom, AtomType, DecayRates
        from memory.decay import decay_atom, apply_decay

        old_time = datetime.now() - timedelta(hours=24)
        atom = Atom(
            content="test", atom_type=AtomType.CONCEPT, weight=1.0, timestamp=old_time
        )

        result = decay_atom(atom)
        expected_weight = apply_decay(1.0, DecayRates.CONCEPT, 24)

        assert abs(result.weight - expected_weight) < 0.01

    def test_decay_atom_uses_correct_decay_rate_for_emotion(self):
        """Emotion atoms should use DecayRates.EMOTION = 0.05."""
        from memory.models import Atom, AtomType, DecayRates
        from memory.decay import decay_atom, apply_decay

        old_time = datetime.now() - timedelta(hours=24)
        atom = Atom(
            content="happy", atom_type=AtomType.EMOTION, weight=1.0, timestamp=old_time
        )

        result = decay_atom(atom)
        expected_weight = apply_decay(1.0, DecayRates.EMOTION, 24)

        assert abs(result.weight - expected_weight) < 0.01

    def test_decay_atom_returns_new_atom(self):
        """decay_atom should return a new Atom, not modify in place."""
        from memory.models import Atom, AtomType
        from memory.decay import decay_atom

        old_time = datetime.now() - timedelta(hours=10)
        original = Atom(
            content="test", atom_type=AtomType.FACT, weight=1.0, timestamp=old_time
        )
        original_weight = original.weight

        result = decay_atom(original)

        # Original should be unchanged
        assert original.weight == original_weight
        # Result should be different object
        assert result is not original


class TestDecayEdge:
    """Tests for applying decay to Edge objects."""

    def test_decay_edge_updates_weight_and_timestamp(self):
        """decay_edge should update weight and timestamp."""
        from memory.models import Edge
        from memory.decay import decay_edge

        old_time = datetime.now() - timedelta(hours=10)
        edge = Edge(source_id="a", target_id="b", weight=1.0, timestamp=old_time)

        before_weight = edge.weight
        result = decay_edge(edge, is_emotion_edge=False)

        assert result.weight < before_weight
        assert result.timestamp > old_time

    def test_decay_edge_uses_normal_rate_for_normal_edge(self):
        """Normal edges should use DecayRates.NORMAL_EDGE = 0.005."""
        from memory.models import Edge, DecayRates
        from memory.decay import decay_edge, apply_decay

        old_time = datetime.now() - timedelta(hours=24)
        edge = Edge(source_id="a", target_id="b", weight=1.0, timestamp=old_time)

        result = decay_edge(edge, is_emotion_edge=False)
        expected_weight = apply_decay(1.0, DecayRates.NORMAL_EDGE, 24)

        assert abs(result.weight - expected_weight) < 0.01

    def test_decay_edge_uses_emotion_rate_for_emotion_edge(self):
        """Emotion edges should use DecayRates.EMOTION_EDGE = 0.001."""
        from memory.models import Edge, DecayRates
        from memory.decay import decay_edge, apply_decay

        old_time = datetime.now() - timedelta(hours=24)
        edge = Edge(source_id="a", target_id="b", weight=1.0, timestamp=old_time)

        result = decay_edge(edge, is_emotion_edge=True)
        expected_weight = apply_decay(1.0, DecayRates.EMOTION_EDGE, 24)

        assert abs(result.weight - expected_weight) < 0.01

    def test_emotion_edge_decays_slower_than_normal(self):
        """Emotion edges should decay slower than normal edges."""
        from memory.models import Edge
        from memory.decay import decay_edge

        old_time = datetime.now() - timedelta(hours=100)

        normal_edge = Edge(source_id="a", target_id="b", weight=1.0, timestamp=old_time)
        emotion_edge = Edge(
            source_id="a", target_id="b", weight=1.0, timestamp=old_time
        )

        normal_result = decay_edge(normal_edge, is_emotion_edge=False)
        emotion_result = decay_edge(emotion_edge, is_emotion_edge=True)

        # Emotion edge decays slower, so weight should be higher
        assert emotion_result.weight > normal_result.weight


class TestBoostAtom:
    """Tests for boost operation on atoms."""

    def test_boost_atom_increases_weight(self):
        """boost_atom should increase weight."""
        from memory.models import Atom, AtomType
        from memory.decay import boost_atom

        atom = Atom(content="test", atom_type=AtomType.FACT, weight=0.5)

        result = boost_atom(atom)

        assert result.weight > atom.weight

    def test_boost_atom_uses_correct_boost_for_fact(self):
        """Fact atoms should use BoostValues.FACT = 0.1."""
        from memory.models import Atom, AtomType, BoostValues
        from memory.decay import boost_atom

        atom = Atom(content="test", atom_type=AtomType.FACT, weight=0.5)

        result = boost_atom(atom)
        expected = min(1.0, 0.5 + BoostValues.FACT)

        assert abs(result.weight - expected) < 1e-10

    def test_boost_atom_uses_correct_boost_for_concept(self):
        """Concept atoms should use BoostValues.CONCEPT = 0.1."""
        from memory.models import Atom, AtomType, BoostValues
        from memory.decay import boost_atom

        atom = Atom(content="test", atom_type=AtomType.CONCEPT, weight=0.5)

        result = boost_atom(atom)
        expected = min(1.0, 0.5 + BoostValues.CONCEPT)

        assert abs(result.weight - expected) < 1e-10

    def test_boost_atom_uses_correct_boost_for_emotion(self):
        """Emotion atoms should use BoostValues.EMOTION = 0.1."""
        from memory.models import Atom, AtomType, BoostValues
        from memory.decay import boost_atom

        atom = Atom(content="happy", atom_type=AtomType.EMOTION, weight=0.5)

        result = boost_atom(atom)
        expected = min(1.0, 0.5 + BoostValues.EMOTION)

        assert abs(result.weight - expected) < 1e-10

    def test_boost_atom_clamps_to_one(self):
        """Weight should not exceed 1.0 after boost."""
        from memory.models import Atom, AtomType
        from memory.decay import boost_atom

        atom = Atom(content="test", atom_type=AtomType.FACT, weight=0.95)

        result = boost_atom(atom)

        assert result.weight == 1.0

    def test_boost_atom_returns_new_atom(self):
        """boost_atom should return a new Atom, not modify in place."""
        from memory.models import Atom, AtomType
        from memory.decay import boost_atom

        original = Atom(content="test", atom_type=AtomType.FACT, weight=0.5)
        original_weight = original.weight

        result = boost_atom(original)

        assert original.weight == original_weight
        assert result is not original


class TestBoostEdge:
    """Tests for boost operation on edges."""

    def test_boost_edge_increases_weight(self):
        """boost_edge should increase weight."""
        from memory.models import Edge
        from memory.decay import boost_edge

        edge = Edge(source_id="a", target_id="b", weight=0.5)

        result = boost_edge(edge, is_emotion_edge=False)

        assert result.weight > edge.weight

    def test_boost_edge_uses_normal_boost_for_normal_edge(self):
        """Normal edges should use BoostValues.NORMAL_EDGE = 0.1."""
        from memory.models import Edge, BoostValues
        from memory.decay import boost_edge

        edge = Edge(source_id="a", target_id="b", weight=0.5)

        result = boost_edge(edge, is_emotion_edge=False)
        expected = min(1.0, 0.5 + BoostValues.NORMAL_EDGE)

        assert abs(result.weight - expected) < 1e-10

    def test_boost_edge_uses_emotion_boost_for_emotion_edge(self):
        """Emotion edges should use BoostValues.EMOTION_EDGE = 0.1."""
        from memory.models import Edge, BoostValues
        from memory.decay import boost_edge

        edge = Edge(source_id="a", target_id="b", weight=0.5)

        result = boost_edge(edge, is_emotion_edge=True)
        expected = min(1.0, 0.5 + BoostValues.EMOTION_EDGE)

        assert abs(result.weight - expected) < 1e-10

    def test_boost_edge_clamps_to_one(self):
        """Weight should not exceed 1.0 after boost."""
        from memory.models import Edge
        from memory.decay import boost_edge

        edge = Edge(source_id="a", target_id="b", weight=0.95)

        result = boost_edge(edge, is_emotion_edge=False)

        assert result.weight == 1.0


class TestGetDecayRateForAtom:
    """Tests for getting decay rate based on atom type."""

    def test_get_decay_rate_for_fact(self):
        """Should return FACT decay rate for fact atoms."""
        from memory.models import AtomType, DecayRates
        from memory.decay import get_decay_rate_for_atom

        rate = get_decay_rate_for_atom(AtomType.FACT)

        assert rate == DecayRates.FACT

    def test_get_decay_rate_for_concept(self):
        """Should return CONCEPT decay rate for concept atoms."""
        from memory.models import AtomType, DecayRates
        from memory.decay import get_decay_rate_for_atom

        rate = get_decay_rate_for_atom(AtomType.CONCEPT)

        assert rate == DecayRates.CONCEPT

    def test_get_decay_rate_for_emotion(self):
        """Should return EMOTION decay rate for emotion atoms."""
        from memory.models import AtomType, DecayRates
        from memory.decay import get_decay_rate_for_atom

        rate = get_decay_rate_for_atom(AtomType.EMOTION)

        assert rate == DecayRates.EMOTION


class TestGetBoostValueForAtom:
    """Tests for getting boost value based on atom type."""

    def test_get_boost_value_for_fact(self):
        """Should return FACT boost for fact atoms."""
        from memory.models import AtomType, BoostValues
        from memory.decay import get_boost_value_for_atom

        boost = get_boost_value_for_atom(AtomType.FACT)

        assert boost == BoostValues.FACT

    def test_get_boost_value_for_concept(self):
        """Should return CONCEPT boost for concept atoms."""
        from memory.models import AtomType, BoostValues
        from memory.decay import get_boost_value_for_atom

        boost = get_boost_value_for_atom(AtomType.CONCEPT)

        assert boost == BoostValues.CONCEPT

    def test_get_boost_value_for_emotion(self):
        """Should return EMOTION boost for emotion atoms."""
        from memory.models import AtomType, BoostValues
        from memory.decay import get_boost_value_for_atom

        boost = get_boost_value_for_atom(AtomType.EMOTION)

        assert boost == BoostValues.EMOTION
