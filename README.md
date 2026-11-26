# Quant Finance Projects

A portfolio of quantitative finance projects, built step by step: each one
starts from an idea, tests it honestly, and explains what the results do and
don't show.

Every project follows the same discipline: a written hypothesis with a rejection
rule, an in-sample / out-of-sample split, causal (look-ahead-free) signals,
trading costs, and an honest verdict, including when the idea fails.

| # | Project | Question | Finding | Skills |
|---|---|---|---|---|
| 1 | [Momentum backtest](projects/01_momentum_backtest/) | Do a 50/200-day MA crossover or 12-1 momentum beat buy and hold on 7 ETFs? | No on Sharpe (out of sample 0.60 and 0.74 vs 0.74; confidence intervals overlap). The MA filter cuts drawdowns in slow bear markets (2008: −10% vs −38%) but not fast crashes. Best in-sample parameters underperformed out of sample. | Data cleaning, look-ahead-free backtesting, costs, Sharpe inference, overfitting checks |
| 2 | [Theta-gamma coupling](projects/02_theta_gamma_coupling/) | Does a neuroscience phase-amplitude coupling signal, or a calendar (turn-of-month) version of it, predict returns? | No coupling with causal filters. Turn-of-month beat buy and hold in sample (Sharpe 0.58 vs 0.50) but not out of sample (0.39 vs 0.60): the effect faded after 2018. | Signal processing, causal FIR filters, surrogate tests, Bonferroni correction |
| 3 | [EMD rhythms](projects/03_emd_rhythms/) | Can empirical mode decomposition find real cycles in returns? | IMF periods match a pure-noise benchmark; only short-term (~3-day) reversal stands out. 11 of 87 coupled pairs in sample, 0 survived out of sample. | EMD/CEEMDAN, noise benchmarks, multiple testing |
| 4 | [Torus volume forecast](projects/04_torus_volume/) | Do cyclic (time-of-day, weekday, month) features forecast BTC 15-minute volume? | Daily shape + weekday + volume level beat the slot-average baseline by 12.5% (RMSE 0.703 vs 0.804); month cycle and interactions add nothing (ablation). | Feature engineering, OLS, ablation, crypto market data |
| 5 | [Monte Carlo risk](projects/05_monte_carlo/) | How much can a multi-asset portfolio lose, and can the risk model be trusted? | One-year VaR99 ≈ €22.5k on €100k; block bootstrap gives the largest ES99 (€28.3k). Normal VaR breached 58 times vs 22 expected; filtered historical simulation is best (32, Kupiec p = 0.05). 2008 replay (−33%) exceeds simulated ES. | Monte Carlo, bootstrap, VaR/ES, EWMA, Kupiec backtest, stress tests |

**Next:** mean-reversion pairs trading (cointegration, z-scores), options pricer, equity factor model, and a fundamental track (sector analysis, DCF, stock pitch).

## Layout

```
src/qfp/        shared code reused across projects
  data.py       fetch (yfinance, cached) and clean price data
  backtest.py   vectorised backtester with a one-day signal delay and costs
  metrics.py    CAGR, volatility, Sharpe, Sortino, drawdown, turnover
  pac.py        causal band-pass filters, phase-amplitude coupling, surrogates
  emd.py        empirical mode decomposition helpers and noise benchmark
  montecarlo.py portfolio simulation, VaR/ES, Kupiec test
projects/       one folder per project, each with its own README write-up
tests/          pytest suite, including look-ahead bias checks
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python projects/01_momentum_backtest/run.py   # each project has its own run script
```
