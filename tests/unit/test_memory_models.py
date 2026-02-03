"""TDD tests for DAN memory models: Atom, Edge, AtomType."""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestAtomType:
    """Tests for AtomType enum."""

    def test_atom_type_has_fact(self):
        """AtomType should have FACT type."""
        from memory.models import AtomType

        assert AtomType.FACT is not None
        assert AtomType.FACT.value == "fact"

    def test_atom_type_has_concept(self):
        """AtomType should have CONCEPT type."""
        from memory.models import AtomType

        assert AtomType.CONCEPT is not None
        assert AtomType.CONCEPT.value == "concept"

    def test_atom_type_has_emotion(self):
        """AtomType should have EMOTION type."""
        from memory.models import AtomType

        assert AtomType.EMOTION is not None
        assert AtomType.EMOTION.value == "emotion"


class TestAtom:
    """Tests for Atom model."""

    def test_atom_creation_with_required_fields(self):
        """Atom can be created with content and type."""
        from memory.models import Atom, AtomType

        atom = Atom(content="Wenki在熬夜", atom_type=AtomType.FACT)

        assert atom.content == "Wenki在熬夜"
        assert atom.atom_type == AtomType.FACT

    def test_atom_has_default_weight(self):
        """Atom should have default weight of 1.0."""
        from memory.models import Atom, AtomType

        atom = Atom(content="test", atom_type=AtomType.CONCEPT)

        assert atom.weight == 1.0

    def test_atom_has_default_timestamp(self):
        """Atom should have default timestamp set to now."""
        from memory.models import Atom, AtomType

        before = datetime.now()
        atom = Atom(content="test", atom_type=AtomType.CONCEPT)
        after = datetime.now()

        assert before <= atom.timestamp <= after

    def test_atom_can_have_embedding(self):
        """Atom can store embedding vector."""
        from memory.models import Atom, AtomType

        embedding = [0.1, 0.2, 0.3]
        atom = Atom(content="test", atom_type=AtomType.FACT, embedding=embedding)

        assert atom.embedding == embedding

    def test_atom_embedding_is_optional(self):
        """Atom embedding should be optional (None by default)."""
        from memory.models import Atom, AtomType

        atom = Atom(content="test", atom_type=AtomType.CONCEPT)

        assert atom.embedding is None

    def test_atom_can_have_extensions(self):
        """Atom can store extension data."""
        from memory.models import Atom, AtomType

        extensions = {"source": "chat", "confidence": 0.9}
        atom = Atom(content="test", atom_type=AtomType.FACT, extensions=extensions)

        assert atom.extensions == extensions

    def test_atom_extensions_is_optional(self):
        """Atom extensions should be optional (None by default)."""
        from memory.models import Atom, AtomType

        atom = Atom(content="test", atom_type=AtomType.CONCEPT)

        assert atom.extensions is None

    def test_atom_weight_must_be_between_0_and_1(self):
        """Atom weight must be in range [0.0, 1.0]."""
        from memory.models import Atom, AtomType

        with pytest.raises(ValidationError):
            Atom(content="test", atom_type=AtomType.FACT, weight=1.5)

        with pytest.raises(ValidationError):
            Atom(content="test", atom_type=AtomType.FACT, weight=-0.1)

    def test_atom_can_have_id(self):
        """Atom can have optional id for database reference."""
        from memory.models import Atom, AtomType

        atom = Atom(content="test", atom_type=AtomType.FACT, id="atom_123")

        assert atom.id == "atom_123"

    def test_atom_id_is_optional(self):
        """Atom id should be optional (None by default)."""
        from memory.models import Atom, AtomType

        atom = Atom(content="test", atom_type=AtomType.CONCEPT)

        assert atom.id is None


