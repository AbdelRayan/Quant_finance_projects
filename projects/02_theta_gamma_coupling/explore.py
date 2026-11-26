"""Project 2, step 1: is there any theta-gamma coupling in market returns?

Usage (from the repo root):

    python projects/02_theta_gamma_coupling/explore.py

For each ticker: modulation index of the slow-band phase vs the fast-band
amplitude of daily log returns, with a surrogate p-value, plus the mean
amplitude and mean next-day return in each phase bin. This is exploration,
not a backtest: it tells us whether a strategy is worth building.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qfp.data import clean_prices, fetch_prices
from qfp.pac import calendar_month_phase, period_band, phase_and_amplitude, surrogate_pvalue

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD"]
START = "2005-01-01"
THETA = period_band(20, 60)  # slow cycles, 20-60 trading days
GAMMA = period_band(5, 12)   # fast cycles, 5-12 trading days
N_BINS = 18


def phase_profile(pa: pd.DataFrame, next_return: pd.Series) -> pd.DataFrame:
    bins = np.linspace(-np.pi, np.pi, N_BINS + 1)
    labels = np.degrees((bins[:-1] + bins[1:]) / 2).round().astype(int)
    df = pa.assign(next_return=next_return).dropna()
    df["bin"] = pd.cut(df["phase"], bins, labels=labels, include_lowest=True)
    return df.groupby("bin", observed=False)[["amplitude", "next_return"]].mean()


def main() -> None:
    prices, _ = clean_prices(fetch_prices(TICKERS, start=START))
    returns = np.log(prices).diff().dropna()

    rows, profiles = {}, {}
    for ticker in returns:
        r = returns[ticker]
        pa = phase_and_amplitude(r, THETA, GAMMA)
        mi, p = surrogate_pvalue(pa["phase"].to_numpy(), pa["amplitude"].to_numpy(), n_surrogates=500)
        rows[ticker] = {"MI": mi, "p-value": p}
        profiles[ticker] = phase_profile(pa, r.shift(-1))  # next-day return: exploration only
    print("A. Theta (20-60 d) phase vs gamma (5-12 d) amplitude\n", pd.DataFrame(rows).T.round(5), sep="")

    # Variant B: theta = the calendar month, gamma = the size of each day's move.
    cal_rows, cal_profiles = {}, {}
    month_phase = calendar_month_phase(returns.index)
    for ticker in returns:
        r = returns[ticker]
        pa = pd.DataFrame({"phase": month_phase, "amplitude": r.abs()})
        mi, p = surrogate_pvalue(pa["phase"].to_numpy(), pa["amplitude"].to_numpy(), n_surrogates=500)
        cal_rows[ticker] = {"MI": mi, "p-value": p}
        cal_profiles[ticker] = phase_profile(pa, r)  # same-day return: the phase is known in advance
    print("\nB. Calendar-month phase vs daily |return|\n", pd.DataFrame(cal_rows).T.round(5), sep="")
    print("\nB. Mean daily return (bps) by position in the month (-180 = first day, +180 = last day)")
    print((pd.DataFrame({t: p["next_return"] for t, p in cal_profiles.items()}) * 1e4).round(1))

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ticker, prof in profiles.items():
        (prof["amplitude"] / prof["amplitude"].mean()).plot(ax=axes[0], label=ticker)
        (prof["next_return"] * 1e4).plot(ax=axes[1], label=ticker)
    axes[0].set_ylabel("Gamma amplitude (relative)")
    axes[1].set_ylabel("Next-day return (bps)")
    axes[1].set_xlabel("Theta phase bin (degrees)")
    axes[0].legend(ncol=4)
    fig.tight_layout()
    fig.savefig("projects/02_theta_gamma_coupling/phase_profile.png", dpi=120)
    print("\nSaved projects/02_theta_gamma_coupling/phase_profile.png")


if __name__ == "__main__":
    main()
