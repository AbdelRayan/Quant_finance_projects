import numpy as np
import pandas as pd

from qfp.pac import (
    calendar_month_phase,
    causal_filter,
    complex_bandpass_kernel,
    modulation_index,
    period_band,
    phase_and_amplitude,
    surrogate_pvalue,
)

THETA = period_band(20, 60)
GAMMA = period_band(5, 12)


def _coupled_signal(n=3000, coupled=True, seed=1):
    """Synthetic 'returns': a 35-day rhythm plus an 8-day rhythm whose size follows the slow phase."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    slow_phase = 2 * np.pi * t / 35
    slow = np.sin(slow_phase)
    envelope = 1 + 0.9 * np.cos(slow_phase) if coupled else np.ones(n)
    fast = envelope * np.sin(2 * np.pi * t / 8)
    x = slow + fast + 0.3 * rng.standard_normal(n)
    return pd.Series(x, index=pd.bdate_range("2000-01-03", periods=n))


def test_period_band_rejects_periods_below_two_days():
    import pytest

    with pytest.raises(ValueError):
        period_band(1, 4)


def test_filter_recovers_in_band_sine_and_blocks_out_of_band():
    t = np.arange(2000)
    kernel = complex_bandpass_kernel(GAMMA)
    in_band = causal_filter(pd.Series(np.sin(2 * np.pi * t / 8)), kernel).abs().iloc[500:]
    out_band = causal_filter(pd.Series(np.sin(2 * np.pi * t / 40)), kernel).abs().iloc[500:]
    assert abs(in_band.mean() - 0.5) < 0.1  # complex output of a unit sine has amplitude ~0.5
    assert out_band.mean() < 0.05


def test_phase_and_amplitude_do_not_look_ahead():
    x = _coupled_signal()
    base = phase_and_amplitude(x, THETA, GAMMA)
    shocked = x.copy()
    shocked.iloc[2000:] += 50
    after = phase_and_amplitude(shocked, THETA, GAMMA)
    pd.testing.assert_frame_equal(base.iloc[:2000], after.iloc[:2000])


def test_modulation_index_detects_coupling():
    coupled = phase_and_amplitude(_coupled_signal(coupled=True), THETA, GAMMA)
    flat = phase_and_amplitude(_coupled_signal(coupled=False), THETA, GAMMA)
    mi_coupled = modulation_index(coupled["phase"].to_numpy(), coupled["amplitude"].to_numpy())
    mi_flat = modulation_index(flat["phase"].to_numpy(), flat["amplitude"].to_numpy())
    assert mi_coupled > 5 * mi_flat


def test_surrogates_separate_coupled_from_uncoupled():
    coupled = phase_and_amplitude(_coupled_signal(coupled=True), THETA, GAMMA)
    _, p_coupled = surrogate_pvalue(coupled["phase"].to_numpy(), coupled["amplitude"].to_numpy(), n_surrogates=100)
    assert p_coupled < 0.05


def test_calendar_month_phase_runs_from_minus_pi_within_each_month():
    idx = pd.bdate_range("2024-01-01", "2024-03-31")
    phase = calendar_month_phase(idx)
    firsts = phase.groupby(idx.to_period("M")).first()
    assert np.allclose(firsts, -np.pi)
    assert (phase < np.pi).all()
    assert (phase.groupby(idx.to_period("M")).apply(lambda p: p.is_monotonic_increasing)).all()
