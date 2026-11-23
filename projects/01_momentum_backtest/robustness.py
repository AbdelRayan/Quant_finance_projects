"""Robustness checks for Project 1: do the results survive small changes?

Usage (from the repo root):

    python projects/01_momentum_backtest/robustness.py

Prints three tables:
1. Parameter sensitivity: Sharpe and max drawdown for nearby parameter choices.
2. Crisis periods: return of each strategy in 2008, March 2020 and 2022.
3. Sharpe with a 95% confidence interval (standard error ~ sqrt((1 + SR^2/2) / years)).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qfp.backtest import buy_and_hold, run_backtest
from qfp.data import clean_prices, fetch_prices
from qfp.metrics import TRADING_DAYS, max_drawdown, sharpe_ratio
from run import COST_BPS, OUT_OF_SAMPLE_START, START, TICKERS, TOP_N
from strategy import ma_crossover, momentum_12_1

MA_WINDOWS = [(20, 100), (50, 200), (100, 300)]
MOM_LOOKBACKS = [126, 189, 252]  # 6, 9, 12 months
MOM_TOP_N = [1, 2, 3, 4]
CRISES = {
    "2008 crisis": ("2008-01-01", "2009-03-09"),
    "Covid crash": ("2020-02-19", "2020-03-23"),
    "2022 bear": ("2022-01-01", "2022-10-12"),
}


def sharpe_ci(returns: pd.Series) -> tuple[float, float, float]:
    """Sharpe ratio with an approximate 95% confidence interval."""
    sr = sharpe_ratio(returns)
    years = len(returns) / TRADING_DAYS
    se = np.sqrt((1 + sr**2 / 2) / years)
    return sr, sr - 1.96 * se, sr + 1.96 * se


def stats(returns: pd.Series) -> dict:
    ins = returns[:OUT_OF_SAMPLE_START]
    oos = returns[OUT_OF_SAMPLE_START:]
    return {
        "Sharpe in": sharpe_ratio(ins),
        "Sharpe out": sharpe_ratio(oos),
        "MaxDD in": max_drawdown(ins),
        "MaxDD out": max_drawdown(oos),
    }


def main() -> None:
    prices, _ = clean_prices(fetch_prices(TICKERS, start=START))

    rows = {}
    for fast, slow in MA_WINDOWS:
        res = run_backtest(prices, ma_crossover(prices, fast, slow), cost_bps=COST_BPS)
        rows[f"MA {fast}/{slow}"] = stats(res.returns)
    for lookback in MOM_LOOKBACKS:
        for n in MOM_TOP_N:
            sig = momentum_12_1(prices, top_n=n, lookback=lookback)
            res = run_backtest(prices, sig, cost_bps=COST_BPS)
            rows[f"Mom {lookback // 21}m top{n}"] = stats(res.returns)
    bh = run_backtest(prices, buy_and_hold(prices), cost_bps=COST_BPS)
    rows["Buy and hold"] = stats(bh.returns)
    print("1. Parameter sensitivity\n", pd.DataFrame(rows).T.round(3), sep="")

    main_runs = {
        "MA 50/200": run_backtest(prices, ma_crossover(prices), cost_bps=COST_BPS).returns,
        f"Mom 12-1 top{TOP_N}": run_backtest(prices, momentum_12_1(prices, top_n=TOP_N), cost_bps=COST_BPS).returns,
        "Buy and hold": bh.returns,
    }

    crisis = {
        name: {label: (1 + r[start:end]).prod() - 1 for label, (start, end) in CRISES.items()}
        for name, r in main_runs.items()
    }
    print("\n2. Total return in crisis periods\n", pd.DataFrame(crisis).round(3), sep="")

    ci = {
        name: dict(zip(["Sharpe", "95% low", "95% high"], sharpe_ci(r[OUT_OF_SAMPLE_START:])))
        for name, r in main_runs.items()
    }
    print("\n3. Out-of-sample Sharpe with 95% confidence interval\n", pd.DataFrame(ci).T.round(2), sep="")


if __name__ == "__main__":
    main()
