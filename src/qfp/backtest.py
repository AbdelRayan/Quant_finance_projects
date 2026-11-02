"""A small vectorised backtester that cannot look ahead.

Convention: ``signal`` at date t may use data up to and including the close of
day t. The backtester holds that position from t+1 onward, so the return
earned on day t+1 is ``position[t] * return[t+1]``.

The delay only protects against trading on the same close you computed the
signal from. A signal that itself uses future data (e.g. ``shift(-1)``) will
still cheat, which is why every strategy also gets a look-ahead test.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestResult:
    returns: pd.Series        # daily strategy returns, net of costs
    gross_returns: pd.Series  # daily strategy returns before costs
    positions: pd.DataFrame   # weights actually held each day
    turnover: pd.Series       # sum of absolute weight changes each day
    equity: pd.Series         # growth of $1


def run_backtest(
    prices: pd.DataFrame,
    signal: pd.DataFrame,
    cost_bps: float = 5.0,
) -> BacktestResult:
    """Backtest target weights ``signal`` (same shape as ``prices``).

    ``cost_bps`` is charged on every unit of weight traded (one-way), which
    covers commissions and slippage in a simple way. Weights are reset to
    target every day, and the small trades needed to undo price drift are not
    charged, so costs are slightly understated for constant-weight portfolios.
    """
    signal = signal.reindex_like(prices).fillna(0.0)
    asset_returns = prices.pct_change().fillna(0.0)

    # The one-bar shift is what prevents look-ahead bias.
    positions = signal.shift(1).fillna(0.0)

    gross = (positions * asset_returns).sum(axis=1)
    turnover = positions.diff().abs().sum(axis=1)
    turnover.iloc[0] = positions.iloc[0].abs().sum()
    net = gross - turnover * cost_bps / 10_000

    return BacktestResult(
        returns=net,
        gross_returns=gross,
        positions=positions,
        turnover=turnover,
        equity=(1 + net).cumprod(),
    )


def buy_and_hold(prices: pd.DataFrame) -> pd.DataFrame:
    """Equal-weight, always-invested weights: the benchmark to beat."""
    n = prices.shape[1]
    return pd.DataFrame(1.0 / n, index=prices.index, columns=prices.columns)
