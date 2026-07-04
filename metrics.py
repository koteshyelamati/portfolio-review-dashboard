"""Performance and allocation metrics for fund analysis.

All functions operate on pandas Series/DataFrames indexed by date and are
kept pure so they can be unit-tested and reused outside the dashboard.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def daily_returns(nav: pd.Series) -> pd.Series:
    """Simple daily returns from a NAV series."""
    return nav.pct_change().dropna()


def cumulative_returns(nav: pd.Series) -> pd.Series:
    """Growth of 1 unit invested at the start of the series."""
    returns = daily_returns(nav)
    return (1 + returns).cumprod()


def cagr(nav: pd.Series) -> float:
    """Compound annual growth rate based on first/last NAV and elapsed days."""
    if len(nav) < 2:
        return float("nan")
    n_days = (nav.index[-1] - nav.index[0]).days
    if n_days <= 0:
        return float("nan")
    total_growth = nav.iloc[-1] / nav.iloc[0]
    return float(total_growth ** (365.25 / n_days) - 1)


def annualized_volatility(nav: pd.Series) -> float:
    """Annualized standard deviation of daily returns."""
    returns = daily_returns(nav)
    if returns.empty:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(nav: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio from daily returns.

    ``risk_free_rate`` is an annual rate, converted to a daily rate assuming
    252 trading days.
    """
    returns = daily_returns(nav)
    if returns.empty:
        return float("nan")
    daily_rf = (1 + risk_free_rate) ** (1 / TRADING_DAYS_PER_YEAR) - 1
    excess = returns - daily_rf
    std = excess.std(ddof=1)
    if std == 0 or np.isnan(std):
        return float("nan")
    return float(excess.mean() / std * np.sqrt(TRADING_DAYS_PER_YEAR))


def max_drawdown(nav: pd.Series) -> float:
    """Largest peak-to-trough decline, as a negative fraction."""
    if nav.empty:
        return float("nan")
    running_max = nav.cummax()
    drawdowns = nav / running_max - 1
    return float(drawdowns.min())


def allocation_drift(
    target: dict[str, float], current: dict[str, float]
) -> pd.DataFrame:
    """Compare current asset-class weights against targets.

    Returns a DataFrame with target, current and drift (current - target)
    per asset class, including classes present in only one of the inputs.
    """
    classes = sorted(set(target) | set(current))
    rows = [
        {
            "asset_class": cls,
            "target": target.get(cls, 0.0),
            "current": current.get(cls, 0.0),
        }
        for cls in classes
    ]
    frame = pd.DataFrame(rows)
    frame["drift"] = frame["current"] - frame["target"]
    return frame
