from itertools import combinations
from typing import Iterable, Set, Tuple

from memory.models import Atom


def concept_pairs_to_link(atoms: Iterable[Atom]) -> Set[Tuple[str, str]]:
    concepts = [a for a in atoms if a.type == "concept"]
    pairs: Set[Tuple[str, str]] = set()
    for a, b in combinations(concepts, 2):
        x, y = sorted([a.content, b.content])
        pairs.add((x, y))
    return pairs
