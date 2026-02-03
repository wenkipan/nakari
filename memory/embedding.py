"""DAN Memory Embedding - Interfaces and implementations for text embeddings.

This module provides an abstract interface for embedding providers
and a unified OpenAI-compatible implementation that works with any provider
following the OpenAI API format (OpenAI, Zhipu, Moonshot, DeepSeek, etc.).
"""

import abc
import hashlib
from typing import List, Optional

import httpx

from memory.config import EmbeddingConfig


class EmbeddingProvider(abc.ABC):
    """Abstract base class for embedding providers.

    Implementations should provide methods to convert text to vector embeddings.
    """

    @abc.abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Convert a single text to an embedding vector.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        pass

    @abc.abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        pass


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """Unified embedding provider for any OpenAI-compatible API.

    Works with OpenAI, Zhipu (智谱), Moonshot, DeepSeek, and any other
    provider that follows the OpenAI embeddings API format.

    API format expected:
        POST /embeddings
        Request: {"input": "text" or ["text1", "text2"], "model": "model-name"}
        Response: {"data": [{"embedding": [0.1, 0.2, ...]}]}
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        api_base: str,
        timeout: float = 60.0,
    ):
        """Initialize the embedding provider.

        Args:
            api_key: API key for the service.
            model: Model name to use for embeddings.
            api_base: Base URL for the API (e.g., https://api.openai.com/v1).
            timeout: Request timeout in seconds (default: 60.0).
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self._client = httpx.AsyncClient(
            base_url=api_base,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    @classmethod
    def from_config(
        cls, config: EmbeddingConfig
    ) -> "OpenAICompatibleEmbeddingProvider":
        """Create provider from EmbeddingConfig.

        Args:
            config: EmbeddingConfig instance.

        Returns:
            Configured provider instance.
        """
        return cls(
            api_key=config.api_key,
            model=config.model,
            api_base=config.api_base,
        )

    @classmethod
    def from_env(cls) -> "OpenAICompatibleEmbeddingProvider":
        """Create provider from environment variables.

        Reads EMBEDDING_API_BASE, EMBEDDING_API_KEY, EMBEDDING_MODEL.

        Returns:
            Configured provider instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        config = EmbeddingConfig.from_env()
        return cls.from_config(config)

    async def _call_api(self, input_data: str | List[str]) -> dict:
        """Make API call to embeddings endpoint.

        Args:
            input_data: Single text or list of texts to embed.

        Returns:
            API response as dictionary.
        """
        response = await self._client.post(
            "/embeddings",
            json={"input": input_data, "model": self.model},
        )
        response.raise_for_status()
        return response.json()

    async def embed(self, text: str) -> List[float]:
        """Convert a single text to an embedding vector.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        response = await self._call_api(text)
        return response["data"][0]["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        response = await self._call_api(texts)
        # Sort by index to ensure correct order
        sorted_data = sorted(response["data"], key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in sorted_data]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


# Alias for backward compatibility
OpenAIEmbeddingProvider = OpenAICompatibleEmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing without API calls.

    Generates deterministic pseudo-embeddings based on text hash.
    """

    def __init__(self, dimension: int = 1536):
        """Initialize mock provider.

        Args:
            dimension: Dimension of the embedding vectors.
        """
        self.dimension = dimension

    def _hash_to_vector(self, text: str) -> List[float]:
        """Convert text to a deterministic vector using hash.

        Args:
            text: Text to convert.

        Returns:
            Deterministic vector of floats.
        """
        # Use SHA-256 and extend to fill dimension
        hash_bytes = hashlib.sha256(text.encode()).digest()

        # Convert bytes to floats in [-1, 1] range
        vector = []
        for i in range(self.dimension):
            # Cycle through hash bytes
            byte_idx = i % len(hash_bytes)
            # Normalize to [-1, 1]
            value = (hash_bytes[byte_idx] / 255.0) * 2 - 1
            # Add some variation based on position
            value = (value + (i % 256) / 256.0) / 2
            vector.append(value)

        return vector

    async def embed(self, text: str) -> List[float]:
        """Generate a deterministic embedding for text.

        Args:
            text: The text to embed.

        Returns:
            Deterministic embedding vector.
        """
        return self._hash_to_vector(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of deterministic embedding vectors.
        """
        return [self._hash_to_vector(text) for text in texts]
