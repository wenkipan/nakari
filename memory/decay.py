from __future__ import annotations

import math
from datetime import datetime
from typing import Tuple


def on_access_value(
    current_value: float,
    last_ts: datetime,
    now_ts: datetime,
    decay_rate: float,
    boost: float,
) -> Tuple[float, datetime]:
    """Apply exponential decay since last_ts, then add boost.

    Args:
        current_value: Current scalar value in [0, 1].
        last_ts: Timestamp when value was last updated.
        now_ts: Current timestamp; returned as the updated timestamp.
        decay_rate: Exponential decay rate per hour.
        boost: Additive boost applied after decay.

    Returns:
        Tuple of (new_value, now_ts) where new_value is clamped to [0, 1].
    """

    hours = (now_ts - last_ts).total_seconds() / 3600.0
    if hours < 0:
        hours = 0.0

    decayed = current_value * math.exp(-decay_rate * hours)
    new_value = decayed + boost

    if new_value < 0.0:
        new_value = 0.0
    elif new_value > 1.0:
        new_value = 1.0

    return new_value, now_ts
