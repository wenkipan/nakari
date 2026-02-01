from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryConfig:
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    dan_embedding_dim: int

    @staticmethod
    def from_env() -> "MemoryConfig":
        return MemoryConfig(
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_username=os.environ.get("NEO4J_USERNAME", "neo4j"),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", "password"),
            dan_embedding_dim=int(os.environ.get("DAN_EMBEDDING_DIM", "1536")),
        )
