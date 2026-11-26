# Project 2: Theta-gamma coupling as a trading signal

Borrowing phase-amplitude coupling (PAC) from neuroscience: in the brain, the
amplitude of fast gamma oscillations is nested in the phase of slower theta
oscillations. Here we ask the same question of market returns: does the size
of fast moves depend on where we are in a slower cycle, and can that be traded?

## Status

- [x] Causal PAC toolkit: band-pass phase/amplitude, Tort modulation index, surrogate test (`src/qfp/pac.py`, `tests/test_pac.py`)
- [x] Step 1: exploration on 7 ETFs (`explore.py`). A (filtered theta/gamma): no coupling, p 0.35–0.92. B (calendar month): volatility coupling for TLT (p 0.014) and GLD (p 0.038), not significant after Bonferroni for 14 tests; clear turn-of-the-month pattern in equity *returns*.
- [x] Step 2: rule: hold the 5 equity ETFs from the 5th-last to the 1st trading day of the month, cash otherwise (`strategy.turn_of_month`)
- [x] Step 3: backtest vs buy and hold, in and out of sample, plus window sensitivity (`run.py`)
- [x] Step 4: robustness: surrogates, Bonferroni correction, window grid chosen in sample only
- [x] Step 5: results and limitations write-up

## From EEG to markets

| | EEG | Markets (this project) |
|---|---|---|
| Signal | Voltage, sampled at e.g. 1000 Hz | Daily log returns, 1 sample per trading day |
| Theta (phase) | 4–8 Hz (often 5–12 Hz) | Cycles with a 20–60 trading-day period |
| Gamma (amplitude) | 30–100 Hz | Cycles with a 5–12 trading-day period (≈ short-term volatility) |
| Fastest possible rhythm | Sampling rate / 2 | 2-day period (Nyquist) |
| Phase / envelope | Hilbert transform after `filtfilt` | Causal complex FIR filters (past data only) |
| Coupling measure | Tort modulation index | Same |
| Null | Time-shifted surrogates | Same |

## Variant B: the calendar as theta

Instead of estimating a slow rhythm from prices, use the calendar month as the
theta cycle (first trading day = −180°, last = +180°) and the size of each
day's move as gamma. The phase is known in advance, so there is no filter
delay and no look-ahead risk. This links to the documented *turn-of-the-month
effect* (Ariel 1987; Lakonishok and Smidt 1988): stock returns concentrate in
the last and first few trading days of the month, often explained by salary,
pension and fund flows. The question is whether it still exists after costs.

## Why causal filters

`filtfilt` and the FFT Hilbert transform use samples after time t to estimate
the phase at t. In a backtest that is look-ahead bias: the strategy would
"know" where the cycle goes next. `qfp.pac` only uses past data;
`tests/test_pac.py::test_phase_and_amplitude_do_not_look_ahead` proves it.
The price is a delay (about half the filter length) and noisier phase.

## Run

    python projects/02_theta_gamma_coupling/explore.py   # step 1: is there coupling?
    python projects/02_theta_gamma_coupling/run.py       # step 3: backtest the rule

Note on data snooping: the 5+1 window was picked after seeing the full-sample
phase table, which includes the out-of-sample years. `run.py` therefore also
prints the window chosen on 2005–2017 only, and how it did after 2018.

## Results

### Step 1: is there coupling? (`explore.py`, 2005–2025, 7 ETFs)

| Test | Result |
|---|---|
| A. Filtered theta (20–60 d) phase vs gamma (5–12 d) amplitude | No coupling in any ETF (p = 0.35–0.92) |
| B. Calendar-month phase vs daily \|return\| | TLT p = 0.014, GLD p = 0.038, others p > 0.2. With 14 tests, the Bonferroni threshold is 0.004, so **none is significant** |
| B. Calendar-month phase vs daily return | All 5 equity ETFs: the last ~4–5 trading days and the first day average +9 to +23 bps/day; mid-month ≈ 0 or negative |

Rhythms estimated from prices do not nest the way brain rhythms do. The
calendar, an external clock, does organise returns: the turn-of-the-month effect.

### Step 3: trading the calendar phase (`run.py`, SPY, QQQ, IWM, EFA, EEM, 5 bps costs)

Rule: equal weight in the 5 equity ETFs from the 5th-last to the 1st trading
day of each month, cash otherwise (invested 29% of days).

| | Turn of month (5+1) | Buy and hold |
|---|---|---|
| **In sample (2005–2017)** | | |
| CAGR | 6.3% | 8.8% |
| Volatility | 11.8% | 21.9% |
| Sharpe | 0.58 | 0.50 |
| Max drawdown | −16% | −57% |
| **Out of sample (2018–)** | | |
| CAGR | 3.3% | 10.4% |
| Volatility | 9.5% | 19.6% |
| Sharpe | 0.39 | 0.60 |
| Max drawdown | −14% | −33% |
| Annual turnover | 24 | 0 |

**Window sensitivity.** Almost every window from "last 4–5 days + first 1–3 days"
has a positive Sharpe in both periods, so the effect is broad, not one lucky
setting. Choosing the window on 2005–2017 only (best: last 4 + first 2, Sharpe
0.75) gives 0.49 out of sample, still below buy and hold (0.60).

### Interpretation

- **In sample, the effect is strong:** 29% of the days delivered about 70% of buy-and-hold's annual return, with a quarter of the drawdown.
- **Out of sample, it weakened** and lost to buy and hold on Sharpe and return. This fits the literature: well-known calendar effects tend to shrink after publication and as trading becomes cheaper.
- **Costs matter but are not the whole story.** 24× turnover at 5 bps costs ~1.2% a year. Without costs the out-of-sample Sharpe would be about 0.47, still below 0.60.
- **Better use: timing, not a standalone strategy.** The pattern can guide *when* to invest new money or rebalance (just before month end), rather than replacing buy and hold.

### Limitations

- Cash earns 0% in the backtest. Out of the market 71% of the time, a T-bill yield (about 2% a year on average since 2018) would add roughly 1.5% a year.
- The 5+1 window was picked after seeing full-sample data (data snooping); the in-sample-only grid choice is the cleaner test.
- Only 5 broad equity ETFs; daily close-to-close data, so no intraday timing.
- Bond and gold volatility around fixed macro release dates (jobs report, CPI, FOMC) is a better-founded follow-up than generic calendar phase.

### Conclusion

A neuroscience method, used carefully (causal filters, surrogates, multiple-testing
correction), finds **no theta-gamma-style coupling inside market prices**. But it
does recover a known external rhythm, the turn of the month, which was tradeable
before 2018 and has since faded below buy and hold after costs.
