"""Backtest the turn-of-the-month rule vs buy and hold on equity ETFs.

Usage (from the repo root):

    python projects/02_theta_gamma_coupling/run.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from qfp.backtest import buy_and_hold, run_backtest
from qfp.data import clean_prices, fetch_prices
from qfp.metrics import drawdown, sharpe_ratio, summary
from strategy import turn_of_month

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM"]
START = "2005-01-01"
COST_BPS = 5.0
OUT_OF_SAMPLE_START = "2018-01-01"
N_LAST, N_FIRST = 5, 1  # chosen from the phase table in explore.py


def main() -> None:
    prices, _ = clean_prices(fetch_prices(TICKERS, start=START))
    signal = turn_of_month(prices, N_LAST, N_FIRST)
    results = {
        f"Turn of month ({N_LAST}+{N_FIRST})": run_backtest(prices, signal, cost_bps=COST_BPS),
        "Buy and hold": run_backtest(prices, buy_and_hold(prices), cost_bps=COST_BPS),
    }
    print(f"Time invested: {(signal.sum(axis=1) > 0).mean():.0%} of days")

    periods = [("In-sample", slice(None, OUT_OF_SAMPLE_START)), ("Out-of-sample", slice(OUT_OF_SAMPLE_START, None))]
    for label, sl in periods:
        table = pd.DataFrame({n: summary(r.returns[sl], r.turnover[sl]) for n, r in results.items()})
        print(f"\n{label}\n{table.round(3)}")

    # Window sensitivity: chosen on in-sample, judged out-of-sample.
    grid = {}
    for n_last in range(1, 8):
        for n_first in range(0, 4):
            res = run_backtest(prices, turn_of_month(prices, n_last, n_first), cost_bps=COST_BPS)
            grid[(n_last, n_first)] = {
                "Sharpe in": sharpe_ratio(res.returns[:OUT_OF_SAMPLE_START]),
                "Sharpe out": sharpe_ratio(res.returns[OUT_OF_SAMPLE_START:]),
            }
    grid = pd.DataFrame(grid).T.rename_axis(["last days", "first days"])
    print("\nWindow sensitivity (Sharpe)\n", grid.unstack("first days").round(2), sep="")
    best = grid["Sharpe in"].idxmax()
    print(f"\nBest in-sample window: last {best[0]} + first {best[1]} days "
          f"-> Sharpe in {grid.loc[best, 'Sharpe in']:.2f}, out {grid.loc[best, 'Sharpe out']:.2f}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name, res in results.items():
        res.equity.plot(ax=ax1, label=name)
        drawdown(res.returns).plot(ax=ax2, label=name)
    ax1.set_yscale("log")
    ax1.set_ylabel("Growth of $1")
    ax1.axvline(pd.Timestamp(OUT_OF_SAMPLE_START), color="grey", linestyle="--")
    ax1.legend()
    ax2.set_ylabel("Drawdown")
    fig.tight_layout()
    fig.savefig("projects/02_theta_gamma_coupling/equity_curve.png", dpi=120)
    print("\nSaved projects/02_theta_gamma_coupling/equity_curve.png")


if __name__ == "__main__":
    main()
