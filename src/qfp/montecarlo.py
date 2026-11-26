"""Monte Carlo simulation of portfolio paths, and Value at Risk / Expected Shortfall.

Three ways to generate future daily returns from history:

- ``normal``: multivariate normal with the historical mean and covariance.
  Simple, but thin tails: it underestimates crashes.
- ``bootstrap``: draw whole historical days (all assets together) at random.
  Keeps fat tails and cross-asset correlation, loses volatility clustering.
- ``block``: draw blocks of consecutive historical days. Also keeps
  volatility clustering (calm and stormy weeks stay together).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

METHODS = ("normal", "bootstrap", "block")


def simulate_portfolio_returns(
    returns: pd.DataFrame,
    weights: np.ndarray,
    horizon: int = 252,
    n_paths: int = 10_000,
    method: str = "bootstrap",
    block: int = 20,
    seed: int = 0,
) -> np.ndarray:
    """Simulated daily portfolio returns, shape (n_paths, horizon).

    ``returns`` are daily simple returns per asset; the portfolio is rebalanced
    to ``weights`` every day.
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    rng = np.random.default_rng(seed)
    r = returns.dropna().to_numpy()
    w = np.asarray(weights, dtype=float)
    n_days = len(r)
    if method == "normal":
        draws = rng.multivariate_normal(r.mean(axis=0), np.cov(r, rowvar=False), size=(n_paths, horizon))
        return draws @ w
    if method == "bootstrap":
        idx = rng.integers(0, n_days, size=(n_paths, horizon))
    else:
        n_blocks = -(-horizon // block)
        starts = rng.integers(0, n_days - block + 1, size=(n_paths, n_blocks))
        idx = (starts[:, :, None] + np.arange(block)).reshape(n_paths, -1)[:, :horizon]
    return r[idx] @ w


def paths_from_returns(sim_returns: np.ndarray, start_value: float = 1.0) -> np.ndarray:
    """Portfolio value paths, shape (n_paths, horizon + 1), starting at ``start_value``."""
    growth = np.cumprod(1 + sim_returns, axis=1)
    return start_value * np.hstack([np.ones((len(sim_returns), 1)), growth])


def var_es(pnl: np.ndarray, level: float = 0.99) -> tuple[float, float]:
    """Value at Risk and Expected Shortfall of a P&L sample, both as positive losses.

    VaR: the loss exceeded with probability 1 - level.
    ES: the average loss in that worst 1 - level tail.
    """
    pnl = np.asarray(pnl, dtype=float)
    cutoff = np.quantile(pnl, 1 - level)
    return float(-cutoff), float(-pnl[pnl <= cutoff].mean())


def kupiec_pof(n_obs: int, n_exceed: int, level: float) -> float:
    """Kupiec proportion-of-failures test p-value: are VaR breaches as rare as promised?"""
    from scipy.stats import chi2

    p = 1 - level
    x, n = n_exceed, n_obs
    if x == 0:
        lr = -2 * n * np.log(1 - p)
    elif x == n:
        lr = -2 * n * np.log(p)
    else:
        phat = x / n
        lr = -2 * ((n - x) * np.log(1 - p) + x * np.log(p) - (n - x) * np.log(1 - phat) - x * np.log(phat))
    return float(1 - chi2.cdf(lr, df=1))
