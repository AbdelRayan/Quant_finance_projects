import numpy as np
import pandas as pd

from qfp.backtest import buy_and_hold, run_backtest


def test_position_is_delayed_one_day(prices):
    signal = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    signal.iloc[10, 0] = 1.0
    result = run_backtest(prices, signal, cost_bps=0)
    asset_ret = prices["A"].pct_change()
    assert result.returns.iloc[10] == 0.0
    assert np.isclose(result.returns.iloc[11], asset_ret.iloc[11])


def test_future_prices_do_not_change_past_returns(prices):
    signal = buy_and_hold(prices)
    base = run_backtest(prices, signal).returns
    shocked = prices.copy()
    shocked.iloc[500:] *= 3.0
    after = run_backtest(shocked, signal).returns
    pd.testing.assert_series_equal(base.iloc[:500], after.iloc[:500])


def test_costs_reduce_returns_by_turnover(prices):
    signal = buy_and_hold(prices)
    free = run_backtest(prices, signal, cost_bps=0)
    costly = run_backtest(prices, signal, cost_bps=10)
    diff = free.returns - costly.returns
    assert np.allclose(diff, free.turnover * 10 / 10_000)

