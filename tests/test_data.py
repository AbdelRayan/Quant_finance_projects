import numpy as np

from qfp.data import clean_prices


def test_clean_fills_short_gaps_only_forward(prices):
    dirty = prices.copy()
    dirty.iloc[100:102, 0] = np.nan
    cleaned, report = clean_prices(dirty)
    assert cleaned.iloc[100, 0] == prices.iloc[99, 0]
    assert report["values_forward_filled"] == 2


def test_clean_drops_sparse_tickers(prices):
    dirty = prices.copy()
    dirty.iloc[::5, 2] = np.nan
    dirty.iloc[1::5, 2] = np.nan
    cleaned, report = clean_prices(dirty, max_gap=0)
    assert "C" not in cleaned.columns
    assert report["dropped_tickers"] == ["C"]


def test_clean_flags_large_jumps(prices):
    dirty = prices.copy()
    dirty.iloc[300:, 1] *= 2
    _, report = clean_prices(dirty)
    assert len(report["large_jumps"]) == 1
