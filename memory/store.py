"""DAN Memory Store - Neo4j storage layer for atoms and edges.

This module provides the storage abstraction and Neo4j implementation
for persisting and retrieving atoms and edges in the DAN memory system.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import neo4j
from neo4j import AsyncGraphDatabase

from memory.models import Atom, AtomType, Edge


class AtomStore(abc.ABC):
    """Abstract base class for atom storage.

    Defines the interface for storing and retrieving atoms and edges.
    """

    @abc.abstractmethod
    async def create_atom(self, atom: Atom) -> Atom:
        """Create a new atom in the store.

        Args:
            atom: The atom to create.

        Returns:
            The created atom with database ID.
        """
        pass

    @abc.abstractmethod
    async def get_atom_by_id(self, atom_id: str) -> Optional[Atom]:
        """Get an atom by its ID.

        Args:
            atom_id: The database ID of the atom.

        Returns:
            The atom if found, None otherwise.
        """
        pass

    @abc.abstractmethod
    async def get_atom_by_content(self, content: str) -> Optional[Atom]:
        """Get an atom by its content (exact match).

        Args:
            content: The content to search for.

        Returns:
            The atom if found, None otherwise.
        """
        pass

    @abc.abstractmethod
    async def update_atom(self, atom: Atom) -> None:
        """Update an existing atom.

        Args:
            atom: The atom with updated values.
        """
        pass

    @abc.abstractmethod
    async def create_edge(self, edge: Edge) -> None:
        """Create a new edge between two atoms.

        Args:
            edge: The edge to create.
        """
        pass

    @abc.abstractmethod
    async def get_edges_for_atom(self, atom_id: str) -> List[Edge]:
        """Get all edges connected to an atom.

        Args:
            atom_id: The ID of the atom.

        Returns:
            List of edges connected to this atom.
        """
        pass

    @abc.abstractmethod
    async def vector_search(
        self, embedding: List[float], top_k: int = 10
    ) -> List[Tuple[Atom, float]]:
        """Search for atoms by vector similarity.

        Args:
            embedding: The query embedding vector.
            top_k: Maximum number of results to return.

        Returns:
            List of (Atom, similarity_score) tuples.
        """
        pass

    @abc.abstractmethod
    async def get_neighbors(self, atom_id: str) -> List[Atom]:
        """Get all atoms connected to the given atom by edges.

        Args:
            atom_id: The ID of the center atom.

        Returns:
            List of connected atoms.
        """
        pass

    @abc.abstractmethod
    async def update_edge(self, edge: Edge) -> None:
        """Update an existing edge.

        Args:
            edge: The edge with updated values.
        """
        pass

    @abc.abstractmethod
    async def batch_update_atoms(self, atoms: List[Atom]) -> None:
        """Update multiple atoms in a batch.

        Args:
            atoms: List of atoms to update.
        """
        pass

    @abc.abstractmethod
    async def batch_update_edges(self, edges: List[Edge]) -> None:
        """Update multiple edges in a batch.

        Args:
            edges: List of edges to update.
        """
        pass


def _atom_type_to_label(atom_type: AtomType) -> str:
    """Convert AtomType enum to Neo4j label string."""
    return atom_type.value.capitalize()


def _label_to_atom_type(label: str) -> AtomType:
    """Convert Neo4j label string to AtomType enum."""
    label_lower = label.lower()
    for atom_type in AtomType:
        if atom_type.value == label_lower:
            return atom_type
    raise ValueError(f"Unknown label: {label}")


def _record_to_atom(record: Dict[str, Any]) -> Atom:
    """Convert a Neo4j record to an Atom object."""
    labels = record.get("labels", [])
    # Find the atom type label (Fact, Concept, or Emotion)
    atom_type = None
    for label in labels:
        try:
            atom_type = _label_to_atom_type(label)
            break
        except ValueError:
            continue

    if atom_type is None:
        # Default to Fact if no valid label found
        atom_type = AtomType.FACT

    timestamp = record.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    elif timestamp is None:
        timestamp = datetime.now()

    return Atom(
        id=str(record.get("id", "")),
        content=record.get("content", ""),
        atom_type=atom_type,
        embedding=record.get("embedding"),
        weight=record.get("weight", 1.0),
        timestamp=timestamp,
        extensions=record.get("extensions"),
    )


class Neo4jAtomStore(AtomStore):
    """Neo4j implementation of atom storage.

    Uses Neo4j graph database for storing atoms and edges,
    with vector index support for similarity search.
    """

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687).
            username: Neo4j username.
            password: Neo4j password.
            database: Database name (default: neo4j).
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver = AsyncGraphDatabase.driver(uri, auth=(username, password))

    async def close(self) -> None:
        """Close the database connection."""
        await self._driver.close()

    async def create_atom(self, atom: Atom) -> Atom:
        """Create a new atom in Neo4j."""
        label = _atom_type_to_label(atom.atom_type)

        query = f"""
        CREATE (n:{label} {{
            content: $content,
            weight: $weight,
            timestamp: $timestamp,
            embedding: $embedding,
            extensions: $extensions
        }})
        RETURN elementId(n) as id
        """

        async with self._driver.session(database=self.database) as session:
            result = await session.run(
                query,
                content=atom.content,
                weight=atom.weight,
                timestamp=atom.timestamp.isoformat(),
                embedding=atom.embedding,
                extensions=atom.extensions,
            )
            record = await result.single()
            if record is None:
                raise ValueError("Failed to create atom")
            atom_id = record["id"]

        return Atom(
            id=atom_id,
            content=atom.content,
            atom_type=atom.atom_type,
            embedding=atom.embedding,
            weight=atom.weight,
            timestamp=atom.timestamp,
            extensions=atom.extensions,
        )

    async def get_atom_by_id(self, atom_id: str) -> Optional[Atom]:
        """Get an atom by its ID."""
        query = """
        MATCH (n)
        WHERE elementId(n) = $id
        RETURN elementId(n) as id, n.content as content, n.weight as weight,
               n.timestamp as timestamp, n.embedding as embedding,
               n.extensions as extensions, labels(n) as labels
        """

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, id=atom_id)
            record = await result.single()

            if record is None:
                return None

            return _record_to_atom(dict(record))

    async def get_atom_by_content(self, content: str) -> Optional[Atom]:
        """Get an atom by its content (exact match)."""
        query = """
        MATCH (n)
        WHERE n.content = $content
        RETURN elementId(n) as id, n.content as content, n.weight as weight,
               n.timestamp as timestamp, n.embedding as embedding,
               n.extensions as extensions, labels(n) as labels
        LIMIT 1
        """

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, content=content)
            record = await result.single()

            if record is None:
                return None

            return _record_to_atom(dict(record))

    async def update_atom(self, atom: Atom) -> None:
        """Update an existing atom."""
        query = """
        MATCH (n)
        WHERE elementId(n) = $id
        SET n.weight = $weight, n.timestamp = $timestamp
        """

        async with self._driver.session(database=self.database) as session:
            await session.run(
                query,
                id=atom.id,
                weight=atom.weight,
                timestamp=atom.timestamp.isoformat(),
            )

    async def create_edge(self, edge: Edge) -> None:
        """Create a new edge between two atoms."""
        query = """
        MATCH (a), (b)
        WHERE elementId(a) = $source_id AND elementId(b) = $target_id
        MERGE (a)-[r:CONNECTED]-(b)
        SET r.weight = $weight, r.timestamp = $timestamp
        """

        async with self._driver.session(database=self.database) as session:
            await session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                weight=edge.weight,
                timestamp=edge.timestamp.isoformat(),
            )

    async def get_edges_for_atom(self, atom_id: str) -> List[Edge]:
        """Get all edges connected to an atom."""
        query = """
        MATCH (a)-[r:CONNECTED]-(b)
        WHERE elementId(a) = $atom_id
        RETURN elementId(a) as source_id, elementId(b) as target_id,
               r.weight as weight, r.timestamp as timestamp
        """

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, atom_id=atom_id)
            edges = []
            async for record in result:
                timestamp = record["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                elif timestamp is None:
                    timestamp = datetime.now()

                edges.append(
                    Edge(
                        source_id=record["source_id"],
                        target_id=record["target_id"],
                        weight=record["weight"] or 1.0,
                        timestamp=timestamp,
                    )
                )
            return edges

    async def vector_search(
        self, embedding: List[float], top_k: int = 10
    ) -> List[Tuple[Atom, float]]:
        """Search for atoms by vector similarity using Neo4j vector index.

        Searches across all node types (Fact, Concept, Emotion) by querying
        their respective vector indexes and merging results.
        """
        # Query multiple indexes and combine results
        indexes = [
            ("atom_embeddings", "Fact"),
            ("concept_embeddings", "Concept"),
            ("emotion_embeddings", "Emotion"),
        ]

        # Use dict for deduplication, keeping highest similarity score
        seen_atoms: Dict[str, Tuple[Atom, float]] = {}

        async with self._driver.session(database=self.database) as session:
            for index_name, label in indexes:
                query = f"""
                CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
                YIELD node, score
                RETURN elementId(node) as id, node.content as content,
                       node.weight as weight, node.timestamp as timestamp,
                       node.embedding as embedding, node.extensions as extensions,
                       labels(node) as labels, score as similarity
                """

                try:
                    result = await session.run(
                        query,
                        embedding=embedding,
                        top_k=top_k,
                    )

                    async for record in result:
                        atom = _record_to_atom(dict(record))
                        similarity = record["similarity"]
                        atom_id = atom.id

                        # Keep the result with highest similarity
                        if atom_id not in seen_atoms:
                            seen_atoms[atom_id] = (atom, similarity)
                        elif similarity > seen_atoms[atom_id][1]:
                            seen_atoms[atom_id] = (atom, similarity)
                except Exception:
                    # Index might not exist, skip
                    pass

        # Sort by similarity and return top_k
        all_results = list(seen_atoms.values())
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]

    async def get_neighbors(self, atom_id: str) -> List[Atom]:
        """Get all atoms connected to the given atom by edges."""
        query = """
        MATCH (a)-[r:CONNECTED]-(b)
        WHERE elementId(a) = $atom_id
        RETURN elementId(b) as id, b.content as content, b.weight as weight,
               b.timestamp as timestamp, b.embedding as embedding,
               b.extensions as extensions, labels(b) as labels
        """

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, atom_id=atom_id)

            atoms = []
            async for record in result:
                atoms.append(_record_to_atom(dict(record)))

            return atoms

    async def update_edge(self, edge: Edge) -> None:
        """Update an existing edge."""
        query = """
        MATCH (a)-[r:CONNECTED]-(b)
        WHERE elementId(a) = $source_id AND elementId(b) = $target_id
        SET r.weight = $weight, r.timestamp = $timestamp
        """

        async with self._driver.session(database=self.database) as session:
            await session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                weight=edge.weight,
                timestamp=edge.timestamp.isoformat(),
            )

    async def batch_update_atoms(self, atoms: List[Atom]) -> None:
        """Update multiple atoms in a batch."""
        query = """
        UNWIND $atoms as atom
        MATCH (n)
        WHERE elementId(n) = atom.id
        SET n.weight = atom.weight, n.timestamp = atom.timestamp
        """

        atoms_data = [
            {
                "id": atom.id,
                "weight": atom.weight,
                "timestamp": atom.timestamp.isoformat(),
            }
            for atom in atoms
        ]

        async with self._driver.session(database=self.database) as session:
            await session.run(query, atoms=atoms_data)

    async def batch_update_edges(self, edges: List[Edge]) -> None:
        """Update multiple edges in a batch."""
        query = """
        UNWIND $edges as edge
        MATCH (a)-[r:CONNECTED]-(b)
        WHERE elementId(a) = edge.source_id AND elementId(b) = edge.target_id
        SET r.weight = edge.weight, r.timestamp = edge.timestamp
        """

        edges_data = [
            {
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "weight": edge.weight,
                "timestamp": edge.timestamp.isoformat(),
            }
            for edge in edges
        ]

        async with self._driver.session(database=self.database) as session:
            await session.run(query, edges=edges_data)
