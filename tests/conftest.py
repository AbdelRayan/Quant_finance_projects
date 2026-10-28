import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "projects" / "01_momentum_backtest"))


@pytest.fixture
def prices() -> pd.DataFrame:
    """Synthetic random-walk prices for three assets over ~3 years."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=800)
    returns = rng.normal(0.0004, 0.01, size=(len(dates), 3))
    return pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=dates, columns=["A", "B", "C"])
