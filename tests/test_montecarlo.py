import numpy as np
import pandas as pd
import pytest

from qfp.montecarlo import kupiec_pof, paths_from_returns, simulate_portfolio_returns, var_es


@pytest.fixture
def daily_returns(prices):
    return prices.pct_change().dropna()


@pytest.mark.parametrize("method", ["normal", "bootstrap", "block"])
def test_shapes_and_reproducibility(daily_returns, method):
    w = np.ones(3) / 3
    a = simulate_portfolio_returns(daily_returns, w, horizon=30, n_paths=200, method=method, seed=1)
    b = simulate_portfolio_returns(daily_returns, w, horizon=30, n_paths=200, method=method, seed=1)
    assert a.shape == (200, 30)
    np.testing.assert_array_equal(a, b)


def test_bootstrap_only_uses_historical_days(daily_returns):
    w = np.array([1.0, 0.0, 0.0])
    sim = simulate_portfolio_returns(daily_returns, w, horizon=50, n_paths=50, method="bootstrap")
    assert np.isin(sim, daily_returns["A"].to_numpy()).all()


def test_block_bootstrap_keeps_consecutive_days(daily_returns):
    w = np.array([1.0, 0.0, 0.0])
    hist = daily_returns["A"].to_numpy()
    sim = simulate_portfolio_returns(daily_returns, w, horizon=10, n_paths=20, method="block", block=10)
    for row in sim:
        start = np.flatnonzero(hist == row[0])[0]
        np.testing.assert_array_equal(row, hist[start:start + 10])


def test_normal_method_matches_mean_and_vol(daily_returns):
    w = np.ones(3) / 3
    port = daily_returns.to_numpy() @ w
    sim = simulate_portfolio_returns(daily_returns, w, horizon=1, n_paths=200_000, method="normal")
    assert abs(sim.std() / port.std() - 1) < 0.02


def test_paths_start_at_start_value():
    paths = paths_from_returns(np.full((4, 5), 0.01), start_value=100)
    assert paths.shape == (4, 6)
    assert np.allclose(paths[:, 0], 100)
    assert np.allclose(paths[:, -1], 100 * 1.01**5)


def test_var_es_on_standard_normal():
    pnl = np.random.default_rng(0).standard_normal(1_000_000)
    var, es = var_es(pnl, 0.99)
    assert abs(var - 2.326) < 0.02
    assert abs(es - 2.665) < 0.02
    assert es > var


def test_kupiec_accepts_correct_rate_and_rejects_bad_one():
    assert kupiec_pof(1000, 10, 0.99) > 0.5
    assert kupiec_pof(1000, 30, 0.99) < 0.001
