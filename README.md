# Quant Finance Projects

A portfolio of quantitative finance projects, built step by step: each one
starts from an idea, tests it honestly, and explains what the results do and
don't show.

| # | Project | Shows | Status |
|---|---|---|---|
| 1 | [Momentum strategy backtest](projects/01_momentum_backtest/) | Data cleaning, signal design, look-ahead-free backtesting, benchmark comparison | In progress |
| 2 | Monte Carlo risk simulator | Simulation, VaR and expected shortfall, stress testing | Planned |
| 3 | Mean-reversion pairs trading | Cointegration, z-scores, out-of-sample stat arb | Planned |
| 4 | Options pricer | Black-Scholes, Monte Carlo, binomial trees, implied volatility | Planned |
| 5 | Equity factor model | Factor construction, Fama-MacBeth, portfolio optimisation | Planned |
| 6 | Sector analysis | Industry structure, competition, regulation, profit pools | Planned |
| 7 | DCF valuation model | Three-statement model, WACC, enterprise value | Planned |
| 8 | Stock pitch | Investment thesis, valuation, risks, price target | Planned |

## Layout

```
src/qfp/        shared code reused across projects
  data.py       fetch (yfinance, cached) and clean price data
  backtest.py   vectorised backtester with a one-day signal delay and costs
  metrics.py    CAGR, volatility, Sharpe, Sortino, drawdown, turnover
projects/       one folder per project, each with its own README write-up
tests/          pytest suite, including look-ahead bias checks
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python projects/01_momentum_backtest/run.py
```