class TestEdge:
    """Tests for Edge model."""

    def test_edge_creation_with_required_fields(self):
        """Edge can be created with source and target ids."""
        from memory.models import Edge

        edge = Edge(source_id="atom_1", target_id="atom_2")

        assert edge.source_id == "atom_1"
        assert edge.target_id == "atom_2"

    def test_edge_has_default_weight(self):
        """Edge should have default weight of 1.0."""
        from memory.models import Edge

        edge = Edge(source_id="atom_1", target_id="atom_2")

        assert edge.weight == 1.0

    def test_edge_has_default_timestamp(self):
        """Edge should have default timestamp set to now."""
        from memory.models import Edge

        before = datetime.now()
        edge = Edge(source_id="atom_1", target_id="atom_2")
        after = datetime.now()

        assert before <= edge.timestamp <= after

    def test_edge_weight_must_be_between_0_and_1(self):
        """Edge weight must be in range [0.0, 1.0]."""
        from memory.models import Edge

        with pytest.raises(ValidationError):
            Edge(source_id="a", target_id="b", weight=1.5)

        with pytest.raises(ValidationError):
            Edge(source_id="a", target_id="b", weight=-0.1)

    def test_edge_can_have_custom_weight(self):
        """Edge can be created with custom weight."""
        from memory.models import Edge

        edge = Edge(source_id="atom_1", target_id="atom_2", weight=0.5)

        assert edge.weight == 0.5


class TestDecayRates:
    """Tests for decay rate constants."""

    def test_fact_decay_rate(self):
        """Fact decay rate should be 0.01."""
        from memory.models import DecayRates

        assert DecayRates.FACT == 0.01

    def test_concept_decay_rate(self):
        """Concept decay rate should be 0.005."""
        from memory.models import DecayRates

        assert DecayRates.CONCEPT == 0.005

    def test_emotion_decay_rate(self):
        """Emotion decay rate should be 0.05."""
        from memory.models import DecayRates

        assert DecayRates.EMOTION == 0.05

    def test_normal_edge_decay_rate(self):
        """Normal edge decay rate should be 0.005."""
        from memory.models import DecayRates

        assert DecayRates.NORMAL_EDGE == 0.005

    def test_emotion_edge_decay_rate(self):
        """Emotion edge decay rate should be 0.001."""
        from memory.models import DecayRates

        assert DecayRates.EMOTION_EDGE == 0.001


class TestBoostValues:
    """Tests for boost value constants."""

    def test_fact_boost(self):
        """Fact boost should be 0.1."""
        from memory.models import BoostValues

        assert BoostValues.FACT == 0.1

    def test_concept_boost(self):
        """Concept boost should be 0.1."""
        from memory.models import BoostValues

        assert BoostValues.CONCEPT == 0.1

    def test_emotion_boost(self):
        """Emotion boost should be 0.1."""
        from memory.models import BoostValues

        assert BoostValues.EMOTION == 0.1

    def test_normal_edge_boost(self):
        """Normal edge boost should be 0.1."""
        from memory.models import BoostValues

        assert BoostValues.NORMAL_EDGE == 0.1

    def test_emotion_edge_boost(self):
        """Emotion edge boost should be 0.1."""
        from memory.models import BoostValues

        assert BoostValues.EMOTION_EDGE == 0.1


class TestRetrievalWeights:
    """Tests for RetrievalWeights configuration."""

    def test_retrieval_weights_default_values(self):
        """RetrievalWeights should have sensible defaults."""
        from memory.models import RetrievalWeights

        weights = RetrievalWeights()

        assert weights.semantic_similarity == 1.0
        assert weights.fact_weight == 0.1
        assert weights.concept_weight == 0.1
        assert weights.emotion_weight == 0.2

    def test_retrieval_weights_can_be_customized(self):
        """RetrievalWeights can be customized."""
        from memory.models import RetrievalWeights

        weights = RetrievalWeights(
            semantic_similarity=0.8,
            fact_weight=0.2,
            concept_weight=0.15,
            emotion_weight=0.3,
        )

        assert weights.semantic_similarity == 0.8
        assert weights.fact_weight == 0.2
        assert weights.concept_weight == 0.15
        assert weights.emotion_weight == 0.3


class TestRetrievalConfig:
    """Tests for RetrievalConfig."""

    def test_retrieval_config_default_values(self):
        """RetrievalConfig should have sensible defaults."""
        from memory.models import RetrievalConfig

        config = RetrievalConfig()

        assert config.n_hops == 2
        assert config.top_k == 3

    def test_retrieval_config_can_be_customized(self):
        """RetrievalConfig can be customized."""
        from memory.models import RetrievalConfig

        config = RetrievalConfig(n_hops=3, top_k=5)

        assert config.n_hops == 3
        assert config.top_k == 5
