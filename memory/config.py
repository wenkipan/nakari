"""DAN Memory Configuration - Unified configuration management.

This module provides centralized configuration loading from environment variables.
All LLM/Embedding providers use OpenAI-compatible API format.

Environment Variables:
    EMBEDDING_API_BASE: Base URL for embedding API (e.g., https://open.bigmodel.cn/api/paas/v4)
    EMBEDDING_API_KEY: API key for embedding service
    EMBEDDING_MODEL: Model name (e.g., embedding-3-pro, text-embedding-3-small)

    LLM_API_BASE: Base URL for LLM API
    LLM_API_KEY: API key for LLM service
    LLM_MODEL: Model name (e.g., glm-4, gpt-4)
    LLM_MAX_TOKENS: Maximum tokens for LLM responses

    NEO4J_URI: Neo4j connection URI (e.g., bolt://localhost:7687)
    NEO4J_USERNAME: Neo4j username
    NEO4J_PASSWORD: Neo4j password
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Configuration for embedding provider."""

    api_base: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Load configuration from environment variables.

        Returns:
            EmbeddingConfig instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        api_base = os.getenv("EMBEDDING_API_BASE")
        api_key = os.getenv("EMBEDDING_API_KEY")
        model = os.getenv("EMBEDDING_MODEL")

        missing = []
        if not api_base:
            missing.append("EMBEDDING_API_BASE")
        if not api_key:
            missing.append("EMBEDDING_API_KEY")
        if not model:
            missing.append("EMBEDDING_MODEL")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(api_base=api_base, api_key=api_key, model=model)


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""

    api_base: str
    api_key: str
    model: str
    max_tokens: int = 4096

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables.

        Returns:
            LLMConfig instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        api_base = os.getenv("LLM_API_BASE")
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL")
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

        missing = []
        if not api_base:
            missing.append("LLM_API_BASE")
        if not api_key:
            missing.append("LLM_API_KEY")
        if not model:
            missing.append("LLM_MODEL")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(
            api_base=api_base, api_key=api_key, model=model, max_tokens=max_tokens
        )


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j database."""

    uri: str
    username: str
    password: str
    database: str = "neo4j"

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Load configuration from environment variables.

        Returns:
            Neo4jConfig instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")

        missing = []
        if not uri:
            missing.append("NEO4J_URI")
        if not username:
            missing.append("NEO4J_USERNAME")
        if not password:
            missing.append("NEO4J_PASSWORD")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(uri=uri, username=username, password=password, database=database)


@dataclass
class MemoryConfig:
    """Complete configuration for DAN memory system."""

    embedding: EmbeddingConfig
    neo4j: Neo4jConfig
    llm: Optional[LLMConfig] = None

    @classmethod
    def from_env(cls, require_llm: bool = False) -> "MemoryConfig":
        """Load all configuration from environment variables.

        Args:
            require_llm: If True, raise error if LLM config is missing.

        Returns:
            MemoryConfig instance.
        """
        embedding = EmbeddingConfig.from_env()
        neo4j = Neo4jConfig.from_env()

        llm = None
        if require_llm:
            llm = LLMConfig.from_env()
        else:
            # Try to load LLM config, but don't fail if missing
            try:
                llm = LLMConfig.from_env()
            except ValueError:
                pass

        return cls(embedding=embedding, neo4j=neo4j, llm=llm)
