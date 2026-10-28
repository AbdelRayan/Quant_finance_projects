import pandas as pd

from strategy import ma_crossover


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
