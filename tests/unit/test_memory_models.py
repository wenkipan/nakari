from __future__ import annotations

from datetime import datetime, timezone


def test_atom_model_roundtrip() -> None:
    from memory.models import Atom

    a = Atom(
        content="Wenki is staying up late",
        type="fact",
        timestamp=datetime(2026, 2, 1, 12, 34, 56, tzinfo=timezone.utc),
    )

    dumped = a.model_dump()
    assert dumped["content"] == "Wenki is staying up late"
    assert dumped["type"] == "fact"


def test_link_model_roundtrip() -> None:
    from memory.models import Link

    l = Link(
        source="A",
        target="B",
        weight=0.25,
        timestamp=datetime(2026, 2, 1, 12, 34, 56, tzinfo=timezone.utc),
    )

    assert l.weight == 0.25
