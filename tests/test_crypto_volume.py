import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

_path = Path(__file__).resolve().parents[1] / "projects" / "04_torus_volume" / "crypto_volume.py"
_spec = importlib.util.spec_from_file_location("crypto_volume", _path)
cv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cv)


def test_torus_features_wrap_smoothly_at_midnight_and_month_end():
    idx = pd.DatetimeIndex(["2024-01-31 23:45", "2024-02-01 00:00"], tz="UTC")
    f = cv.torus_features(idx, k=2, interactions=True)
    assert np.allclose(f.iloc[0], f.iloc[1], atol=0.2)  # 15 minutes apart, so close but not identical


def test_interactions_add_k_squared_times_four_columns():
    idx = pd.date_range("2024-01-01", periods=10, freq="15min", tz="UTC")
    base = cv.torus_features(idx, k=3, interactions=False)
    full = cv.torus_features(idx, k=3, interactions=True)
    assert full.shape[1] - base.shape[1] == 4 * 3 * 3


def test_slot_average_uses_only_past_days():
    idx = pd.date_range("2024-01-01", periods=96 * 30, freq="15min", tz="UTC")
    y = pd.Series(np.random.default_rng(0).normal(size=len(idx)), index=idx)
    base = cv.slot_average(y, 5)
    shocked = y.copy()
    shocked.iloc[96 * 20:] += 100
    after = cv.slot_average(shocked, 5)
    pd.testing.assert_series_equal(base.iloc[: 96 * 20], after.iloc[: 96 * 20])
    assert base.iloc[: 96 * 5].isna().all()


def test_yesterday_level_uses_previous_day_only():
    idx = pd.date_range("2024-01-01", periods=96 * 3, freq="15min", tz="UTC")
    y = pd.Series(np.repeat([1.0, 2.0, 3.0], 96), index=idx)
    x = cv.add_context(cv.torus_features(idx, 1, False), y)
    assert x["yesterday_level"].iloc[:96].isna().all()
    assert (x["yesterday_level"].iloc[96:192] == 1.0).all()
    assert (x["yesterday_level"].iloc[192:] == 2.0).all()
