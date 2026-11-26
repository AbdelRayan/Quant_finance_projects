"""Project 2 trading rule: the calendar month as the theta cycle.

Hold equities only in the turn-of-the-month window, cash otherwise. The
trading calendar is known in advance, so deciding today whether tomorrow is
in the window uses no future prices.
"""

from __future__ import annotations

import pandas as pd


def month_position(index: pd.DatetimeIndex) -> pd.DataFrame:
    """For each trading day: position from the start (0 = first) and from the end (0 = last)."""
    s = index.to_series()
    month = index.to_period("M")
    from_start = s.groupby(month).cumcount()
    from_end = s.groupby(month).cumcount(ascending=False)
    return pd.DataFrame({"from_start": from_start, "from_end": from_end}, index=index)


def turn_of_month(prices: pd.DataFrame, n_last: int = 5, n_first: int = 1) -> pd.DataFrame:
    """Equal weights on every asset for the last ``n_last`` and first ``n_first`` trading days of each month.

    The backtester applies weights from date t to the return of t+1, so the
    weight on date t is set by whether the *next* trading day is in the window.
    """
    pos = month_position(prices.index)
    in_window = (pos["from_end"] < n_last) | (pos["from_start"] < n_first)
    hold_tomorrow = in_window.shift(-1, fill_value=False)  # calendar, not prices: known in advance
    weights = pd.DataFrame(1.0 / prices.shape[1], index=prices.index, columns=prices.columns)
    return weights.mul(hold_tomorrow.astype(float), axis=0)
