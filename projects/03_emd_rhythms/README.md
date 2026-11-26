# Project 3: Letting the data choose the rhythms (EMD + coupling)

Project 2 picked theta and gamma bands by hand. Here empirical mode
decomposition (EMD) finds each ETF's own rhythms, and we test phase-amplitude
coupling between them, the way one would analyse EEG without assuming
standard bands.

## Status

- [x] EMD helpers: decomposition, IMF periods, shuffled-noise benchmark (`src/qfp/emd.py`, `tests/test_emd.py`)
- [x] Discovery and out-of-sample test script (`discover.py`)
- [x] Step 1: run on real data and read the IMF tables
- [x] Step 2: no coupling survived out of sample, so no trading rule (see Results)
- [x] Step 3: write-up

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

## Results (7 ETFs, daily log returns)

### 1. What rhythms does EMD find? (2005–2017)

Every ETF splits into 8–9 IMFs with mean periods of about **2.8, 5.5, 11, 22,
45, 100, 230 … trading days**. These are almost exactly the periods EMD
produces on *shuffled* returns (2.8, 5.4, 10.4, 20.5, 42, 90 …): the doubling
pattern of a noise filter bank.

- **IMFs 2–9: no genuine rhythm.** None carries more energy than the same IMF of shuffled returns.
- **IMF 1 (≈3-day period): more energy than noise in all 7 ETFs** (e.g. SPY 0.63 vs a noise 95th percentile of 0.50). Extra energy at the fastest scale means consecutive daily returns tend to alternate sign: short-term **reversal** (negative day-to-day autocorrelation). Because energy shares sum to 1, the slower IMFs then look slightly *below* noise.

### 2. Coupling between IMFs, in sample

11 of 87 slow-phase / fast-amplitude pairs had p = 0.005, the minimum possible
with 200 surrogates. By chance alone we'd expect about 0.4. So in sample,
coupling looks real.

### 3. Out of sample (2018–), causal filters at the discovered periods

**None of the 11 candidates survives** (p = 0.10 to 0.87; Bonferroni threshold
0.0045). The in-sample coupling did not carry over.

### Interpretation

- **Why did in-sample coupling vanish?** EMD and the Hilbert transform are non-causal and adapt to the data: in volatile periods (2008) EMD puts extrema closer together, so IMF amplitudes and phases are tied together *by the decomposition itself*. Add volatility clustering and one crisis-heavy sample, and coupling appears that a causal, out-of-sample test does not confirm.
- **What EMD did find is mundane but real:** daily ETF returns look like noise across scales, apart from slight short-term reversal at the 1–3 day scale.
- **Link to Project 2:** brain-style nested rhythms are absent inside prices; structure comes from *outside clocks* (the calendar) and from microstructure (reversal), not from internal oscillations.

### Limitations

- Plain EMD (mode mixing); CEEMDAN (`decompose(..., ensemble=True)`) is the natural robustness check.
- 200 surrogates can't reach a Bonferroni-level p in sample, so the in-sample screen is permissive by design; the out-of-sample test does the filtering.
- Daily data only; intraday data might show richer structure.

### Conclusion

Letting EMD choose the bands removes the "my own speculation" problem, and the
answer is clear: **no tradeable theta-gamma-style coupling in daily ETF
returns**. The 1–3 day reversal in IMF 1 is the one signal worth following up.
