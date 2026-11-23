"""Run the Project 1 backtest: strategy vs buy and hold.

Usage (from the repo root, after ``pip install -e .[dev]``):

    python projects/01_momentum_backtest/run.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from qfp.backtest import buy_and_hold, run_backtest
from qfp.data import clean_prices, fetch_prices
from qfp.metrics import drawdown, summary
from strategy import ma_crossover, momentum_12_1

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]
START = "2005-01-01"
COST_BPS = 5.0
TOP_N = 3  # 12-1 momentum holds the 3 strongest of 7 ETFs
OUT_OF_SAMPLE_START = "2018-01-01"  # tune on data before this, report after it


def main() -> None:
    raw = fetch_prices(TICKERS, start=START)
    prices, report = clean_prices(raw)
    print("Cleaning report:", {k: v for k, v in report.items() if k != "large_jumps"})
    print(f"Large one-day moves to inspect: {len(report['large_jumps'])}")

    results = {
        "MA crossover": run_backtest(prices, ma_crossover(prices), cost_bps=COST_BPS),
        "12-1 momentum": run_backtest(prices, momentum_12_1(prices, top_n=TOP_N), cost_bps=COST_BPS),
        "Buy and hold": run_backtest(prices, buy_and_hold(prices), cost_bps=COST_BPS),
    }

    for label, sl in [("In-sample", slice(None, OUT_OF_SAMPLE_START)),
                      ("Out-of-sample", slice(OUT_OF_SAMPLE_START, None))]:
        table = pd.DataFrame({
            name: summary(res.returns[sl], res.turnover[sl]) for name, res in results.items()
        })
        print(f"\n{label}\n{table.round(3)}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for name, res in results.items():
        res.equity.plot(ax=ax1, label=name)
    ax1.set_ylabel("Growth of $1")
    ax1.set_yscale("log")
    ax1.axvline(pd.Timestamp(OUT_OF_SAMPLE_START), color="grey", linestyle="--")
    ax1.legend()
    for name, res in results.items():
        drawdown(res.returns).plot(ax=ax2, label=name)
    ax2.set_ylabel("Drawdown")
    fig.tight_layout()
    fig.savefig("projects/01_momentum_backtest/equity_curve.png", dpi=120)
    print("\nSaved projects/01_momentum_backtest/equity_curve.png")


if __name__ == "__main__":
    main()
