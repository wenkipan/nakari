from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from neo4j import GraphDatabase

from memory.config import MemoryConfig
from memory.constants import ATOM_LABEL
from memory.models import Atom


class Neo4jMemoryStore:
    def __init__(self, config: MemoryConfig) -> None:
        self._cfg = config
        self._driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_username, config.neo4j_password),
        )

    def close(self) -> None:
        self._driver.close()

    def reset_all(self) -> None:
        with self._driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")

    def ensure_schema(self) -> None:
        with self._driver.session() as s:
            s.run(
                "CREATE CONSTRAINT atom_content_unique IF NOT EXISTS "
                "FOR (a:%s) REQUIRE a.content IS UNIQUE" % ATOM_LABEL
            )

    def create_atom(self, atom: Atom) -> None:
        with self._driver.session() as s:
            s.run(
                "MERGE (a:%s {content: $content}) "
                "SET a.type = $type, a.embedding = $embedding, a.strength = $strength, "
                "a.timestamp = $timestamp, a.extensions = $extensions" % ATOM_LABEL,
                content=atom.content,
                type=atom.type,
                embedding=atom.embedding,
                strength=atom.strength,
                timestamp=atom.timestamp.isoformat(),
                extensions=json.dumps(atom.extensions),
            )

    def get_atom(self, content: str) -> Optional[Atom]:
        with self._driver.session() as s:
            rec = s.run(
                "MATCH (a:%s {content: $content}) RETURN a" % ATOM_LABEL,
                content=content,
            ).single()
            if not rec:
                return None
            node = rec["a"]
            ext_raw = node.get("extensions") or "{}"
            return Atom(
                content=node["content"],
                embedding=list(node.get("embedding") or []),
                type=node.get("type"),
                strength=float(node.get("strength") or 0.0),
                timestamp=datetime.fromisoformat(node.get("timestamp")),
                extensions=json.loads(ext_raw),
            )
