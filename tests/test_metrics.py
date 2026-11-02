import numpy as np
import pandas as pd

from qfp.metrics import annual_volatility, cagr, max_drawdown, sharpe_ratio


def test_cagr_of_constant_return():
    r = pd.Series([0.001] * 252)
    assert np.isclose(cagr(r), 1.001**252 - 1)


def test_volatility_scales_with_sqrt_time():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 100_000))
    assert abs(annual_volatility(r) - 0.01 * np.sqrt(252)) < 0.002


def test_max_drawdown():
    r = pd.Series([0.10, -0.50, 0.20])
    assert np.isclose(max_drawdown(r), -0.50)


def test_sharpe_sign():
    assert sharpe_ratio(pd.Series([0.01, 0.02, 0.0, 0.01])) > 0
