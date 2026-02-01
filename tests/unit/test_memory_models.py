from __future__ import annotations

from datetime import datetime, timezone


def test_atom_roundtrip_via_json() -> None:
    from memory.models import Atom

    atom = Atom(
        content="Wenki is staying up late",
        embedding=[0.1, 0.2, 0.3],
        type="fact",
        strength=0.75,
        timestamp=datetime(2026, 2, 1, 12, 34, 56, tzinfo=timezone.utc),
        extensions={"source": "chat", "lang": "en"},
    )

    payload = atom.model_dump_json()
    parsed = Atom.model_validate_json(payload)
    assert parsed == atom


def test_link_roundtrip_via_json() -> None:
    from memory.models import Link

    link = Link(
        weight=0.42,
        timestamp=datetime(2026, 2, 1, 12, 34, 56, tzinfo=timezone.utc),
    )

    payload = link.model_dump_json()
    parsed = Link.model_validate_json(payload)
    assert parsed == link
