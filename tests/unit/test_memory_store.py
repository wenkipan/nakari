"""TDD tests for DAN memory store - Neo4j storage layer."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from typing import List


class TestAtomStoreInterface:
    """Tests for abstract AtomStore interface."""

    def test_atom_store_is_abstract(self):
        """AtomStore should be an abstract base class."""
        from memory.store import AtomStore
        import abc

        assert issubclass(AtomStore, abc.ABC)

    def test_atom_store_has_create_atom_method(self):
        """AtomStore should have abstract create_atom method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "create_atom")
        assert getattr(AtomStore.create_atom, "__isabstractmethod__", False)

    def test_atom_store_has_get_atom_by_id_method(self):
        """AtomStore should have abstract get_atom_by_id method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "get_atom_by_id")
        assert getattr(AtomStore.get_atom_by_id, "__isabstractmethod__", False)

    def test_atom_store_has_get_atom_by_content_method(self):
        """AtomStore should have abstract get_atom_by_content method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "get_atom_by_content")
        assert getattr(AtomStore.get_atom_by_content, "__isabstractmethod__", False)

    def test_atom_store_has_update_atom_method(self):
        """AtomStore should have abstract update_atom method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "update_atom")
        assert getattr(AtomStore.update_atom, "__isabstractmethod__", False)

    def test_atom_store_has_create_edge_method(self):
        """AtomStore should have abstract create_edge method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "create_edge")
        assert getattr(AtomStore.create_edge, "__isabstractmethod__", False)

    def test_atom_store_has_get_edges_for_atom_method(self):
        """AtomStore should have abstract get_edges_for_atom method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "get_edges_for_atom")
        assert getattr(AtomStore.get_edges_for_atom, "__isabstractmethod__", False)

    def test_atom_store_has_vector_search_method(self):
        """AtomStore should have abstract vector_search method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "vector_search")
        assert getattr(AtomStore.vector_search, "__isabstractmethod__", False)

    def test_atom_store_has_get_neighbors_method(self):
        """AtomStore should have abstract get_neighbors method."""
        from memory.store import AtomStore

        assert hasattr(AtomStore, "get_neighbors")
        assert getattr(AtomStore.get_neighbors, "__isabstractmethod__", False)


class TestNeo4jAtomStoreInit:
    """Tests for Neo4jAtomStore initialization."""

    def test_neo4j_store_is_atom_store(self):
        """Neo4jAtomStore should inherit from AtomStore."""
        from memory.store import AtomStore, Neo4jAtomStore

        assert issubclass(Neo4jAtomStore, AtomStore)

    def test_neo4j_store_requires_uri(self):
        """Neo4jAtomStore should require URI."""
        from memory.store import Neo4jAtomStore

        with patch("memory.store.AsyncGraphDatabase") as mock_db:
            store = Neo4jAtomStore(
                uri="bolt://localhost:7687", username="neo4j", password="password"
            )
            assert store.uri == "bolt://localhost:7687"

    def test_neo4j_store_requires_auth(self):
        """Neo4jAtomStore should require username and password."""
        from memory.store import Neo4jAtomStore

        with patch("memory.store.AsyncGraphDatabase") as mock_db:
            store = Neo4jAtomStore(
                uri="bolt://localhost:7687", username="neo4j", password="test_password"
            )
            assert store.username == "neo4j"
            assert store.password == "test_password"


@pytest.fixture
def mock_neo4j_store():
    """Create Neo4jAtomStore with fully mocked Neo4j driver."""
    from memory.store import Neo4jAtomStore

    with patch("memory.store.AsyncGraphDatabase") as mock_db:
        mock_driver = MagicMock()
        mock_db.driver.return_value = mock_driver

        # Create the session mock that supports async context manager
        mock_session = AsyncMock()

        # Make session() return an async context manager
        async def async_session_cm():
            return mock_session

        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, *args):
                pass

        mock_driver.session.return_value = MockAsyncContextManager()

        store = Neo4jAtomStore(
            uri="bolt://localhost:7687", username="neo4j", password="password"
        )

        yield store, mock_session


