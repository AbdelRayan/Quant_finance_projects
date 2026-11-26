"""Phase-amplitude coupling (theta-gamma style) for financial time series.

Everything here is *causal*: the value at date t uses data up to t only, so it
can be used inside a backtest. That rules out the usual EEG tools
(``scipy.signal.filtfilt`` and the FFT-based Hilbert transform), which both
use future samples.

Instead, each band uses one complex FIR filter applied to the past only:
a windowed-sinc low-pass prototype shifted to the band centre. Its output is
an analytic-like signal, so ``np.angle`` gives the phase and ``np.abs`` the
amplitude envelope. Frequencies are in cycles per trading day, so a band of
periods 20-60 days is ``(1/60, 1/20)``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def period_band(short_period: float, long_period: float) -> tuple[float, float]:
    """Convert a band given in periods (trading days) to frequencies (cycles/day)."""
    if not 2 <= short_period < long_period:
        raise ValueError("need 2 <= short_period < long_period (2 days is the Nyquist limit)")
    return 1.0 / long_period, 1.0 / short_period


def complex_bandpass_kernel(band: tuple[float, float], n_cycles: float = 3.0) -> np.ndarray:
    """Causal complex FIR kernel for a band (low, high) in cycles/day.

    The length covers ``n_cycles`` periods of the band's slowest frequency.
    """
    low, high = band
    centre = (low + high) / 2
    half_width = (high - low) / 2
    length = int(np.ceil(n_cycles / low))
    k = np.arange(length)
    m = k - (length - 1) / 2
    lowpass = 2 * half_width * np.sinc(2 * half_width * m) * np.hamming(length)
    kernel = lowpass * np.exp(2j * np.pi * centre * k)
    return kernel / np.abs(np.sum(lowpass))  # unit gain at the band centre


def causal_filter(x: pd.Series, kernel: np.ndarray) -> pd.Series:
    """Apply a FIR kernel to past values only: y[t] = sum_k kernel[k] * x[t - k].

    The first ``len(kernel) - 1`` outputs are NaN (not enough history).
    """
    values = x.to_numpy(dtype=float)
    full = np.convolve(values, kernel, mode="full")[: len(values)]
    full[: len(kernel) - 1] = np.nan
    return pd.Series(full, index=x.index)


def phase_and_amplitude(
    x: pd.Series,
    phase_band: tuple[float, float],
    amp_band: tuple[float, float],
) -> pd.DataFrame:
    """Causal theta-like phase (radians, -pi..pi) and gamma-like amplitude envelope."""
    slow = causal_filter(x, complex_bandpass_kernel(phase_band))
    fast = causal_filter(x, complex_bandpass_kernel(amp_band))
    return pd.DataFrame({"phase": np.angle(slow), "amplitude": np.abs(fast)}, index=x.index)


def calendar_month_phase(index: pd.DatetimeIndex) -> pd.Series:
    """Phase of each trading day within its calendar month, in radians (-pi..pi).

    The first trading day of a month maps to -pi and the last to just below pi,
    so the turn of the month sits at the +/-pi wrap. The calendar is known in
    advance, so this phase has no look-ahead and no filter delay.
    """
    s = index.to_series()
    month = index.to_period("M")
    position = s.groupby(month).cumcount()
    n_days = s.groupby(month).transform("count")
    return pd.Series(-np.pi + 2 * np.pi * position / n_days, index=index)


def modulation_index(phase: np.ndarray, amplitude: np.ndarray, n_bins: int = 18) -> float:
    """Tort et al. (2010) modulation index: 0 = no coupling, 1 = all amplitude in one bin."""
    ok = ~(np.isnan(phase) | np.isnan(amplitude))
    phase, amplitude = phase[ok], amplitude[ok]
    bins = np.linspace(-np.pi, np.pi, n_bins + 1)
    idx = np.clip(np.digitize(phase, bins) - 1, 0, n_bins - 1)
    mean_amp = np.array([amplitude[idx == b].mean() if np.any(idx == b) else 0.0 for b in range(n_bins)])
    p = mean_amp / mean_amp.sum()
    entropy = -np.sum(p[p > 0] * np.log(p[p > 0]))
    return float((np.log(n_bins) - entropy) / np.log(n_bins))


def surrogate_pvalue(
    phase: np.ndarray,
    amplitude: np.ndarray,
    n_surrogates: int = 200,
    min_shift: int = 60,
    n_bins: int = 18,
    seed: int = 0,
) -> tuple[float, float]:
    """Observed MI and its p-value against circularly time-shifted amplitude surrogates.

    Shifting breaks the phase-amplitude timing but keeps each series' own
    statistics, the standard null in the PAC literature.
    """
    ok = ~(np.isnan(phase) | np.isnan(amplitude))
    phase, amplitude = phase[ok], amplitude[ok]
    observed = modulation_index(phase, amplitude, n_bins)
    rng = np.random.default_rng(seed)
    shifts = rng.integers(min_shift, len(amplitude) - min_shift, size=n_surrogates)
    null = np.array([modulation_index(phase, np.roll(amplitude, s), n_bins) for s in shifts])
    return observed, float((1 + np.sum(null >= observed)) / (1 + n_surrogates))
