from datetime import datetime, timedelta, timezone


def test_on_access_boosts_and_updates_timestamp():
    from memory.decay import on_access_value

    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    past = now - timedelta(hours=10)

    new_value, new_ts = on_access_value(
        current_value=0.5,
        last_ts=past,
        now_ts=now,
        decay_rate=0.01,
        boost=0.05,
    )

    assert new_ts == now
    assert 0.5 < new_value <= 1.0
