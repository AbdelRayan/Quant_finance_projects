# Project 5: Monte Carlo risk simulator

Simulate thousands of one-year paths for a multi-asset ETF portfolio and turn
them into risk numbers a risk manager would use: percentile outcomes,
probability of loss, Value at Risk (VaR), Expected Shortfall (ES) and drawdowns.
Then check whether the risk model can be trusted (VaR backtest) and what
happens in crises (stress tests).

## Status

- [x] Simulation engine: normal, bootstrap and block bootstrap; VaR/ES; Kupiec test (`src/qfp/montecarlo.py`, `tests/test_montecarlo.py`)
- [x] Run script: one-year outlook, VaR backtest, stress tests, fan chart (`run.py`)
- [ ] Run on real data and read the results
- [ ] Results and limitations write-up

## Setup

- Portfolio: equal weight in SPY, QQQ, IWM, EFA, EEM, TLT, GLD (Project 1's buy and hold), rebalanced daily, EUR 100,000.
- History: daily returns from 2005.
- 10,000 paths × 252 trading days per method.

## Three ways to simulate the future

| Method | How | Keeps | Misses |
|---|---|---|---|
| Normal | Draw from a multivariate normal with historical mean and covariance | Average correlations | Fat tails, crashes, volatility clustering |
| Bootstrap | Draw whole historical days at random | Fat tails, same-day correlations | Volatility clustering |
| Block bootstrap | Draw 20-day blocks of consecutive history | Fat tails, correlations, calm/stormy spells | Regimes longer than a block |

## Risk measures

- **VaR 99%**: the loss exceeded in only 1% of outcomes. "We lose at most X on 99 of 100 years."
- **ES 99%**: the average loss *in* that worst 1%. It looks into the tail VaR ignores, which is why Basel III moved market-risk capital from VaR to ES.
- **VaR backtest (Kupiec)**: a 99% 1-day VaR should be breached on about 1% of days. Too many breaches means the model understates risk.

## Run

    python projects/05_monte_carlo/run.py
