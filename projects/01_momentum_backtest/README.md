# Project 1: Momentum strategy backtest

From trading idea to tested strategy: fetch and clean historical prices, define
momentum signals and entry/exit rules, backtest without look-ahead bias, and
compare against buy and hold.

## Status

- [x] Data module: fetch, cache, clean (`src/qfp/data.py`)
- [x] Backtester with a one-day signal delay and transaction costs (`src/qfp/backtest.py`)
- [x] Metrics: CAGR, volatility, Sharpe, Sortino, max drawdown, hit rate, turnover (`src/qfp/metrics.py`)
- [x] Reference strategy: 50/200-day moving-average crossover (`strategy.py`)
- [ ] **Your turn:** write the hypothesis below
- [ ] **Your turn:** implement 12-1 momentum in `strategy.momentum_12_1` and add tests
- [ ] **Your turn:** robustness checks (other lookbacks, walk-forward, regimes)
- [ ] **Your turn:** results and limitations write-up

## 1. Hypothesis

_Write 3–5 sentences: what you expect, and why it might work (e.g. investors
under-react to news, trends persist), before looking at results._

## 2. Data

Daily adjusted closes for liquid ETFs (`run.py`, `TICKERS`) from 2005, via
yfinance, cached in `data/cache/`. Cleaning: drop tickers with under 95% coverage,
forward-fill gaps of up to 5 days (never backward-fill), and flag one-day moves
over 30% for inspection.

Known bias: the universe is chosen with today's knowledge (survivorship bias).

## 3. Rules

| | MA crossover | 12-1 momentum |
|---|---|---|
| Signal | 50-day MA above 200-day MA | Return from t−252 to t−21 |
| Entry | Signal turns on | Asset enters the top N at month end |
| Exit | Signal turns off | Asset drops out of the top N |
| Sizing | Equal weight across all assets, cash when off | Equal weight across the top N |
| Rebalance | Daily | Monthly |
| Costs | 5 bps per unit traded | 5 bps per unit traded |

## 4. Avoiding look-ahead bias

Signals at date t use prices up to the close of t; the backtester trades them
from t+1 (`signal.shift(1)`). `tests/test_backtest.py` and
`tests/test_strategy.py` check that changing future prices never changes past
returns or signals.

## 5. Results

Run `python projects/01_momentum_backtest/run.py`. Paste the in-sample and
out-of-sample tables and `equity_curve.png` here, then explain them.

## 6. Robustness and limitations

_Lookback sensitivity (20/100, 50/200, 100/300), walk-forward results,
performance in 2008, 2020 and 2022, and what the backtest does not capture._
