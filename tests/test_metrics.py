import numpy as np
import pandas as pd
import pytest

import metrics


def _nav(values, start="2024-01-01"):
    dates = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=dates, dtype=float)


def test_daily_returns_basic():
    nav = _nav([100, 110, 99])
    returns = metrics.daily_returns(nav)
    assert returns.iloc[0] == pytest.approx(0.10)
    assert returns.iloc[1] == pytest.approx(-0.10)


def test_cumulative_returns_growth_of_one():
    nav = _nav([100, 110, 121])
    growth = metrics.cumulative_returns(nav)
    assert growth.iloc[-1] == pytest.approx(1.21)


def test_cagr_doubling_in_one_year():
    dates = pd.to_datetime(["2024-01-01", "2025-01-01"])
    nav = pd.Series([100.0, 200.0], index=dates)
    # Slightly over a 365.25-day year, so just under 100%
    assert metrics.cagr(nav) == pytest.approx(1.0, abs=0.01)


def test_cagr_requires_two_points():
    nav = _nav([100])
    assert np.isnan(metrics.cagr(nav))


def test_annualized_volatility_of_constant_series_is_zero():
    nav = _nav([100] * 30)
    assert metrics.annualized_volatility(nav) == pytest.approx(0.0)


def test_sharpe_ratio_sign():
    rng = np.random.default_rng(0)
    steps = rng.normal(loc=0.001, scale=0.01, size=500)
    nav = _nav(100 * np.exp(np.cumsum(steps)))
    assert metrics.sharpe_ratio(nav) > 0
    # A high risk-free rate should lower the ratio
    assert metrics.sharpe_ratio(nav, risk_free_rate=0.5) < metrics.sharpe_ratio(nav)


def test_max_drawdown_known_value():
    nav = _nav([100, 120, 90, 95, 130])
    # Peak 120 -> trough 90 = -25%
    assert metrics.max_drawdown(nav) == pytest.approx(-0.25)


def test_max_drawdown_monotonic_series_is_zero():
    nav = _nav([100, 101, 102, 103])
    assert metrics.max_drawdown(nav) == pytest.approx(0.0)


def test_allocation_drift_includes_all_classes():
    target = {"Equity": 0.6, "Cash": 0.4}
    current = {"Equity": 0.7, "Bonds": 0.3}
    drift = metrics.allocation_drift(target, current)
    assert set(drift["asset_class"]) == {"Equity", "Cash", "Bonds"}
    equity = drift.set_index("asset_class").loc["Equity"]
    assert equity["drift"] == pytest.approx(0.1)
    cash = drift.set_index("asset_class").loc["Cash"]
    assert cash["drift"] == pytest.approx(-0.4)
