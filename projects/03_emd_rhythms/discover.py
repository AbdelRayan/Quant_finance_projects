"""Project 3: let EMD find each ETF's own rhythms, then test theta-gamma coupling.

Usage (from the repo root):

    python projects/03_emd_rhythms/discover.py

1. In sample (2005-2017): EMD on each ETF's daily log returns. For every IMF,
   its mean period and energy share, compared with shuffled returns. An IMF
   counts as a real rhythm only if its energy beats the 95th percentile of noise.
2. In sample: coupling between every pair of IMFs (slow IMF phase vs fast IMF
   amplitude, Hilbert transform, Tort MI, 200 time-shift surrogates),
   Bonferroni-corrected over all pairs and tickers.
3. Out of sample (2018-): for each in-sample-significant pair, rebuild the two
   bands around the discovered periods with *causal* filters and test again.
   Only this step tells us whether a rhythm could be traded.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qfp.data import clean_prices, fetch_prices
from qfp.emd import decompose, hilbert_phase_amplitude, imf_table, noise_benchmark
from qfp.pac import period_band, phase_and_amplitude, surrogate_pvalue

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]
START = "2005-01-01"
OUT_OF_SAMPLE_START = "2018-01-01"
N_SURROGATES = 200
ALPHA = 0.05
BAND_WIDTH = (0.7, 1.4)  # band = discovered period x these factors
MAX_SLOW_PERIOD = 126  # slower rhythms have too few cycles out of sample (~8 years) to test
MIN_RATIO = 2.0  # slow period must be at least 2x the fast period (nesting)


def band_around(period: float) -> tuple[float, float]:
    lo, hi = max(2.0, BAND_WIDTH[0] * period), BAND_WIDTH[1] * period
    return period_band(lo, hi)


def main() -> None:
    prices, _ = clean_prices(fetch_prices(TICKERS, start=START))
    returns = np.log(prices).diff().dropna()
    ins, oos = returns[:OUT_OF_SAMPLE_START], returns[OUT_OF_SAMPLE_START:]

    rhythm_tables, pair_rows = {}, []
    for ticker in TICKERS:
        x = ins[ticker].to_numpy()
        imfs = decompose(x)
        table = imf_table(imfs).join(noise_benchmark(x))
        table["rhythm"] = table["energy_share"] > table["noise_energy_95"]
        rhythm_tables[ticker] = table

        pa = [hilbert_phase_amplitude(m) for m in imfs]
        for slow in range(1, len(imfs)):
            if table.loc[slow + 1, "period"] > MAX_SLOW_PERIOD:
                continue
            for fast in range(slow):
                if table.loc[slow + 1, "period"] < MIN_RATIO * table.loc[fast + 1, "period"]:
                    continue
                mi, p = surrogate_pvalue(pa[slow][0], pa[fast][1], n_surrogates=N_SURROGATES)
                pair_rows.append({
                    "ticker": ticker, "fast_imf": fast + 1, "slow_imf": slow + 1,
                    "fast_period": table.loc[fast + 1, "period"], "slow_period": table.loc[slow + 1, "period"],
                    "MI": mi, "p_in": p,
                })

    print("1. IMFs per ETF, in sample (period in trading days; rhythm = energy above shuffled-noise 95th pct)")
    for ticker, table in rhythm_tables.items():
        print(f"\n{ticker}\n{table.round(3)}")

    pairs = pd.DataFrame(pair_rows)
    n_tests = len(pairs)
    threshold = ALPHA / n_tests
    min_p = 1 / (1 + N_SURROGATES)
    print(f"\n2. Coupling between IMF pairs, in sample: {n_tests} tests, Bonferroni threshold {threshold:.2e}")
    if min_p > threshold:
        print(f"   Note: with {N_SURROGATES} surrogates the smallest possible p is {min_p:.4f}, so we use p == min_p "
              "(no surrogate beat the observed MI) as 'significant' and correct again out of sample.")
        significant = pairs[pairs["p_in"] <= min_p]
    else:
        significant = pairs[pairs["p_in"] < threshold]
    print(pairs.sort_values("p_in").head(15).round(4).to_string(index=False))
    print(f"\n   Candidate pairs: {len(significant)}")

    if significant.empty:
        print("\n3. No candidate pairs, nothing to test out of sample.")
        return
    rows = []
    for _, row in significant.iterrows():
        x = oos[row["ticker"]]
        pa_c = phase_and_amplitude(x, band_around(row["slow_period"]), band_around(row["fast_period"]))
        mi, p = surrogate_pvalue(pa_c["phase"].to_numpy(), pa_c["amplitude"].to_numpy(), n_surrogates=N_SURROGATES)
        rows.append({**row[["ticker", "fast_period", "slow_period"]].to_dict(), "MI_out": mi, "p_out": p})
    out = pd.DataFrame(rows)
    out["significant_out"] = out["p_out"] < ALPHA / len(out)
    print(f"\n3. Out of sample with causal filters (Bonferroni over {len(out)} candidates)")
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
