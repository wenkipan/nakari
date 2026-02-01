import math
from datetime import datetime
from typing import Tuple


def on_access_value(
    *,
    current_value: float,
    last_ts: datetime,
    now_ts: datetime,
    decay_rate: float,
    boost: float,
) -> Tuple[float, datetime]:
    """Apply exponential decay since last_ts, then add boost and clamp to [0, 1]."""

    hours = (now_ts - last_ts).total_seconds() / 3600.0
    decayed = current_value * math.exp(-decay_rate * hours)
    new_value = min(1.0, max(0.0, decayed + boost))
    return new_value, now_ts
