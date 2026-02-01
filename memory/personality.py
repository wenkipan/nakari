from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml

from memory.embedding import EmbeddingProvider
from memory.models import Atom
from memory.neo4j_store import Neo4jMemoryStore


def load_persona_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def init_personality(
    *,
    store: Neo4jMemoryStore,
    embedder: EmbeddingProvider,
    persona_yaml_path: str,
    rng_seed: Optional[int] = 0,
) -> None:
    cfg = load_persona_config(persona_yaml_path)
    emotions_cfg = cfg.get("emotions", {})
    init_range = emotions_cfg.get("init_range", [0.3, 0.7])
    emotion_types = emotions_cfg.get("types", [])

    rng = random.Random(rng_seed)
    now = datetime.now(tz=timezone.utc)

    for e in emotion_types:
        strength = float(rng.uniform(float(init_range[0]), float(init_range[1])))
        store.create_atom(
            Atom(
                content=str(e),
                embedding=embedder.embed(str(e)),
                type="emotion",
                strength=strength,
                timestamp=now,
            )
        )

    prefs = cfg.get("preferences", {})

    for concept in prefs.get("concepts", []) or []:
        c_content = concept.get("content")
        if not c_content:
            continue
        store.create_atom(
            Atom(
                content=c_content,
                embedding=embedder.embed(c_content),
                type="concept",
                strength=0.0,
                timestamp=now,
            )
        )
        for emotion, weight in (concept.get("emotions") or {}).items():
            store.create_link(
                c_content, str(emotion), weight=float(weight), timestamp=now
            )

    for fact in prefs.get("facts", []) or []:
        f_content = fact.get("content")
        if not f_content:
            continue
        store.create_atom(
            Atom(
                content=f_content,
                embedding=embedder.embed(f_content),
                type="fact",
                strength=0.0,
                timestamp=now,
            )
        )
        for emotion, weight in (fact.get("emotions") or {}).items():
            store.create_link(
                f_content, str(emotion), weight=float(weight), timestamp=now
            )
