"""Project 5: Monte Carlo risk simulator for a multi-asset ETF portfolio.

Usage (from the repo root):

    python projects/05_monte_carlo/run.py

1. Simulate 10,000 one-year paths with three methods (normal, bootstrap,
   block bootstrap) and compare percentiles, probability of loss, VaR and ES.
2. Backtest 1-day 99% VaR on 2018 onward (trailing 500-day window) with the
   Kupiec test: does the model breach as rarely as it promises?
3. Stress tests: replay historical crises and a hypothetical shock.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from qfp.data import clean_prices, fetch_prices
from qfp.montecarlo import METHODS, kupiec_pof, paths_from_returns, simulate_portfolio_returns, var_es

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]
WEIGHTS = np.ones(len(TICKERS)) / len(TICKERS)  # equal weight, as in Project 1's buy and hold
START = "2005-01-01"
HORIZON, N_PATHS, BLOCK = 252, 10_000, 20
START_VALUE = 100_000  # euros, for readable numbers
BACKTEST_START, WINDOW, LEVEL = "2018-01-01", 500, 0.99
CRISES = {"2008 crisis": ("2008-09-01", "2009-03-09"), "Covid crash": ("2020-02-19", "2020-03-23"),
          "2022 bear": ("2022-01-01", "2022-10-12")}
SHOCK = {"SPY": -0.30, "QQQ": -0.35, "IWM": -0.35, "EFA": -0.30, "EEM": -0.35, "TLT": 0.10, "GLD": 0.05}


def max_drawdowns(paths: np.ndarray) -> np.ndarray:
    return (paths / np.maximum.accumulate(paths, axis=1) - 1).min(axis=1)


def main() -> None:
    prices, _ = clean_prices(fetch_prices(TICKERS, start=START))
    prices = prices[TICKERS]
    returns = prices.pct_change().dropna()
    port_hist = returns.to_numpy() @ WEIGHTS

    # 1. One-year simulation
    rows, all_paths = {}, {}
    for method in METHODS:
        sim = simulate_portfolio_returns(returns, WEIGHTS, HORIZON, N_PATHS, method, BLOCK)
        paths = paths_from_returns(sim, START_VALUE)
        all_paths[method] = paths
        pnl = paths[:, -1] - START_VALUE
        var95, es95 = var_es(pnl, 0.95)
        var99, es99 = var_es(pnl, 0.99)
        p5, p50, p95 = np.percentile(paths[:, -1], [5, 50, 95])
        rows[method] = {"5th pct": p5, "Median": p50, "95th pct": p95, "P(loss)": (pnl < 0).mean(),
                        "VaR 95%": var95, "ES 95%": es95, "VaR 99%": var99, "ES 99%": es99,
                        "Median max DD": np.median(max_drawdowns(paths)),
                        "5% worst max DD": np.percentile(max_drawdowns(paths), 5)}
    table = pd.DataFrame(rows)
    print(f"1. One-year outlook for EUR {START_VALUE:,}, {N_PATHS:,} paths per method "
          f"(history {returns.index[0]:%Y-%m} to {returns.index[-1]:%Y-%m})")
    print(table.map(lambda v: f"{v:,.0f}" if abs(v) > 1 else f"{v:.1%}").to_string())

    # 2. 1-day VaR backtest
    port = pd.Series(port_hist, index=returns.index)
    roll = port.rolling(WINDOW)
    var_normal = -(roll.mean() + norm.ppf(1 - LEVEL) * roll.std()).shift(1)
    var_hist = -roll.quantile(1 - LEVEL).shift(1)
    test = port[BACKTEST_START:]
    bt = {}
    for name, var in [("Normal", var_normal), ("Historical", var_hist)]:
        v = var[BACKTEST_START:]
        breaches = int((test < -v).sum())
        bt[name] = {"Days": len(test), "Expected breaches": round(len(test) * (1 - LEVEL), 1),
                    "Actual breaches": breaches, "Kupiec p-value": round(kupiec_pof(len(test), breaches, LEVEL), 4)}
    print(f"\n2. Backtest of 1-day {LEVEL:.0%} VaR from {BACKTEST_START} (trailing {WINDOW}-day window)")
    print(pd.DataFrame(bt).T.to_string())

    # 3. Stress tests
    stress = {name: (1 + port[a:b]).prod() - 1 for name, (a, b) in CRISES.items()}
    stress["Hypothetical shock"] = float(np.dot(WEIGHTS, [SHOCK[t] for t in TICKERS]))
    print("\n3. Stress tests (portfolio return)")
    for name, r in stress.items():
        print(f"   {name:20s} {r:7.1%}   (EUR {r * START_VALUE:,.0f})")

    # Figure: fan chart (block bootstrap) and terminal value distributions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), layout="constrained")
    paths = all_paths["block"]
    days = np.arange(HORIZON + 1)
    for lo, hi, alpha in [(5, 95, 0.2), (25, 75, 0.35)]:
        ax1.fill_between(days, np.percentile(paths, lo, axis=0), np.percentile(paths, hi, axis=0),
                         alpha=alpha, color="tab:blue", label=f"{lo}th–{hi}th pct")
    ax1.plot(days, np.median(paths, axis=0), color="tab:blue", label="Median")
    ax1.plot(days, paths[:20].T, color="grey", lw=0.5, alpha=0.5)
    ax1.set(title="Block bootstrap: 1-year portfolio paths", xlabel="Trading days", ylabel="Portfolio value (EUR)")
    ax1.legend(loc="upper left")
    for method in METHODS:
        ax2.hist(all_paths[method][:, -1], bins=120, histtype="step", label=method, density=True)
    ax2.axvline(START_VALUE, color="black", lw=0.8)
    ax2.set(title="Value after 1 year", xlabel="Portfolio value (EUR)", ylabel="Density")
    ax2.legend()
    fig.savefig("projects/05_monte_carlo/monte_carlo.png", dpi=140)
    print("\nSaved projects/05_monte_carlo/monte_carlo.png")


if __name__ == "__main__":
    main()
