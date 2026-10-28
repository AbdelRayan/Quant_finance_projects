"""Project 1 signals: turn a momentum idea into target weights.

Every function here returns weights for date t using only prices up to and
including date t. The backtester applies the one-day delay.
"""

from __future__ import annotations

import pandas as pd


def ma_crossover(prices: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.DataFrame:
    """Reference example: long an asset when its fast MA is above its slow MA.

    Capital is split equally across the assets that are "on"; assets that are
    "off" are held in cash. Days before the slow MA has a full window get no
    position, so nothing is computed from an incomplete history.
    """
    fast_ma = prices.rolling(fast, min_periods=fast).mean()
    slow_ma = prices.rolling(slow, min_periods=slow).mean()
    on = (fast_ma > slow_ma).astype(float)
    n_assets = prices.shape[1]
    return on / n_assets


def momentum_12_1(prices: pd.DataFrame, top_n: int = 3, rebalance: str = "ME") -> pd.DataFrame:
    """Your turn: 12-1 cross-sectional momentum.

    Spec (see README, step 4):
    - Score each asset by its return from 252 trading days ago to 21 days ago
      (skip the most recent month).
    - On each rebalance date (month end), hold the ``top_n`` assets with equal
      weight; hold the weights constant until the next rebalance.
    - Use only prices up to the rebalance date.

    Hints: ``prices.shift(21) / prices.shift(252) - 1``, ``.rank(axis=1)``,
    ``.resample(rebalance).last()``, then ``.reindex(prices.index).ffill()``.
    Add tests in ``tests/test_strategy.py`` once it works, including the
    look-ahead check used for ``ma_crossover``.
    """
    raise NotImplementedError("Implement 12-1 momentum (Project 1, step 4)")
