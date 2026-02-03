"""TDD tests for DAN memory module - main DAN class."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List


class TestDANMemoryInit:
    """Tests for DANMemory initialization."""

    def test_dan_memory_requires_store(self):
        """DANMemory should require an AtomStore."""
        from memory.dan import DANMemory
        from memory.store import AtomStore

        mock_store = MagicMock(spec=AtomStore)
        mock_embedding = MagicMock()

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        assert dan.store == mock_store

    def test_dan_memory_requires_embedding_provider(self):
        """DANMemory should require an EmbeddingProvider."""
        from memory.dan import DANMemory
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = MagicMock(spec=AtomStore)
        mock_embedding = MagicMock(spec=EmbeddingProvider)

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        assert dan.embedding_provider == mock_embedding


class TestDANMemoryCreateAtom:
    """Tests for DANMemory.create_atom method."""

    @pytest.mark.asyncio
    async def test_create_atom_generates_embedding(self):
        """create_atom should generate embedding for the content."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed.return_value = [0.1, 0.2, 0.3]

        # Mock store to return atom with id
        async def mock_create(atom):
            return Atom(
                id="atom_123",
                content=atom.content,
                atom_type=atom.atom_type,
                embedding=atom.embedding,
                weight=atom.weight,
            )

        mock_store.create_atom.side_effect = mock_create

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        result = await dan.create_atom(
            content="Wenki在熬夜", atom_type=AtomType.FACT, weight=0.8
        )

        mock_embedding.embed.assert_called_once_with("Wenki在熬夜")
        assert result.embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_create_atom_returns_atom_with_id(self):
        """create_atom should return atom with database ID."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed.return_value = [0.1, 0.2]

        mock_store.create_atom.return_value = Atom(
            id="atom_123",
            content="test",
            atom_type=AtomType.FACT,
            embedding=[0.1, 0.2],
        )

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        result = await dan.create_atom(content="test", atom_type=AtomType.FACT)

        assert result.id == "atom_123"


class TestDANMemoryInsertData:
    """Tests for DANMemory.insert_data method."""

    @pytest.mark.asyncio
    async def test_insert_data_creates_main_atom(self):
        """insert_data should create the main atom."""
        from memory.dan import DANMemory, InsertRequest, RelatedAtom
        from memory.models import Atom, AtomType
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed.return_value = [0.1, 0.2]
        mock_store.get_atom_by_content.return_value = None  # Atom doesn't exist

        mock_store.create_atom.return_value = Atom(
            id="main_123",
            content="Wenki在熬夜",
            atom_type=AtomType.FACT,
            embedding=[0.1, 0.2],
        )

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        request = InsertRequest(
            main=RelatedAtom(
                content="Wenki在熬夜", atom_type=AtomType.FACT, weight=0.8
            ),
            related=[],
        )

        result = await dan.insert_data(request)

        assert mock_store.create_atom.called

    @pytest.mark.asyncio
    async def test_insert_data_creates_related_atoms(self):
        """insert_data should create related atoms and edges."""
        from memory.dan import DANMemory, InsertRequest, RelatedAtom
        from memory.models import Atom, AtomType
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed.return_value = [0.1, 0.2]
        mock_store.get_atom_by_content.return_value = None

        atom_counter = [0]

        async def mock_create_atom(atom):
            atom_counter[0] += 1
            return Atom(
                id=f"atom_{atom_counter[0]}",
                content=atom.content,
                atom_type=atom.atom_type,
                embedding=atom.embedding,
            )

        mock_store.create_atom.side_effect = mock_create_atom

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        request = InsertRequest(
            main=RelatedAtom(
                content="Wenki在熬夜", atom_type=AtomType.FACT, weight=0.8
            ),
            related=[
                RelatedAtom(
                    content="Wenki", atom_type=AtomType.CONCEPT, edge_weight=0.8
                ),
                RelatedAtom(
                    content="熬夜", atom_type=AtomType.CONCEPT, edge_weight=0.6
                ),
            ],
        )

        await dan.insert_data(request)

        # Should create 3 atoms (1 main + 2 related)
        assert mock_store.create_atom.call_count == 3
        # Should create 2 edges (main to each related)
        assert mock_store.create_edge.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_data_reuses_existing_atoms(self):
        """insert_data should reuse atoms that already exist by content."""
        from memory.dan import DANMemory, InsertRequest, RelatedAtom
        from memory.models import Atom, AtomType
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed.return_value = [0.1, 0.2]

        # First call returns None (main atom doesn't exist)
        # Second call returns existing atom (Wenki exists)
        existing_atom = Atom(
            id="existing_1",
            content="Wenki",
            atom_type=AtomType.CONCEPT,
            embedding=[0.1, 0.2],
        )
        mock_store.get_atom_by_content.side_effect = [None, existing_atom, None]

        atom_counter = [0]

        async def mock_create_atom(atom):
            atom_counter[0] += 1
            return Atom(
                id=f"new_{atom_counter[0]}",
                content=atom.content,
                atom_type=atom.atom_type,
                embedding=atom.embedding,
            )

        mock_store.create_atom.side_effect = mock_create_atom

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        request = InsertRequest(
            main=RelatedAtom(
                content="Wenki在熬夜", atom_type=AtomType.FACT, weight=0.8
            ),
            related=[
                RelatedAtom(
                    content="Wenki", atom_type=AtomType.CONCEPT, edge_weight=0.8
                ),
                RelatedAtom(
                    content="熬夜", atom_type=AtomType.CONCEPT, edge_weight=0.6
                ),
            ],
        )

        await dan.insert_data(request)

        # Should only create 2 atoms (main + 熬夜, but not Wenki which exists)
        assert mock_store.create_atom.call_count == 2


class TestDANMemoryRetrieve:
    """Tests for DANMemory.retrieve method."""

    @pytest.mark.asyncio
    async def test_retrieve_does_vector_search(self):
        """retrieve should do vector search for each query."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType, RetrievalConfig, RetrievalWeights
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_store.vector_search.return_value = [
            (
                Atom(
                    id="a1",
                    content="test",
                    atom_type=AtomType.FACT,
                    embedding=[0.1, 0.2],
                ),
                0.9,
            )
        ]
        mock_store.get_neighbors.return_value = []

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        await dan.retrieve(queries=["query1", "query2"])

        mock_embedding.embed_batch.assert_called_once_with(["query1", "query2"])
        assert mock_store.vector_search.call_count == 2

    @pytest.mark.asyncio
    async def test_retrieve_expands_n_hops(self):
        """retrieve should expand search n_hops from seeds."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType, RetrievalConfig
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed_batch.return_value = [[0.1, 0.2]]

        seed_atom = Atom(
            id="seed", content="seed", atom_type=AtomType.FACT, embedding=[0.1, 0.2]
        )
        neighbor_atom = Atom(
            id="neighbor",
            content="neighbor",
            atom_type=AtomType.CONCEPT,
            embedding=[0.2, 0.3],
        )

        mock_store.vector_search.return_value = [(seed_atom, 0.9)]
        mock_store.get_neighbors.side_effect = [
            [neighbor_atom],  # First hop from seed
            [],  # Second hop from neighbor
        ]

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        config = RetrievalConfig(n_hops=2, top_k=5)
        results = await dan.retrieve(queries=["query"], config=config)

        # Should call get_neighbors for expansion
        assert mock_store.get_neighbors.call_count >= 1

    @pytest.mark.asyncio
    async def test_retrieve_returns_top_k_atoms(self):
        """retrieve should return top_k scored atoms."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType, RetrievalConfig
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed_batch.return_value = [[0.1, 0.2]]

        atoms = [
            Atom(
                id=f"a{i}",
                content=f"content{i}",
                atom_type=AtomType.FACT,
                embedding=[0.1 * i, 0.2 * i],
                weight=0.5,
            )
            for i in range(10)
        ]
        mock_store.vector_search.return_value = [
            (a, 0.9 - 0.1 * i) for i, a in enumerate(atoms)
        ]
        mock_store.get_neighbors.return_value = []

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        config = RetrievalConfig(n_hops=0, top_k=3)
        results = await dan.retrieve(queries=["query"], config=config)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_retrieve_applies_decay(self):
        """retrieve should apply decay to atom weights."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType, RetrievalConfig
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider
        from datetime import timedelta

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed_batch.return_value = [[0.1, 0.2]]

        # Create atom with old timestamp
        old_time = datetime.now() - timedelta(hours=100)
        atom = Atom(
            id="old",
            content="old content",
            atom_type=AtomType.FACT,
            embedding=[0.1, 0.2],
            weight=1.0,
            timestamp=old_time,
        )
        mock_store.vector_search.return_value = [(atom, 0.9)]
        mock_store.get_neighbors.return_value = []

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        config = RetrievalConfig(n_hops=0, top_k=3)
        results = await dan.retrieve(queries=["query"], config=config)

        # Result atom should have decayed weight (less than 1.0)
        assert len(results) == 1
        assert results[0].weight < 1.0


class TestDANMemoryBoost:
    """Tests for DANMemory.boost method."""

    @pytest.mark.asyncio
    async def test_boost_increases_atom_weights(self):
        """boost should increase weights of given atoms."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_store.get_edges_for_atom.return_value = []

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        atoms = [
            Atom(
                id="a1",
                content="test1",
                atom_type=AtomType.FACT,
                embedding=[0.1],
                weight=0.5,
            ),
            Atom(
                id="a2",
                content="test2",
                atom_type=AtomType.CONCEPT,
                embedding=[0.2],
                weight=0.6,
            ),
        ]

        await dan.boost(atoms)

        # Should update atoms in store
        mock_store.batch_update_atoms.assert_called()

    @pytest.mark.asyncio
    async def test_boost_creates_edges_between_atoms(self):
        """boost should create edges between all atom pairs."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType, Edge
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_store.get_edges_for_atom.return_value = []  # No existing edges

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        atoms = [
            Atom(
                id="a1",
                content="test1",
                atom_type=AtomType.FACT,
                embedding=[0.1],
                weight=0.5,
            ),
            Atom(
                id="a2",
                content="test2",
                atom_type=AtomType.CONCEPT,
                embedding=[0.2],
                weight=0.6,
            ),
            Atom(
                id="a3",
                content="test3",
                atom_type=AtomType.EMOTION,
                embedding=[0.3],
                weight=0.7,
            ),
        ]

        await dan.boost(atoms)

        # Should create edges: a1-a2, a1-a3, a2-a3 (3 pairs)
        # Either create_edge or batch operations should be called
        assert mock_store.create_edge.called or mock_store.batch_update_edges.called


class TestDANMemoryRetrieveAndBoost:
    """Tests for retrieval with automatic boost."""

    @pytest.mark.asyncio
    async def test_retrieve_boosts_retrieved_atoms(self):
        """retrieve should boost the retrieved atoms automatically."""
        from memory.dan import DANMemory
        from memory.models import Atom, AtomType, RetrievalConfig
        from memory.store import AtomStore
        from memory.embedding import EmbeddingProvider

        mock_store = AsyncMock(spec=AtomStore)
        mock_embedding = AsyncMock(spec=EmbeddingProvider)
        mock_embedding.embed_batch.return_value = [[0.1, 0.2]]

        atom = Atom(
            id="a1",
            content="test",
            atom_type=AtomType.FACT,
            embedding=[0.1, 0.2],
            weight=0.5,
        )
        mock_store.vector_search.return_value = [(atom, 0.9)]
        mock_store.get_neighbors.return_value = []
        mock_store.get_edges_for_atom.return_value = []

        dan = DANMemory(store=mock_store, embedding_provider=mock_embedding)

        config = RetrievalConfig(n_hops=0, top_k=3)
        await dan.retrieve(queries=["query"], config=config)

        # Should boost the retrieved atoms
        mock_store.batch_update_atoms.assert_called()
