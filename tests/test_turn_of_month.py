import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

# Load Project 2's strategy.py under its own name (Project 1 also has a strategy.py).
_path = Path(__file__).resolve().parents[1] / "projects" / "02_theta_gamma_coupling" / "strategy.py"
_spec = importlib.util.spec_from_file_location("tom_strategy", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
month_position, turn_of_month = _mod.month_position, _mod.turn_of_month


def test_month_position_counts_from_both_ends():
    idx = pd.bdate_range("2024-01-01", "2024-02-29")
    pos = month_position(idx)
    jan = pos.loc["2024-01"]
    assert jan["from_start"].iloc[0] == 0 and jan["from_end"].iloc[-1] == 0
    assert jan["from_start"].iloc[-1] == len(jan) - 1


def test_turn_of_month_earns_exactly_the_window_days(prices):
    weights = turn_of_month(prices, n_last=5, n_first=1)
    held = weights.shift(1).fillna(0).sum(axis=1) > 0  # what the backtester holds each day
    pos = month_position(prices.index)
    expected = (pos["from_end"] < 5) | (pos["from_start"] < 1)
    expected.iloc[0] = False  # nothing can be held on the very first day
    pd.testing.assert_series_equal(held, expected, check_names=False)


def test_turn_of_month_weights_are_equal_and_sum_to_one(prices):
    weights = turn_of_month(prices)
    invested = weights[weights.sum(axis=1) > 0]
    assert np.allclose(invested.sum(axis=1), 1.0)
    assert np.allclose(invested, 1.0 / prices.shape[1])


def test_turn_of_month_ignores_prices(prices):
    shocked = prices * np.random.default_rng(0).uniform(0.5, 1.5, size=prices.shape)
    pd.testing.assert_frame_equal(turn_of_month(prices), turn_of_month(shocked))