class TestNeo4jAtomStoreCreateAtom:
    """Tests for Neo4jAtomStore.create_atom method."""

    @pytest.mark.asyncio
    async def test_create_atom_returns_atom_with_id(self, mock_neo4j_store):
        """create_atom should return atom with database ID."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        # Mock the run result
        mock_result = AsyncMock()
        mock_record = {"id": "atom_123"}
        mock_result.single = AsyncMock(return_value=mock_record)
        mock_session.run.return_value = mock_result

        atom = Atom(
            content="Wenki在熬夜",
            atom_type=AtomType.FACT,
            embedding=[0.1, 0.2, 0.3],
        )

        result = await store.create_atom(atom)

        assert result.id == "atom_123"
        assert result.content == "Wenki在熬夜"

    @pytest.mark.asyncio
    async def test_create_atom_uses_correct_label(self, mock_neo4j_store):
        """create_atom should use AtomType as Neo4j label."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_record = {"id": "atom_123"}
        mock_result.single = AsyncMock(return_value=mock_record)
        mock_session.run.return_value = mock_result

        atom = Atom(content="Wenki", atom_type=AtomType.CONCEPT, embedding=[0.1, 0.2])

        await store.create_atom(atom)

        # Verify the Cypher query contains the correct label
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "Concept" in query or ":Concept" in query.replace(" ", "")


class TestNeo4jAtomStoreGetAtom:
    """Tests for Neo4jAtomStore get methods."""

    @pytest.mark.asyncio
    async def test_get_atom_by_id_returns_atom(self, mock_neo4j_store):
        """get_atom_by_id should return atom if found."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        # Mock the result
        mock_result = AsyncMock()
        mock_record = {
            "id": "atom_123",
            "content": "test content",
            "weight": 0.8,
            "timestamp": datetime.now().isoformat(),
            "embedding": [0.1, 0.2],
            "extensions": None,
            "labels": ["Fact"],
        }
        mock_result.single = AsyncMock(return_value=mock_record)
        mock_session.run.return_value = mock_result

        result = await store.get_atom_by_id("atom_123")

        assert result is not None
        assert result.id == "atom_123"
        assert result.content == "test content"

    @pytest.mark.asyncio
    async def test_get_atom_by_id_returns_none_if_not_found(self, mock_neo4j_store):
        """get_atom_by_id should return None if atom not found."""
        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value=None)
        mock_session.run.return_value = mock_result

        result = await store.get_atom_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_atom_by_content_returns_atom(self, mock_neo4j_store):
        """get_atom_by_content should return atom if found."""
        from memory.models import AtomType

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_record = {
            "id": "atom_456",
            "content": "Wenki",
            "weight": 0.8,
            "timestamp": datetime.now().isoformat(),
            "embedding": [0.1, 0.2],
            "extensions": None,
            "labels": ["Concept"],
        }
        mock_result.single = AsyncMock(return_value=mock_record)
        mock_session.run.return_value = mock_result

        result = await store.get_atom_by_content("Wenki")

        assert result is not None
        assert result.content == "Wenki"


class TestNeo4jAtomStoreEdges:
    """Tests for Neo4jAtomStore edge operations."""

    @pytest.mark.asyncio
    async def test_create_edge_creates_relationship(self, mock_neo4j_store):
        """create_edge should create relationship in Neo4j."""
        from memory.models import Edge

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_session.run.return_value = mock_result

        edge = Edge(source_id="atom_1", target_id="atom_2", weight=0.8)

        await store.create_edge(edge)

        # Verify run was called with MERGE or CREATE for relationship
        assert mock_session.run.called

    @pytest.mark.asyncio
    async def test_get_edges_for_atom_returns_edges(self, mock_neo4j_store):
        """get_edges_for_atom should return all edges connected to atom."""
        from memory.models import Edge

        store, mock_session = mock_neo4j_store

        # Mock multiple edge results using async iterator
        mock_records = [
            {
                "source_id": "atom_1",
                "target_id": "atom_2",
                "weight": 0.8,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "source_id": "atom_1",
                "target_id": "atom_3",
                "weight": 0.6,
                "timestamp": datetime.now().isoformat(),
            },
        ]

        async def mock_aiter():
            for record in mock_records:
                yield record

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: mock_aiter()
        mock_session.run.return_value = mock_result

        results = await store.get_edges_for_atom("atom_1")

        assert len(results) == 2


class TestNeo4jAtomStoreVectorSearch:
    """Tests for Neo4jAtomStore vector search."""

    @pytest.mark.asyncio
    async def test_vector_search_returns_atoms_with_similarity(self, mock_neo4j_store):
        """vector_search should return atoms ranked by similarity."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        # Mock search results using async iterator
        mock_records = [
            {
                "id": "atom_1",
                "content": "Wenki在熬夜",
                "weight": 0.8,
                "timestamp": datetime.now().isoformat(),
                "embedding": [0.1, 0.2],
                "extensions": None,
                "labels": ["Fact"],
                "similarity": 0.95,
            },
            {
                "id": "atom_2",
                "content": "熬夜",
                "weight": 0.9,
                "timestamp": datetime.now().isoformat(),
                "embedding": [0.1, 0.3],
                "extensions": None,
                "labels": ["Concept"],
                "similarity": 0.85,
            },
        ]

        async def mock_aiter():
            for record in mock_records:
                yield record

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: mock_aiter()
        mock_session.run.return_value = mock_result

        results = await store.vector_search(embedding=[0.1, 0.2], top_k=5)

        assert len(results) == 2
        # Results should be tuples of (Atom, similarity)
        assert results[0][1] == 0.95
        assert results[1][1] == 0.85


