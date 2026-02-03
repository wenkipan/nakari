"""DAN Memory Personality Initialization Module.

This module provides personality initialization for the DAN memory system:
- BASE_EMOTIONS: List of 12 core emotions
- PreferenceItem: Model for preference configuration
- PersonalityConfig: Configuration for personality setup
- PersonalityInitializer: Class to initialize emotions and preferences
- load_config_from_yaml: Parse YAML configuration
"""

import random
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from memory.dan import DANMemory, InsertRequest, RelatedAtom
from memory.models import Atom, AtomType


# 12 base emotions as defined in arcV3.md
BASE_EMOTIONS: List[str] = [
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


class PreferenceItem(BaseModel):
    """A preference item for personality configuration.

    Attributes:
        content: The content of the preference (e.g., "coding").
        atom_type: Type of atom (e.g., "concept", "fact").
        emotion: The emotion to link this preference to.
        edge_weight: Weight of the edge to the emotion (default 0.5).
    """

    content: str
    atom_type: str
    emotion: str
    edge_weight: float = 0.5


class PersonalityConfig(BaseModel):
    """Configuration for personality initialization.

    Attributes:
        emotions: List of emotions to initialize (defaults to BASE_EMOTIONS).
        preferences: List of preferences to initialize.
    """

    emotions: List[str] = Field(default_factory=lambda: list(BASE_EMOTIONS))
    preferences: List[PreferenceItem] = Field(default_factory=list)


class PersonalityInitializer:
    """Initializer for DAN memory personality.

    Creates emotion atoms and preference atoms with edges to emotions.
    """

    def __init__(self, dan: DANMemory):
        """Initialize with a DANMemory instance.

        Args:
            dan: The DANMemory instance to use for atom creation.
        """
        self.dan = dan

    async def initialize_emotions(self, config: PersonalityConfig) -> Dict[str, Atom]:
        """Initialize emotion atoms with random weights.

        Creates an atom for each emotion in the config with a random
        weight in the range [0.3, 0.7].

        Args:
            config: Personality configuration with emotions list.

        Returns:
            Dictionary mapping emotion names to their atoms.
        """
        emotion_atoms: Dict[str, Atom] = {}

        for emotion in config.emotions:
            # Random weight in [0.3, 0.7] as per arcV3.md
            weight = random.uniform(0.3, 0.7)

            atom = await self.dan.create_atom(
                content=emotion,
                atom_type=AtomType.EMOTION,
                weight=weight,
            )
            emotion_atoms[emotion] = atom

        return emotion_atoms

    async def initialize_preferences(
        self,
        config: PersonalityConfig,
        emotion_atoms: Dict[str, Atom],
    ) -> List[Atom]:
        """Initialize preference atoms with edges to emotions.

        Creates atoms for each preference and links them to their
        corresponding emotion atoms.

        Args:
            config: Personality configuration with preferences list.
            emotion_atoms: Dictionary of emotion atoms from initialize_emotions.

        Returns:
            List of created preference atoms.
        """
        preference_atoms: List[Atom] = []

        for pref in config.preferences:
            # Map string atom_type to AtomType enum
            atom_type = AtomType(pref.atom_type)

            # Get the emotion atom to link to
            emotion_atom = emotion_atoms.get(pref.emotion)

            # Build related atoms list (the emotion)
            related: List[RelatedAtom] = []
            if emotion_atom:
                related.append(
                    RelatedAtom(
                        content=emotion_atom.content,
                        atom_type=AtomType.EMOTION,
                        edge_weight=pref.edge_weight,
                    )
                )

            # Create insert request
            request = InsertRequest(
                main=RelatedAtom(
                    content=pref.content,
                    atom_type=atom_type,
                ),
                related=related,
            )

            atom = await self.dan.insert_data(request)
            preference_atoms.append(atom)

        return preference_atoms

    async def initialize_personality(
        self, config: PersonalityConfig
    ) -> Dict[str, Atom]:
        """Initialize complete personality with emotions and preferences.

        This method:
        1. Initializes all emotion atoms
        2. Initializes all preferences with edges to emotions

        Args:
            config: Personality configuration.

        Returns:
            Dictionary of emotion atoms.
        """
        # Initialize emotions first
        emotion_atoms = await self.initialize_emotions(config)

        # Then initialize preferences
        await self.initialize_preferences(config, emotion_atoms)

        return emotion_atoms


def load_config_from_yaml(yaml_content: str) -> PersonalityConfig:
    """Load personality configuration from YAML string.

    Args:
        yaml_content: YAML string with personality configuration.

    Returns:
        PersonalityConfig parsed from YAML.
    """
    data = yaml.safe_load(yaml_content)

    # Handle empty or None data
    if data is None:
        data = {}

    # Parse preferences if present
    preferences: List[PreferenceItem] = []
    if "preferences" in data and data["preferences"]:
        for pref_data in data["preferences"]:
            preferences.append(PreferenceItem(**pref_data))

    # Build config, using defaults if fields are missing
    config_data: Dict = {"preferences": preferences}

    if "emotions" in data and data["emotions"]:
        config_data["emotions"] = data["emotions"]

    return PersonalityConfig(**config_data)
