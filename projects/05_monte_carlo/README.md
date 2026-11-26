# Project 5: Monte Carlo risk simulator

Simulate thousands of one-year paths for a multi-asset ETF portfolio and turn
them into risk numbers a risk manager would use: percentile outcomes,
probability of loss, Value at Risk (VaR), Expected Shortfall (ES) and drawdowns.
Then check whether the risk model can be trusted (VaR backtest) and what
happens in crises (stress tests).

## Status

- [x] Simulation engine: normal, bootstrap and block bootstrap; VaR/ES; Kupiec test (`src/qfp/montecarlo.py`, `tests/test_montecarlo.py`)
- [x] Run script: one-year outlook, VaR backtest, stress tests, fan chart (`run.py`)
- [x] Volatility-aware VaR: EWMA normal and filtered historical simulation
- [x] Run on real data and read the results
- [x] Results and limitations write-up

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

## Results (history 2005-01 to 2026-10)

### 1. One-year outlook, EUR 100,000, 10,000 paths per method

| | Normal | Bootstrap | Block bootstrap |
|---|---|---|---|
| 5th percentile | 85,663 | 85,538 | 87,571 |
| Median | 109,536 | 109,617 | 110,761 |
| 95th percentile | 139,837 | 141,927 | 135,083 |
| P(loss) | 27.1% | 27.0% | 21.6% |
| VaR 95% | 14,337 | 14,462 | 12,429 |
| ES 95% | 19,374 | 19,743 | 19,015 |
| VaR 99% | 22,515 | 22,957 | 22,633 |
| ES 99% | 26,662 | 26,685 | **28,281** |
| Median max drawdown | -12.4% | -12.0% | -10.6% |
| 5% worst max drawdown | -23.4% | -23.2% | **-24.7%** |

### 2. Backtest of 1-day 99% VaR from 2018-01-01 (trailing 500-day window, 2,220 days, 22.2 breaches expected)

| Model | Breaches | Kupiec p-value | Verdict at 5% |
|---|---|---|---|
| Normal | 58 | 0.0000 | Rejected |
| EWMA normal (λ = 0.94) | 53 | 0.0000 | Rejected |
| Historical | 34 | 0.0196 | Rejected |
| Filtered historical | **32** | 0.0499 | Borderline (just rejected) |
| Filtered historical, all history (expanding window) | 35 | 0.0118 | Rejected |

### 3. Stress tests (portfolio return)

| Scenario | Return | EUR |
|---|---|---|
| 2008 crisis | -32.7% | -32,676 |
| 2022 bear | -25.0% | -25,036 |
| Covid crash | -22.8% | -22,836 |
| Hypothetical shock (equities -30 to -35%, TLT +10%, GLD +5%) | -21.4% | -21,429 |

## Reading the figure (`monte_carlo.png`)

- **(a) Fan chart:** each grey line is one simulated year. The dark band holds the middle 50% of paths, the light band 90%. The band widens to the right because uncertainty grows with time. The dashed line is break-even.
- **(b) Value after 1 year:** one histogram per method. Left of the dashed start line is a loss. The red line is VaR99 (only 1% of years end left of it, shaded), the dotted line is ES99 (the average of that shaded 1%).
- **(c) VaR backtest:** grey is the real daily return; the coloured lines are each model's VaR line for that day. A dot is a breach, a day the loss fell below the line. The normal line barely moves; the filtered historical line drops when markets get wild. A good model has about 1% dots, spread out rather than clustered.

## Interpretation

1. **The methods agree on VaR but not on the tail.** VaR 99% is about EUR 22.5-23k whichever way we simulate. The difference shows up beyond it: the block bootstrap has the narrowest middle (lowest P(loss), 21.6%) but the largest ES 99% (EUR 28.3k) and the worst 5% drawdown. Keeping consecutive days together keeps bad days together, so calm years look calmer and bad years look worse. VaR alone would hide this; ES shows it.
2. **Fat tails matter more than volatility timing.** Making the normal model react to current volatility (EWMA) only cut breaches from 58 to 53. Replacing the normal curve with the empirical distribution cut them to 34. Doing both (filtered historical) gave the best result, 32, but still about 10 more breaches than expected.
3. **No model fully passes, and more data did not fix it.** We tested whether the excess breaches came from estimating a 1% quantile from only ~5 tail days, by giving filtered historical all standardized history since 2005 (~30+ tail days). Breaches rose from 32 to 35, so that idea is rejected. The 500-day version adapts better to the recent shape of the tails, and the remaining breaches most likely come from sudden jumps (e.g. March 2020) that start from a calm day, when yesterday's volatility estimate is still low.
4. **Stress tests see what the simulation misses.** Replaying 2008 loses 32.7%, worse than the simulated one-year ES 99% (26.7-28.3k). Even though 2008 is in the history, resampling days or 20-day blocks rarely rebuilds a full year-long crisis. This is why risk teams report stress tests next to VaR and ES.

## Limitations

- Returns are the ETFs' own (USD) returns; the EUR figures only scale the result and ignore EUR/USD risk.
- Daily rebalancing to equal weight and no transaction costs.
- One portfolio and one test period (2018 onward); Kupiec only checks the breach count, not whether breaches cluster (Christoffersen's independence test would).
- λ = 0.94 is the RiskMetrics default, not tuned, to avoid fitting the backtest.

## Conclusion

For this portfolio a risk number built on the normal distribution understates daily 99% risk by more than 2x in breach terms. Filtered historical simulation, which combines real fat-tailed returns with current volatility, is the best of the four models and sits right at the edge of the Kupiec test. The practical lesson: report ES next to VaR, use a fat-tailed, volatility-aware model, and always add stress tests for crises the data cannot reproduce.
