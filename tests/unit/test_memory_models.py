from datetime import datetime, timezone


def test_atom_model_roundtrip():
    from memory.models import Atom

    a = Atom(
        content="Wenki stayed up late",
        embedding=[0.0, 1.0, 0.0],
        type="fact",
        strength=0.5,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        extensions={"source": "test"},
    )

    dumped = a.model_dump()
    assert dumped["content"] == "Wenki stayed up late"
    assert dumped["type"] == "fact"


def test_link_model_roundtrip():
    from memory.models import Link

    l = Link(
        source="A",
        target="B",
        weight=0.25,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert l.weight == 0.25
