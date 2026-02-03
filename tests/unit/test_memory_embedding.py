"""TDD tests for DAN memory embedding interfaces."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List


class TestEmbeddingProvider:
    """Tests for abstract EmbeddingProvider interface."""

    def test_embedding_provider_is_abstract(self):
        """EmbeddingProvider should be an abstract base class."""
        from memory.embedding import EmbeddingProvider
        import abc

        assert issubclass(EmbeddingProvider, abc.ABC)

    def test_embedding_provider_has_embed_method(self):
        """EmbeddingProvider should have abstract embed method."""
        from memory.embedding import EmbeddingProvider

        # Check that embed is an abstract method
        assert hasattr(EmbeddingProvider, "embed")
        assert getattr(EmbeddingProvider.embed, "__isabstractmethod__", False)

    def test_embedding_provider_has_embed_batch_method(self):
        """EmbeddingProvider should have abstract embed_batch method."""
        from memory.embedding import EmbeddingProvider

        assert hasattr(EmbeddingProvider, "embed_batch")
        assert getattr(EmbeddingProvider.embed_batch, "__isabstractmethod__", False)


class TestOpenAICompatibleEmbeddingProvider:
    """Tests for OpenAI-compatible embedding provider implementation."""

    def test_provider_is_embedding_provider(self):
        """OpenAICompatibleEmbeddingProvider should inherit from EmbeddingProvider."""
        from memory.embedding import (
            EmbeddingProvider,
            OpenAICompatibleEmbeddingProvider,
        )

        assert issubclass(OpenAICompatibleEmbeddingProvider, EmbeddingProvider)

    def test_provider_requires_api_key(self):
        """Provider should require API key."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-small",
            api_base="https://api.openai.com/v1",
        )
        assert provider.api_key == "test-key"

    def test_provider_requires_model(self):
        """Provider should require model."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="embedding-3-pro",
            api_base="https://open.bigmodel.cn/api/paas/v4",
        )
        assert provider.model == "embedding-3-pro"

    def test_provider_requires_api_base(self):
        """Provider should require api_base."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-small",
            api_base="https://api.openai.com/v1",
        )
        assert provider.api_base == "https://api.openai.com/v1"

    def test_provider_works_with_openai(self):
        """Provider should work with OpenAI API."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="sk-openai-key",
            model="text-embedding-3-small",
            api_base="https://api.openai.com/v1",
        )
        assert provider.api_base == "https://api.openai.com/v1"
        assert provider.model == "text-embedding-3-small"

    def test_provider_works_with_zhipu(self):
        """Provider should work with Zhipu API."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="zhipu-key",
            model="embedding-3-pro",
            api_base="https://open.bigmodel.cn/api/paas/v4",
        )
        assert provider.api_base == "https://open.bigmodel.cn/api/paas/v4"
        assert provider.model == "embedding-3-pro"

    def test_provider_works_with_moonshot(self):
        """Provider should work with Moonshot API."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="moonshot-key",
            model="moonshot-v1-8k",
            api_base="https://api.moonshot.cn/v1",
        )
        assert provider.api_base == "https://api.moonshot.cn/v1"

    @pytest.mark.asyncio
    async def test_embed_returns_list_of_floats(self):
        """embed() should return a list of floats."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="test-model",
            api_base="https://api.test.com/v1",
        )

        # Mock the HTTP client
        mock_response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            result = await provider.embed("test text")

            assert isinstance(result, list)
            assert all(isinstance(x, float) for x in result)
            assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_batch_returns_list_of_embeddings(self):
        """embed_batch() should return list of embedding vectors."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="test-model",
            api_base="https://api.test.com/v1",
        )

        mock_response = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                {"index": 1, "embedding": [0.4, 0.5, 0.6]},
            ]
        }

        with patch.object(provider, "_call_api", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            result = await provider.embed_batch(["text1", "text2"])

            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_embed_batch_handles_empty_input(self):
        """embed_batch() should handle empty input list."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="test-model",
            api_base="https://api.test.com/v1",
        )

        result = await provider.embed_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_provider_has_close_method(self):
        """Provider should have close method for cleanup."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider

        provider = OpenAICompatibleEmbeddingProvider(
            api_key="test-key",
            model="test-model",
            api_base="https://api.test.com/v1",
        )

        assert hasattr(provider, "close")
        # Should not raise
        with patch.object(provider._client, "aclose", new_callable=AsyncMock):
            await provider.close()

    def test_from_config_creates_provider(self):
        """from_config should create provider from EmbeddingConfig."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider
        from memory.config import EmbeddingConfig

        config = EmbeddingConfig(
            api_base="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )

        provider = OpenAICompatibleEmbeddingProvider.from_config(config)

        assert provider.api_base == "https://api.test.com/v1"
        assert provider.api_key == "test-key"
        assert provider.model == "test-model"

    def test_from_env_creates_provider(self):
        """from_env should create provider from environment variables."""
        from memory.embedding import OpenAICompatibleEmbeddingProvider
        import os

        with patch.dict(
            os.environ,
            {
                "EMBEDDING_API_BASE": "https://api.test.com/v1",
                "EMBEDDING_API_KEY": "test-key",
                "EMBEDDING_MODEL": "test-model",
            },
        ):
            provider = OpenAICompatibleEmbeddingProvider.from_env()

            assert provider.api_base == "https://api.test.com/v1"
            assert provider.api_key == "test-key"
            assert provider.model == "test-model"


class TestOpenAIEmbeddingProviderAlias:
    """Tests for backward compatibility alias."""

    def test_alias_exists(self):
        """OpenAIEmbeddingProvider should be an alias for OpenAICompatibleEmbeddingProvider."""
        from memory.embedding import (
            OpenAIEmbeddingProvider,
            OpenAICompatibleEmbeddingProvider,
        )

        assert OpenAIEmbeddingProvider is OpenAICompatibleEmbeddingProvider


class TestMockEmbeddingProvider:
    """Tests for mock embedding provider (for testing without API)."""

    def test_mock_provider_is_embedding_provider(self):
        """MockEmbeddingProvider should inherit from EmbeddingProvider."""
        from memory.embedding import EmbeddingProvider, MockEmbeddingProvider

        assert issubclass(MockEmbeddingProvider, EmbeddingProvider)

    @pytest.mark.asyncio
    async def test_mock_provider_embed_returns_deterministic_vector(self):
        """MockEmbeddingProvider should return deterministic vectors."""
        from memory.embedding import MockEmbeddingProvider

        provider = MockEmbeddingProvider(dimension=4)

        result1 = await provider.embed("test text")
        result2 = await provider.embed("test text")

        assert result1 == result2
        assert len(result1) == 4

    @pytest.mark.asyncio
    async def test_mock_provider_different_texts_different_vectors(self):
        """Different texts should produce different vectors."""
        from memory.embedding import MockEmbeddingProvider

        provider = MockEmbeddingProvider(dimension=4)

        result1 = await provider.embed("text1")
        result2 = await provider.embed("text2")

        assert result1 != result2

    @pytest.mark.asyncio
    async def test_mock_provider_embed_batch(self):
        """MockEmbeddingProvider should support batch embedding."""
        from memory.embedding import MockEmbeddingProvider

        provider = MockEmbeddingProvider(dimension=4)

        results = await provider.embed_batch(["text1", "text2", "text3"])

        assert len(results) == 3
        assert all(len(v) == 4 for v in results)


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    def test_config_creation(self):
        """EmbeddingConfig should be creatable with required fields."""
        from memory.config import EmbeddingConfig

        config = EmbeddingConfig(
            api_base="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )

        assert config.api_base == "https://api.test.com/v1"
        assert config.api_key == "test-key"
        assert config.model == "test-model"

    def test_config_from_env(self):
        """EmbeddingConfig.from_env should load from environment."""
        from memory.config import EmbeddingConfig
        import os

        with patch.dict(
            os.environ,
            {
                "EMBEDDING_API_BASE": "https://api.test.com/v1",
                "EMBEDDING_API_KEY": "test-key",
                "EMBEDDING_MODEL": "test-model",
            },
        ):
            config = EmbeddingConfig.from_env()

            assert config.api_base == "https://api.test.com/v1"
            assert config.api_key == "test-key"
            assert config.model == "test-model"

    def test_config_from_env_raises_on_missing(self):
        """EmbeddingConfig.from_env should raise if env vars missing."""
        from memory.config import EmbeddingConfig
        import os

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                EmbeddingConfig.from_env()

            assert "EMBEDDING_API_BASE" in str(exc_info.value)
