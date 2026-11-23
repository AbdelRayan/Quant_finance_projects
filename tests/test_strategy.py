import pandas as pd

from strategy import ma_crossover, momentum_12_1


def test_ma_crossover_has_no_position_before_full_window(prices):
    weights = ma_crossover(prices, fast=20, slow=100)
    assert (weights.iloc[:99] == 0).all().all()


def test_ma_crossover_weights_sum_to_at_most_one(prices):
    weights = ma_crossover(prices, fast=20, slow=100)
    assert (weights.sum(axis=1) <= 1 + 1e-12).all()


def test_ma_crossover_does_not_look_ahead(prices):
    base = ma_crossover(prices, fast=20, slow=100)
    shocked = prices.copy()
    shocked.iloc[500:] *= 0.2
    after = ma_crossover(shocked, fast=20, slow=100)
    pd.testing.assert_frame_equal(base.iloc[:500], after.iloc[:500])


def _month_ends(index):
    return set(index.to_series().groupby(index.to_period("M")).max())


def test_momentum_has_no_position_before_full_lookback(prices):
    weights = momentum_12_1(prices, top_n=2, lookback=252, skip=21)
    assert (weights.iloc[:252] == 0).all().all()


def test_momentum_holds_top_n_equal_weights(prices):
    weights = momentum_12_1(prices, top_n=2)
    invested = weights.iloc[300:]
    assert ((invested > 0).sum(axis=1) == 2).all()
    assert ((invested.sum(axis=1) - 1).abs() < 1e-12).all()


def test_momentum_only_changes_on_month_ends(prices):
    weights = momentum_12_1(prices, top_n=2)
    changed = weights.diff().abs().sum(axis=1) > 0
    assert set(weights.index[changed]) <= _month_ends(prices.index)


def test_momentum_picks_the_strongest_asset(prices):
    trending = prices.copy()
    trending["C"] = 100 * 1.003 ** pd.Series(range(len(prices)), index=prices.index, dtype=float)
    weights = momentum_12_1(trending, top_n=1)
    assert (weights["C"].iloc[300:] == 1).all()


def test_momentum_does_not_look_ahead(prices):
    base = momentum_12_1(prices, top_n=2)
    shocked = prices.copy()
    shocked.iloc[500:] *= 0.2
    after = momentum_12_1(shocked, top_n=2)
    pd.testing.assert_frame_equal(base.iloc[:500], after.iloc[:500])
