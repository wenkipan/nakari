from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Tuple

from neo4j import GraphDatabase

from memory.config import MemoryConfig
from memory.constants import ATOM_LABEL, LINK_REL_TYPE
from memory.models import Atom, Link


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

    def create_link(
        self,
        source: str,
        target: str,
        *,
        weight: float,
        timestamp: datetime,
    ) -> None:
        with self._driver.session() as s:
            s.run(
                "MATCH (a:%s {content: $source}), (b:%s {content: $target}) "
                "MERGE (a)-[r:%s]-(b) "
                "SET r.weight = $weight, r.timestamp = $timestamp"
                % (ATOM_LABEL, ATOM_LABEL, LINK_REL_TYPE),
                source=source,
                target=target,
                weight=float(weight),
                timestamp=timestamp.isoformat(),
            )

    def get_link(self, source: str, target: str) -> Optional[Link]:
        with self._driver.session() as s:
            rec = s.run(
                "MATCH (a:%s {content: $source})-[r:%s]-(b:%s {content: $target}) RETURN r"
                % (ATOM_LABEL, LINK_REL_TYPE, ATOM_LABEL),
                source=source,
                target=target,
            ).single()
            if not rec:
                return None
            rel = rec["r"]
            return Link(
                source=source,
                target=target,
                weight=float(rel.get("weight") or 0.0),
                timestamp=datetime.fromisoformat(rel.get("timestamp")),
            )

    def ensure_vector_index(self) -> None:
        with self._driver.session() as s:
            s.run(
                "CREATE VECTOR INDEX atom_embedding_index IF NOT EXISTS "
                "FOR (a:%s) ON (a.embedding) "
                "OPTIONS {indexConfig: {`vector.dimensions`: $dim, `vector.similarity_function`: 'cosine'}}"
                % ATOM_LABEL,
                dim=int(self._cfg.dan_embedding_dim),
            )

    def vector_search(
        self, embedding: List[float], k: int
    ) -> List[Tuple[object, float]]:
        with self._driver.session() as s:
            res = s.run(
                "CALL db.index.vector.queryNodes('atom_embedding_index', $k, $embedding) "
                "YIELD node, score RETURN node, score",
                k=int(k),
                embedding=embedding,
            )
            return [(r["node"], float(r["score"])) for r in res]

    def neighbors_1hop(self, content: str, limit: int = 50) -> List[object]:
        with self._driver.session() as s:
            res = s.run(
                "MATCH (a:%s {content:$content})-[:%s]-(b:%s) RETURN b LIMIT $limit"
                % (ATOM_LABEL, LINK_REL_TYPE, ATOM_LABEL),
                content=content,
                limit=int(limit),
            )
            return [r["b"] for r in res]

    def _node_to_atom(self, node: object) -> Atom:
        ext_raw = node.get("extensions") or "{}"
        return Atom(
            content=node["content"],
            embedding=list(node.get("embedding") or []),
            type=node.get("type"),
            strength=float(node.get("strength") or 0.0),
            timestamp=datetime.fromisoformat(node.get("timestamp")),
            extensions=json.loads(ext_raw),
        )
