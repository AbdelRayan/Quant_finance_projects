# Project 2: Theta-gamma coupling as a trading signal

Borrowing phase-amplitude coupling (PAC) from neuroscience: in the brain, the
amplitude of fast gamma oscillations is nested in the phase of slower theta
oscillations. Here we ask the same question of market returns: does the size
of fast moves depend on where we are in a slower cycle, and can that be traded?

## Status

- [x] Causal PAC toolkit: band-pass phase/amplitude, Tort modulation index, surrogate test (`src/qfp/pac.py`, `tests/test_pac.py`)
- [ ] Step 1: exploration on 7 ETFs (`explore.py`): is there significant coupling at all?
- [ ] Step 2: hypothesis and trading rule (depends on step 1)
- [ ] Step 3: backtest vs buy and hold, in and out of sample, with the Project 1 engine
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

## Why causal filters

`filtfilt` and the FFT Hilbert transform use samples after time t to estimate
the phase at t. In a backtest that is look-ahead bias: the strategy would
"know" where the cycle goes next. `qfp.pac` only uses past data;
`tests/test_pac.py::test_phase_and_amplitude_do_not_look_ahead` proves it.
The price is a delay (about half the filter length) and noisier phase.

## Run

    python projects/02_theta_gamma_coupling/explore.py
