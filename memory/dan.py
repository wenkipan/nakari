"""DAN Memory - Discrete Atom Network main module.

This module provides the main DANMemory class that orchestrates
atom storage, embedding, retrieval, and memory reinforcement.
"""

from datetime import datetime
from itertools import combinations
from typing import List, Optional, Tuple

from pydantic import BaseModel

from memory.decay import boost_atom, boost_edge, decay_atom, decay_edge
from memory.embedding import EmbeddingProvider
from memory.models import (
    Atom,
    AtomType,
    BoostValues,
    Edge,
    RetrievalConfig,
    RetrievalWeights,
)
from memory.store import AtomStore


class RelatedAtom(BaseModel):
    """A related atom for insertion, optionally with edge weight."""

    content: str
    atom_type: AtomType
    weight: float = 1.0
    edge_weight: Optional[float] = None


class InsertRequest(BaseModel):
    """Request to insert a main atom with related atoms."""

    main: RelatedAtom
    related: List[RelatedAtom] = []


class DANMemory:
    """Discrete Atom Network memory system.

    Provides long-term memory storage with:
    - Semantic retrieval via vector search
    - Graph expansion for related memories
    - Ebbinghaus forgetting curve simulation
    - Memory reinforcement through repetition
    """

    def __init__(
        self,
        store: AtomStore,
        embedding_provider: EmbeddingProvider,
    ):
        """Initialize DANMemory.

        Args:
            store: Storage backend for atoms and edges.
            embedding_provider: Provider for text embeddings.
        """
        self.store = store
        self.embedding_provider = embedding_provider

    async def create_atom(
        self,
        content: str,
        atom_type: AtomType,
        weight: float = 1.0,
        extensions: Optional[dict] = None,
    ) -> Atom:
        """Create a new atom with embedding.

        Args:
            content: The semantic content.
            atom_type: Type of atom (Fact, Concept, Emotion).
            weight: Initial weight (default 1.0).
            extensions: Optional extension data.

        Returns:
            The created atom with ID and embedding.
        """
        embedding = await self.embedding_provider.embed(content)

        atom = Atom(
            content=content,
            atom_type=atom_type,
            embedding=embedding,
            weight=weight,
            extensions=extensions,
        )

        return await self.store.create_atom(atom)

    async def insert_data(self, request: InsertRequest) -> Atom:
        """Insert a main atom with related atoms and edges.

        This method:
        1. Creates or retrieves the main atom
        2. Creates or retrieves each related atom
        3. Creates edges between main and related atoms

        Args:
            request: Insert request with main and related atoms.

        Returns:
            The main atom (created or existing).
        """
        # Get or create main atom
        main_atom = await self.store.get_atom_by_content(request.main.content)
        if main_atom is None:
            main_atom = await self.create_atom(
                content=request.main.content,
                atom_type=request.main.atom_type,
                weight=request.main.weight,
            )

        # Process related atoms
        related_atoms: List[Tuple[Atom, float]] = []
        for related in request.related:
            atom = await self.store.get_atom_by_content(related.content)
            if atom is None:
                atom = await self.create_atom(
                    content=related.content,
                    atom_type=related.atom_type,
                    weight=related.weight,
                )
            edge_weight = (
                related.edge_weight if related.edge_weight is not None else 1.0
            )
            related_atoms.append((atom, edge_weight))

        # Create edges between main and related atoms
        for related_atom, edge_weight in related_atoms:
            if main_atom.id and related_atom.id:
                edge = Edge(
                    source_id=main_atom.id,
                    target_id=related_atom.id,
                    weight=edge_weight,
                )
                await self.store.create_edge(edge)

        return main_atom

    async def retrieve(
        self,
        queries: List[str],
        weights: Optional[RetrievalWeights] = None,
        config: Optional[RetrievalConfig] = None,
    ) -> List[Atom]:
        """Retrieve relevant atoms for given queries.

        This method:
        1. Generates embeddings for all queries
        2. Does vector search to find seed atoms
        3. Expands n_hops from seeds to find related atoms
        4. Applies decay to all found atoms
        5. Scores and ranks atoms
        6. Boosts the top-k atoms
        7. Returns top-k atoms

        Args:
            queries: List of query strings.
            weights: Scoring weights (optional, uses defaults).
            config: Retrieval config (optional, uses defaults).

        Returns:
            List of top-k relevant atoms.
        """
        if weights is None:
            weights = RetrievalWeights()
        if config is None:
            config = RetrievalConfig()

        # Generate embeddings for all queries
        query_embeddings = await self.embedding_provider.embed_batch(queries)

        # Collect seed atoms from vector search
        seeds_with_similarity: List[Tuple[Atom, float]] = []
        for embedding in query_embeddings:
            results = await self.store.vector_search(embedding, top_k=config.top_k * 2)
            seeds_with_similarity.extend(results)

        # Build atom map with similarity scores
        atom_map: dict[str, Tuple[Atom, float]] = {}
        for atom, similarity in seeds_with_similarity:
            if atom.id:
                if atom.id not in atom_map or atom_map[atom.id][1] < similarity:
                    atom_map[atom.id] = (atom, similarity)

        # Expand n_hops from seeds
        frontier = set(atom_map.keys())
        for _ in range(config.n_hops):
            next_frontier = set()
            for atom_id in frontier:
                neighbors = await self.store.get_neighbors(atom_id)
                for neighbor in neighbors:
                    if neighbor.id and neighbor.id not in atom_map:
                        atom_map[neighbor.id] = (
                            neighbor,
                            0.0,
                        )  # No similarity for expanded
                        next_frontier.add(neighbor.id)
            frontier = next_frontier

        # Apply decay and compute scores
        now = datetime.now()
        scored_atoms: List[Tuple[Atom, float]] = []

        for atom_id, (atom, similarity) in atom_map.items():
            # Apply lazy decay
            decayed_atom = decay_atom(atom, now)

            # Compute final score
            score = self._compute_score(decayed_atom, similarity, weights)
            scored_atoms.append((decayed_atom, score))

        # Sort by score descending
        scored_atoms.sort(key=lambda x: x[1], reverse=True)

        # Take top-k
        top_atoms = [atom for atom, _ in scored_atoms[: config.top_k]]

        # Boost retrieved atoms
        if top_atoms:
            await self.boost(top_atoms)

        return top_atoms

    def _compute_score(
        self,
        atom: Atom,
        similarity: float,
        weights: RetrievalWeights,
    ) -> float:
        """Compute final score for an atom.

        Formula:
            score = semantic_similarity * similarity +
                    type_weight * weight
        """
        type_weight = {
            AtomType.FACT: weights.fact_weight,
            AtomType.CONCEPT: weights.concept_weight,
            AtomType.EMOTION: weights.emotion_weight,
        }.get(atom.atom_type, 0.0)

        return weights.semantic_similarity * similarity + type_weight * atom.weight

    async def boost(self, atoms: List[Atom]) -> None:
        """Boost a group of atoms and create/strengthen edges between them.

        This simulates memory reinforcement through repetition.

        Args:
            atoms: List of atoms to boost.
        """
        if not atoms:
            return

        # Boost atom weights
        boosted_atoms = [boost_atom(atom) for atom in atoms]
        await self.store.batch_update_atoms(boosted_atoms)

        # Create/boost edges between all pairs
        edges_to_update: List[Edge] = []
        for atom1, atom2 in combinations(atoms, 2):
            if atom1.id and atom2.id:
                # Determine if this is an emotion edge
                is_emotion_edge = (
                    atom1.atom_type == AtomType.EMOTION
                    or atom2.atom_type == AtomType.EMOTION
                )

                # Check for existing edge
                existing_edges = await self.store.get_edges_for_atom(atom1.id)
                existing_edge = None
                for edge in existing_edges:
                    if edge.target_id == atom2.id or edge.source_id == atom2.id:
                        existing_edge = edge
                        break

                if existing_edge:
                    # Boost existing edge
                    boosted_edge = boost_edge(existing_edge, is_emotion_edge)
                    edges_to_update.append(boosted_edge)
                else:
                    # Create new edge with boost value
                    boost_value = (
                        BoostValues.EMOTION_EDGE
                        if is_emotion_edge
                        else BoostValues.NORMAL_EDGE
                    )
                    new_edge = Edge(
                        source_id=atom1.id,
                        target_id=atom2.id,
                        weight=boost_value,
                    )
                    await self.store.create_edge(new_edge)

        # Update existing edges
        if edges_to_update:
            await self.store.batch_update_edges(edges_to_update)
