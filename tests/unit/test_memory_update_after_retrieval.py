from datetime import datetime, timezone


def test_should_link_only_concepts() -> None:
    from memory.models import Atom
    from memory.update_after_retrieval import concept_pairs_to_link

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    atoms = [
        Atom(content="A", embedding=[], type="concept", strength=0.1, timestamp=now),
        Atom(content="B", embedding=[], type="concept", strength=0.1, timestamp=now),
        Atom(content="C", embedding=[], type="fact", strength=0.1, timestamp=now),
    ]

    pairs = concept_pairs_to_link(atoms)
    assert pairs == {("A", "B")}
