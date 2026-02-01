from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module

import pytest


def test_on_access_value_updates_ts_and_boosts_value() -> None:
    try:
        decay = import_module("memory.decay")
    except ModuleNotFoundError:
        pytest.fail("memory.decay module missing")

    try:
        on_access_value = getattr(decay, "on_access_value")
    except AttributeError:
        pytest.fail("on_access_value missing")

    last_ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    now_ts = last_ts + timedelta(hours=1)

    new_value, new_ts = on_access_value(
        current_value=0.5,
        last_ts=last_ts,
        now_ts=now_ts,
        decay_rate=0.0,
        boost=0.1,
    )

    assert new_ts == now_ts
    assert new_value == pytest.approx(0.6)
