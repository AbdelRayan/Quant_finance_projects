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


def momentum_12_1(
    prices: pd.DataFrame,
    top_n: int = 3,
    lookback: int = 252,
    skip: int = 21,
) -> pd.DataFrame:
    """12-1 cross-sectional momentum, rebalanced on the last trading day of each month.

    - Score: return from ``lookback`` days ago to ``skip`` days ago. Skipping
      the most recent month avoids short-term reversal (last month's winners
      tend to give some of it back).
    - On each month's last trading day, hold the ``top_n`` highest scores at
      ``1 / top_n`` weight each; keep those weights until the next month end.
    - Before a full lookback exists, hold nothing.

    Weights at date t use prices up to t only; the backtester trades them at t+1.
    """
    score = prices.shift(skip) / prices.shift(lookback) - 1

    # Last actual trading day of each month (calendar month ends can fall on weekends).
    dates = prices.index.to_series()
    rebalance_dates = dates.groupby(prices.index.to_period("M")).max()

    monthly_score = score.loc[rebalance_dates]
    rank = monthly_score.rank(axis=1, ascending=False, method="first")
    chosen = (rank <= top_n) & monthly_score.notna()
    monthly_weights = chosen.astype(float) / top_n

    return monthly_weights.reindex(prices.index).ffill().fillna(0.0)