class TestNeo4jAtomStoreGetNeighbors:
    """Tests for Neo4jAtomStore.get_neighbors method."""

    @pytest.mark.asyncio
    async def test_get_neighbors_returns_connected_atoms(self, mock_neo4j_store):
        """get_neighbors should return atoms connected by edges."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        mock_records = [
            {
                "id": "atom_2",
                "content": "Wenki",
                "weight": 0.9,
                "timestamp": datetime.now().isoformat(),
                "embedding": [0.2, 0.3],
                "extensions": None,
                "labels": ["Concept"],
            },
            {
                "id": "atom_3",
                "content": "熬夜",
                "weight": 0.8,
                "timestamp": datetime.now().isoformat(),
                "embedding": [0.3, 0.4],
                "extensions": None,
                "labels": ["Concept"],
            },
        ]

        async def mock_aiter():
            for record in mock_records:
                yield record

        mock_result = MagicMock()
        mock_result.__aiter__ = lambda self: mock_aiter()
        mock_session.run.return_value = mock_result

        results = await store.get_neighbors("atom_1")

        assert len(results) == 2


class TestNeo4jAtomStoreUpdateAtom:
    """Tests for Neo4jAtomStore.update_atom method."""

    @pytest.mark.asyncio
    async def test_update_atom_updates_weight_and_timestamp(self, mock_neo4j_store):
        """update_atom should update atom weight and timestamp."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_session.run.return_value = mock_result

        atom = Atom(id="atom_123", content="test", atom_type=AtomType.FACT, weight=0.5)

        await store.update_atom(atom)

        # Verify run was called with SET for weight/timestamp
        assert mock_session.run.called
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "SET" in query


class TestNeo4jAtomStoreUpdateEdge:
    """Tests for Neo4jAtomStore.update_edge method."""

    @pytest.mark.asyncio
    async def test_update_edge_updates_weight_and_timestamp(self, mock_neo4j_store):
        """update_edge should update edge weight and timestamp."""
        from memory.models import Edge

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_session.run.return_value = mock_result

        edge = Edge(source_id="atom_1", target_id="atom_2", weight=0.7)

        await store.update_edge(edge)

        assert mock_session.run.called


class TestNeo4jAtomStoreBatchOperations:
    """Tests for batch update operations."""

    @pytest.mark.asyncio
    async def test_batch_update_atoms(self, mock_neo4j_store):
        """batch_update_atoms should update multiple atoms efficiently."""
        from memory.models import Atom, AtomType

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_session.run.return_value = mock_result

        atoms = [
            Atom(id="atom_1", content="test1", atom_type=AtomType.FACT, weight=0.5),
            Atom(id="atom_2", content="test2", atom_type=AtomType.CONCEPT, weight=0.6),
        ]

        await store.batch_update_atoms(atoms)

        assert mock_session.run.called

    @pytest.mark.asyncio
    async def test_batch_update_edges(self, mock_neo4j_store):
        """batch_update_edges should update multiple edges efficiently."""
        from memory.models import Edge

        store, mock_session = mock_neo4j_store

        mock_result = AsyncMock()
        mock_session.run.return_value = mock_result

        edges = [
            Edge(source_id="atom_1", target_id="atom_2", weight=0.5),
            Edge(source_id="atom_2", target_id="atom_3", weight=0.6),
        ]

        await store.batch_update_edges(edges)

        assert mock_session.run.called
