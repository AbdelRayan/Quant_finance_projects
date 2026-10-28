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
from strategy import ma_crossover

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]
START = "2005-01-01"
COST_BPS = 5.0
OUT_OF_SAMPLE_START = "2018-01-01"  # tune on data before this, report after it


def main() -> None:
    raw = fetch_prices(TICKERS, start=START)
    prices, report = clean_prices(raw)
    print("Cleaning report:", {k: v for k, v in report.items() if k != "large_jumps"})
    print(f"Large one-day moves to inspect: {len(report['large_jumps'])}")

    strategy = run_backtest(prices, ma_crossover(prices), cost_bps=COST_BPS)
    benchmark = run_backtest(prices, buy_and_hold(prices), cost_bps=COST_BPS)

    for label, sl in [("In-sample", slice(None, OUT_OF_SAMPLE_START)),
                      ("Out-of-sample", slice(OUT_OF_SAMPLE_START, None))]:
        table = pd.DataFrame({
            "MA crossover": summary(strategy.returns[sl], strategy.turnover[sl]),
            "Buy and hold": summary(benchmark.returns[sl], benchmark.turnover[sl]),
        })
        print(f"\n{label}\n{table.round(3)}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    strategy.equity.plot(ax=ax1, label="MA crossover")
    benchmark.equity.plot(ax=ax1, label="Buy and hold")
    ax1.set_ylabel("Growth of $1")
    ax1.set_yscale("log")
    ax1.axvline(pd.Timestamp(OUT_OF_SAMPLE_START), color="grey", linestyle="--")
    ax1.legend()
    drawdown(strategy.returns).plot(ax=ax2, label="MA crossover")
    drawdown(benchmark.returns).plot(ax=ax2, label="Buy and hold")
    ax2.set_ylabel("Drawdown")
    fig.tight_layout()
    fig.savefig("projects/01_momentum_backtest/equity_curve.png", dpi=120)
    print("\nSaved projects/01_momentum_backtest/equity_curve.png")


if __name__ == "__main__":
    main()
