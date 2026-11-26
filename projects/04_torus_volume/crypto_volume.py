"""Project 4 on real data: forecast BTC 15-minute trading volume on the torus.

Usage (from the repo root; needs internet the first time):

    python projects/04_torus_volume/crypto_volume.py

Data: Binance public monthly 15-minute klines for BTCUSDT
(https://data.binance.vision, no account or API key), cached in data/cache/binance/.
Target: log of quote volume (USDT traded) per 15-minute bar.

Models, all fitted on 2021-2023 and tested on 2024 to mid-2025:
1. Slot average: mean log volume of the same 15-minute slot over the previous
   20 days. The standard intraday "volume curve" baseline.
2. Torus additive: time-of-day and month-position harmonics (k = 1..K).
3. Torus + interactions: adds day x month harmonic products (your doughnut model).
4. Torus + interactions + day of week + recent level: adds weekday dummies and
   yesterday's mean log volume (volume is persistent).

Every feature at bar t uses only the calendar and volume up to the previous day.
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SYMBOL = "BTCUSDT"
START, END = "2021-01", "2025-06"  # months, inclusive
TEST_START = "2024-01-01"
K_HARMONICS = 3
SLOT_WINDOW = 20  # days
CACHE = Path(__file__).resolve().parents[2] / "data" / "cache" / "binance"
URL = "https://data.binance.vision/data/spot/monthly/klines/{s}/15m/{s}-15m-{m}.zip"
COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
           "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]


def fetch_month(month: str) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{SYMBOL}-15m-{month}.csv"
    if not path.exists():
        with urllib.request.urlopen(URL.format(s=SYMBOL, m=month), timeout=60) as resp:
            raw = resp.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            path.write_bytes(zf.read(zf.namelist()[0]))
    df = pd.read_csv(path, header=None, names=COLUMNS)
    if not np.issubdtype(df["open_time"].dtype, np.number):  # some files ship a header row
        df = df[pd.to_numeric(df["open_time"], errors="coerce").notna()].astype({"open_time": "int64"})
    return df


def load_volume() -> pd.Series:
    months = pd.period_range(START, END, freq="M").strftime("%Y-%m")
    df = pd.concat([fetch_month(m) for m in months], ignore_index=True)
    t = df["open_time"].astype("int64")
    unit = np.where(t > 1e14, "us", "ms")  # Binance switched spot files to microseconds in 2025
    times = pd.to_datetime(np.where(unit == "us", t // 1000, t), unit="ms", utc=True)
    vol = pd.Series(df["quote_volume"].astype(float).to_numpy(), index=times).sort_index()
    vol = vol[~vol.index.duplicated()]
    return np.log(vol[vol > 0])


def torus_features(index: pd.DatetimeIndex, k: int, interactions: bool) -> pd.DataFrame:
    hours = index.hour + index.minute / 60
    day_angle = 2 * np.pi * hours / 24
    month_angle = 2 * np.pi * ((index.day - 1) + hours / 24) / index.days_in_month
    cols = {"const": np.ones(len(index))}
    daily, monthly = {}, {}
    for h in range(1, k + 1):
        daily[f"d_cos{h}"], daily[f"d_sin{h}"] = np.cos(h * day_angle), np.sin(h * day_angle)
        monthly[f"m_cos{h}"], monthly[f"m_sin{h}"] = np.cos(h * month_angle), np.sin(h * month_angle)
    cols.update(daily)
    cols.update(monthly)
    if interactions:
        for dn, dv in daily.items():
            for mn, mv in monthly.items():
                cols[f"{dn}x{mn}"] = dv * mv
    return pd.DataFrame(cols, index=index)


def add_context(features: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    weekday = pd.get_dummies(features.index.dayofweek, prefix="dow", drop_first=True).set_index(features.index)
    daily_mean = y.groupby(y.index.normalize()).mean()
    yesterday = daily_mean.shift(1).reindex(y.index.normalize()).to_numpy()
    return features.join(weekday.astype(float)).assign(yesterday_level=yesterday)


def slot_average(y: pd.Series, window: int) -> pd.Series:
    by_slot = y.groupby([y.index.hour, y.index.minute])
    return by_slot.transform(lambda s: s.shift(1).rolling(window, min_periods=window).mean())


def fit_predict(x: pd.DataFrame, y: pd.Series, train: pd.Series) -> pd.Series:
    ok = x.notna().all(axis=1)
    fit = ok & train
    w = np.linalg.lstsq(x[fit].to_numpy(), y[fit].to_numpy(), rcond=None)[0]
    return pd.Series(np.where(ok, x.fillna(0).to_numpy() @ w, np.nan), index=y.index)


def main() -> None:
    y = load_volume()
    train = pd.Series(y.index < pd.Timestamp(TEST_START, tz="UTC"), index=y.index)
    test = ~train
    print(f"{SYMBOL} 15-min bars: train {train.sum():,} ({y.index[0]:%Y-%m} to 2023-12), test {test.sum():,}")

    preds = {"Slot average (20 d)": slot_average(y, SLOT_WINDOW)}
    for name, inter in [("Torus additive", False), ("Torus + interactions", True)]:
        preds[name] = fit_predict(torus_features(y.index, K_HARMONICS, inter), y, train)
    full = add_context(torus_features(y.index, K_HARMONICS, True), y)
    preds["Torus + inter + weekday + level"] = fit_predict(full, y, train)

    common = test & pd.concat(preds, axis=1).notna().all(axis=1)
    rows = {}
    for name, p in preds.items():
        err = (y - p)[common]
        rows[name] = {"RMSE (log)": np.sqrt((err**2).mean()), "Mean abs % error": (np.exp(err.abs()) - 1).mean()}
    table = pd.DataFrame(rows).T
    print(f"\nTest set ({common.sum():,} bars), errors on log volume\n{table.round(4)}")

    # Plot: average log volume on the time-of-day x month grid, test period, data vs model.
    grid = pd.DataFrame({"y": y, "p": preds["Torus + interactions"]})[test]
    grid["hour"] = grid.index.hour + grid.index.minute / 60
    grid["month_pos"] = np.floor(((grid.index.day - 1) / grid.index.days_in_month) * 20) * 5
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True, layout="constrained")
    for ax, col, title in zip(axes, ["y", "p"], ["Actual (test)", "Torus + interactions"]):
        piv = grid.pivot_table(index="month_pos", columns="hour", values=col, aggfunc="mean")
        mesh = ax.pcolormesh(piv.columns, piv.index, piv.to_numpy(), shading="auto", cmap="viridis")
        ax.set(title=title, xlabel="Time of day (UTC)", xticks=[0, 6, 12, 18, 24])
    axes[0].set_ylabel("Position in month (%)")
    fig.colorbar(mesh, ax=axes, label="Mean log quote volume")
    out = Path(__file__).with_name("crypto_volume.png")
    fig.savefig(out, dpi=140)
    print(f"\nSaved {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out}")


if __name__ == "__main__":
    main()
