"""Fetch and clean historical price data.

Downloads are cached to disk so every result in the portfolio is reproducible
from the same raw data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"


def fetch_prices(
    tickers: list[str],
    start: str,
    end: str | None = None,
    cache_dir: Path = CACHE_DIR,
    refresh: bool = False,
) -> pd.DataFrame:
    """Daily split- and dividend-adjusted close prices, one column per ticker.

    The raw download is cached as CSV; pass ``refresh=True`` to re-download.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = f"{'_'.join(sorted(tickers))}_{start}_{end or 'latest'}.csv"
    path = cache_dir / key
    if path.exists() and not refresh:
        return pd.read_csv(path, index_col=0, parse_dates=True)

    import yfinance as yf  # imported lazily so tests run without network access

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"]
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(tickers[0])
    prices = prices.reindex(columns=sorted(tickers)).dropna(how="all")
    if prices.empty:
        raise RuntimeError(f"No price data downloaded for {tickers}; check the tickers and your connection")
    prices.to_csv(path)
    return prices


def clean_prices(
    prices: pd.DataFrame,
    max_gap: int = 5,
    min_coverage: float = 0.95,
    jump_threshold: float = 0.30,
) -> tuple[pd.DataFrame, dict]:
    """Clean a price panel and report what was changed.

    - Drops tickers with less than ``min_coverage`` of days observed.
    - Forward-fills gaps of at most ``max_gap`` days (never backward-fills,
      which would leak future prices into the past).
    - Drops rows that are still incomplete.
    - Flags (but keeps) one-day moves larger than ``jump_threshold`` so they
      can be inspected by hand.
    """
    prices = prices.sort_index()
    prices = prices[~prices.index.duplicated(keep="first")]

    coverage = prices.notna().mean()
    dropped = coverage[coverage < min_coverage].index.tolist()
    prices = prices.drop(columns=dropped)

    filled = prices.ffill(limit=max_gap) if max_gap > 0 else prices
    n_filled = int((filled.notna() & prices.isna()).sum().sum())
    cleaned = filled.dropna(how="any")

    returns = cleaned.pct_change()
    jumps = returns[returns.abs() > jump_threshold].stack().dropna()

    report = {
        "dropped_tickers": dropped,
        "values_forward_filled": n_filled,
        "rows_dropped": len(prices) - len(cleaned),
        "large_jumps": jumps.to_dict(),
    }
    return cleaned, report
