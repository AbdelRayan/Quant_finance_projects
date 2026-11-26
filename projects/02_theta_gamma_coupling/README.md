# Project 2: Theta-gamma coupling as a trading signal

Borrowing phase-amplitude coupling (PAC) from neuroscience: in the brain, the
amplitude of fast gamma oscillations is nested in the phase of slower theta
oscillations. Here we ask the same question of market returns: does the size
of fast moves depend on where we are in a slower cycle, and can that be traded?

## Status

- [x] Causal PAC toolkit: band-pass phase/amplitude, Tort modulation index, surrogate test (`src/qfp/pac.py`, `tests/test_pac.py`)
- [x] Step 1: exploration on 7 ETFs (`explore.py`). A (filtered theta/gamma): no coupling, p 0.35–0.92. B (calendar month): volatility coupling for TLT (p 0.014) and GLD (p 0.038), not significant after Bonferroni for 14 tests; clear turn-of-the-month pattern in equity *returns*.
- [x] Step 2: rule: hold the 5 equity ETFs from the 5th-last to the 1st trading day of the month, cash otherwise (`strategy.turn_of_month`)
- [ ] Step 3: backtest vs buy and hold, in and out of sample, plus window sensitivity (`run.py`)
- [ ] Step 4: robustness (bands, window length, surrogates, multiple-testing correction)
- [ ] Step 5: results and limitations write-up

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
