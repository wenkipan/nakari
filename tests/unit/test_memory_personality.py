"""TDD tests for DAN memory personality initialization."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import random


class TestBaseEmotions:
    """Tests for base emotion constants."""

    def test_base_emotions_list_has_12_emotions(self):
        """Should have 12 base emotions."""
        from memory.personality import BASE_EMOTIONS

        assert len(BASE_EMOTIONS) == 12

    def test_base_emotions_contains_required_emotions(self):
        """Should contain all required emotions."""
        from memory.personality import BASE_EMOTIONS

        required = [
            "happy",
            "sad",
            "anger",
            "fear",
            "surprise",
            "disgust",
            "love",
            "trust",
            "anticipation",
            "curiosity",
            "calm",
            "anxiety",
        ]

        for emotion in required:
            assert emotion in BASE_EMOTIONS


class TestPersonalityConfig:
    """Tests for PersonalityConfig model."""

    def test_personality_config_has_emotions(self):
        """PersonalityConfig should have emotions field."""
        from memory.personality import PersonalityConfig

        config = PersonalityConfig(emotions=["happy", "sad"])

        assert config.emotions == ["happy", "sad"]

    def test_personality_config_has_preferences(self):
        """PersonalityConfig should have preferences field."""
        from memory.personality import PersonalityConfig, PreferenceItem

        pref = PreferenceItem(
            content="reading", atom_type="concept", emotion="happy", edge_weight=0.8
        )
        config = PersonalityConfig(emotions=[], preferences=[pref])

        assert len(config.preferences) == 1
        assert config.preferences[0].content == "reading"

    def test_personality_config_defaults_to_base_emotions(self):
        """PersonalityConfig should default to BASE_EMOTIONS."""
        from memory.personality import PersonalityConfig, BASE_EMOTIONS

        config = PersonalityConfig()

        assert config.emotions == BASE_EMOTIONS


class TestPreferenceItem:
    """Tests for PreferenceItem model."""

    def test_preference_item_has_required_fields(self):
        """PreferenceItem should have content, type, and emotion."""
        from memory.personality import PreferenceItem

        pref = PreferenceItem(content="coding", atom_type="concept", emotion="happy")

        assert pref.content == "coding"
        assert pref.atom_type == "concept"
        assert pref.emotion == "happy"

    def test_preference_item_has_optional_edge_weight(self):
        """PreferenceItem edge_weight should be optional with default 0.5."""
        from memory.personality import PreferenceItem

        pref = PreferenceItem(content="coding", atom_type="concept", emotion="happy")

        assert pref.edge_weight == 0.5


class TestPersonalityInitializer:
    """Tests for PersonalityInitializer class."""

    def test_initializer_requires_dan_memory(self):
        """PersonalityInitializer should require DANMemory instance."""
        from memory.personality import PersonalityInitializer
        from memory.dan import DANMemory

        mock_dan = MagicMock(spec=DANMemory)

        initializer = PersonalityInitializer(dan=mock_dan)

        assert initializer.dan == mock_dan


class TestInitializeEmotions:
    """Tests for emotion initialization."""

    @pytest.mark.asyncio
    async def test_initialize_emotions_creates_12_emotion_atoms(self):
        """initialize_emotions should create all emotion atoms."""
        from memory.personality import PersonalityInitializer, PersonalityConfig
        from memory.models import Atom, AtomType
        from memory.dan import DANMemory

        mock_dan = AsyncMock(spec=DANMemory)

        atom_counter = [0]

        async def mock_create_atom(content, atom_type, weight, **kwargs):
            atom_counter[0] += 1
            return Atom(
                id=f"emotion_{atom_counter[0]}",
                content=content,
                atom_type=atom_type,
                weight=weight,
            )

        mock_dan.create_atom.side_effect = mock_create_atom

        initializer = PersonalityInitializer(dan=mock_dan)
        config = PersonalityConfig()  # Uses default BASE_EMOTIONS

        await initializer.initialize_emotions(config)

        assert mock_dan.create_atom.call_count == 12

    @pytest.mark.asyncio
    async def test_initialize_emotions_with_random_weights(self):
        """Emotion atoms should have random weights in [0.3, 0.7]."""
        from memory.personality import PersonalityInitializer, PersonalityConfig
        from memory.models import Atom, AtomType
        from memory.dan import DANMemory

        mock_dan = AsyncMock(spec=DANMemory)

        weights_used = []

        async def mock_create_atom(content, atom_type, weight, **kwargs):
            weights_used.append(weight)
            return Atom(
                id=f"emotion_{len(weights_used)}",
                content=content,
                atom_type=atom_type,
                weight=weight,
            )

        mock_dan.create_atom.side_effect = mock_create_atom

        initializer = PersonalityInitializer(dan=mock_dan)
        config = PersonalityConfig()

        # Set seed for reproducibility in test
        random.seed(42)
        await initializer.initialize_emotions(config)

        # All weights should be in [0.3, 0.7]
        for w in weights_used:
            assert 0.3 <= w <= 0.7

    @pytest.mark.asyncio
    async def test_initialize_emotions_uses_emotion_type(self):
        """All created atoms should be of type EMOTION."""
        from memory.personality import PersonalityInitializer, PersonalityConfig
        from memory.models import Atom, AtomType
        from memory.dan import DANMemory

        mock_dan = AsyncMock(spec=DANMemory)

        types_used = []

        async def mock_create_atom(content, atom_type, weight, **kwargs):
            types_used.append(atom_type)
            return Atom(
                id=f"emotion_{len(types_used)}",
                content=content,
                atom_type=atom_type,
                weight=weight,
            )

        mock_dan.create_atom.side_effect = mock_create_atom

        initializer = PersonalityInitializer(dan=mock_dan)
        config = PersonalityConfig()

        await initializer.initialize_emotions(config)

        for t in types_used:
            assert t == AtomType.EMOTION


class TestInitializePreferences:
    """Tests for preference initialization."""

    @pytest.mark.asyncio
    async def test_initialize_preferences_creates_atoms_and_edges(self):
        """initialize_preferences should create atoms and link to emotions."""
        from memory.personality import (
            PersonalityInitializer,
            PersonalityConfig,
            PreferenceItem,
        )
        from memory.models import Atom, AtomType
        from memory.dan import DANMemory, InsertRequest

        mock_dan = AsyncMock(spec=DANMemory)
        mock_dan.insert_data.return_value = Atom(
            id="pref_1", content="coding", atom_type=AtomType.CONCEPT, weight=1.0
        )

        initializer = PersonalityInitializer(dan=mock_dan)

        config = PersonalityConfig(
            emotions=["happy", "curiosity"],
            preferences=[
                PreferenceItem(
                    content="coding",
                    atom_type="concept",
                    emotion="happy",
                    edge_weight=0.8,
                ),
                PreferenceItem(
                    content="learning",
                    atom_type="concept",
                    emotion="curiosity",
                    edge_weight=0.9,
                ),
            ],
        )

        # First initialize emotions so they exist
        emotion_atoms = {}

        async def mock_create_atom(content, atom_type, weight, **kwargs):
            atom = Atom(
                id=f"emotion_{content}",
                content=content,
                atom_type=atom_type,
                weight=weight,
            )
            emotion_atoms[content] = atom
            return atom

        mock_dan.create_atom.side_effect = mock_create_atom

        await initializer.initialize_emotions(config)
        await initializer.initialize_preferences(config, emotion_atoms)

        # Should call insert_data for each preference
        assert mock_dan.insert_data.call_count == 2


class TestInitializePersonality:
    """Tests for full personality initialization."""

    @pytest.mark.asyncio
    async def test_initialize_personality_full_flow(self):
        """initialize_personality should run complete initialization."""
        from memory.personality import (
            PersonalityInitializer,
            PersonalityConfig,
            PreferenceItem,
        )
        from memory.models import Atom, AtomType
        from memory.dan import DANMemory

        mock_dan = AsyncMock(spec=DANMemory)

        atoms_created = []

        async def mock_create_atom(content, atom_type, weight, **kwargs):
            atom = Atom(
                id=f"atom_{len(atoms_created)}",
                content=content,
                atom_type=atom_type,
                weight=weight,
            )
            atoms_created.append(atom)
            return atom

        mock_dan.create_atom.side_effect = mock_create_atom

        mock_dan.insert_data.return_value = Atom(
            id="pref_1", content="test", atom_type=AtomType.CONCEPT, weight=1.0
        )

        initializer = PersonalityInitializer(dan=mock_dan)

        config = PersonalityConfig(
            preferences=[
                PreferenceItem(
                    content="coding",
                    atom_type="concept",
                    emotion="happy",
                    edge_weight=0.8,
                ),
            ]
        )

        await initializer.initialize_personality(config)

        # Should create 12 emotion atoms
        assert mock_dan.create_atom.call_count == 12
        # Should insert preferences
        assert mock_dan.insert_data.call_count == 1


class TestLoadConfigFromYAML:
    """Tests for loading config from YAML."""

    def test_load_config_from_yaml_string(self):
        """Should parse YAML config string."""
        from memory.personality import load_config_from_yaml

        yaml_content = """
emotions:
  - happy
  - sad
preferences:
  - content: coding
    atom_type: concept
    emotion: happy
    edge_weight: 0.8
"""
        config = load_config_from_yaml(yaml_content)

        assert config.emotions == ["happy", "sad"]
        assert len(config.preferences) == 1
        assert config.preferences[0].content == "coding"

    def test_load_config_uses_defaults_for_missing_fields(self):
        """Should use defaults when fields are missing."""
        from memory.personality import load_config_from_yaml, BASE_EMOTIONS

        yaml_content = """
preferences: []
"""
        config = load_config_from_yaml(yaml_content)

        assert config.emotions == BASE_EMOTIONS
