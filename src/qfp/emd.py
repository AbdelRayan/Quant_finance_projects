"""Empirical mode decomposition (EMD) helpers for finding a series' own rhythms.

EMD splits a signal into intrinsic mode functions (IMFs), from fastest to
slowest, without choosing frequency bands in advance.

Two warnings, both important for finance:

1. **EMD is not causal.** Each IMF at time t depends on the whole series,
   including the future (sifting uses envelopes through later extrema). Use it
   only to *discover* periods on in-sample data, then trade with causal
   filters at those periods (``qfp.pac``) out of sample.
2. **EMD on pure noise still returns IMFs**, with periods roughly doubling
   from one IMF to the next (about 3, 6, 12, 24, ... samples; Wu and Huang
   2004). An IMF is only a "rhythm" if it carries more energy than the same
   IMF of shuffled data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import hilbert


def decompose(x: np.ndarray, max_imf: int = -1, seed: int | None = None, ensemble: bool = False) -> np.ndarray:
    """IMFs of ``x`` as rows, fastest first (the residual trend is dropped).

    ``ensemble=True`` uses CEEMDAN, which reduces mode mixing but is ~100x slower.
    """
    from PyEMD import CEEMDAN, EMD

    x = np.asarray(x, dtype=float)
    if ensemble:
        ceemdan = CEEMDAN(trials=50)
        if seed is not None:
            ceemdan.noise_seed(seed)
        imfs = ceemdan(x, max_imf=max_imf)
    else:
        imfs = EMD()(x, max_imf=max_imf)
    return imfs[:-1] if len(imfs) > 1 else imfs


def mean_period(imf: np.ndarray) -> float:
    """Average period in samples, from zero crossings (two per cycle)."""
    crossings = np.sum(np.diff(np.signbit(imf).astype(int)) != 0)
    return float(2 * len(imf) / crossings) if crossings else float("inf")


def imf_table(imfs: np.ndarray) -> pd.DataFrame:
    energy = (imfs**2).sum(axis=1)
    return pd.DataFrame(
        {"period": [mean_period(m) for m in imfs], "energy_share": energy / energy.sum()},
        index=pd.Index(range(1, len(imfs) + 1), name="imf"),
    )


def noise_benchmark(x: np.ndarray, n_shuffles: int = 20, seed: int = 0) -> pd.DataFrame:
    """IMF periods and energy shares of shuffled copies of ``x`` (same values, no timing).

    Returns the mean period and the 95th percentile energy share per IMF index.
    """
    rng = np.random.default_rng(seed)
    tables = [imf_table(decompose(rng.permutation(x))) for _ in range(n_shuffles)]
    joined = pd.concat(tables, keys=range(n_shuffles), names=["run"])
    grouped = joined.groupby("imf")
    return pd.DataFrame({
        "noise_period": grouped["period"].mean(),
        "noise_energy_95": grouped["energy_share"].quantile(0.95),
    })


def hilbert_phase_amplitude(imf: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Instantaneous phase and amplitude of an IMF (non-causal: discovery only)."""
    analytic = hilbert(imf)
    return np.angle(analytic), np.abs(analytic)
