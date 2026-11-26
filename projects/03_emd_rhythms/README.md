# Project 3: Letting the data choose the rhythms (EMD + coupling)

Project 2 picked theta and gamma bands by hand. Here empirical mode
decomposition (EMD) finds each ETF's own rhythms, and we test phase-amplitude
coupling between them, the way one would analyse EEG without assuming
standard bands.

## Status

- [x] EMD helpers: decomposition, IMF periods, shuffled-noise benchmark (`src/qfp/emd.py`, `tests/test_emd.py`)
- [x] Discovery and out-of-sample test script (`discover.py`)
- [ ] Step 1: run on real data and read the IMF tables
- [ ] Step 2: if any coupling survives out of sample, design and backtest a rule
- [ ] Step 3: write-up

## Method

1. **Discover (2005–2017 only).** EMD on daily log returns; each IMF's mean
   period (from zero crossings) and energy share.
2. **Is it a rhythm or noise?** EMD splits even white noise into IMFs with
   periods that roughly double (≈3, 6, 12, 24 … days). So each IMF's energy is
   compared with the same IMF of shuffled returns; only IMFs above the noise
   95th percentile count as genuine rhythms.
3. **Coupling.** For every pair of IMFs: slow-IMF phase vs fast-IMF amplitude
   (Hilbert transform), Tort modulation index, time-shift surrogates,
   corrected for the number of tests. Only slow IMFs up to 126 days (enough
   cycles to test out of sample) and pairs where the slow period is at least
   twice the fast one (nesting) are tested.
4. **Out of sample (2018–).** EMD and the Hilbert transform both use future
   samples, so they can't generate trading signals. For each candidate pair,
   bands are rebuilt around the discovered periods with the *causal* filters
   from `qfp.pac` and tested on unseen data.

## Run

    pip install -e ".[dev]"   # adds scipy and EMD-signal
    python projects/03_emd_rhythms/discover.py
