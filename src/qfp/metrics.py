"""Performance metrics for daily return series."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def cagr(returns: pd.Series) -> float:
    growth = (1 + returns).prod()
    years = len(returns) / TRADING_DAYS
    return growth ** (1 / years) - 1


def annual_volatility(returns: pd.Series) -> float:
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = returns - risk_free / TRADING_DAYS
    return excess.mean() / excess.std() * np.sqrt(TRADING_DAYS)


def sortino_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = returns - risk_free / TRADING_DAYS
    downside = np.sqrt((np.minimum(excess, 0) ** 2).mean())
    return excess.mean() / downside * np.sqrt(TRADING_DAYS)


def drawdown(returns: pd.Series) -> pd.Series:
    equity = (1 + returns).cumprod()
    return equity / equity.cummax() - 1


def max_drawdown(returns: pd.Series) -> float:
    return drawdown(returns).min()


def summary(returns: pd.Series, turnover: pd.Series | None = None) -> pd.Series:
    """One column of the strategy-vs-benchmark comparison table."""
    stats = {
        "CAGR": cagr(returns),
        "Volatility": annual_volatility(returns),
        "Sharpe": sharpe_ratio(returns),
        "Sortino": sortino_ratio(returns),
        "Max drawdown": max_drawdown(returns),
        "Hit rate": (returns[returns != 0] > 0).mean(),
    }
    if turnover is not None:
        stats["Annual turnover"] = turnover.mean() * TRADING_DAYS
    return pd.Series(stats)
