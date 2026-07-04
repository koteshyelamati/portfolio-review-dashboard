"""Data access layer for the dashboard.

In production the NAV history is read from S3 (``PORTFOLIO_DATA_BUCKET``);
locally, a deterministic synthetic dataset is generated so the app runs
without any AWS credentials. The S3 path keeps the same CSV schema, so the
rest of the app does not care where the data came from.
"""

from __future__ import annotations

import io
import os

import numpy as np
import pandas as pd

DATA_BUCKET_ENV = "PORTFOLIO_DATA_BUCKET"
NAV_KEY = "funds/nav.csv"

FUND_PROFILES = {
    "Global Equity Fund": {"annual_return": 0.09, "annual_vol": 0.17},
    "US Core Bond Fund": {"annual_return": 0.035, "annual_vol": 0.05},
    "Emerging Markets Fund": {"annual_return": 0.10, "annual_vol": 0.24},
    "Real Assets Fund": {"annual_return": 0.06, "annual_vol": 0.13},
    "Short-Term Reserves": {"annual_return": 0.02, "annual_vol": 0.01},
}

TARGET_ALLOCATION = {
    "Equity": 0.55,
    "Fixed Income": 0.30,
    "Real Assets": 0.10,
    "Cash": 0.05,
}

CURRENT_ALLOCATION = {
    "Equity": 0.61,
    "Fixed Income": 0.26,
    "Real Assets": 0.09,
    "Cash": 0.04,
}

ADVISORS = [
    {"advisor": "Meridian Capital", "funds": 2, "aum_musd": 840, "rating": "Strong"},
    {"advisor": "Northbridge Advisors", "funds": 1, "aum_musd": 310, "rating": "Watch"},
    {"advisor": "Halstead & Rowe", "funds": 2, "aum_musd": 525, "rating": "Strong"},
]


def generate_synthetic_navs(
    n_years: int = 3, seed: int = 42, end: str = "2026-06-30"
) -> pd.DataFrame:
    """Deterministic geometric-Brownian NAV history for the demo funds.

    Returns a long-format frame with columns ``date``, ``fund``, ``nav``.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=end, periods=n_years * 252)
    frames = []
    for fund, profile in FUND_PROFILES.items():
        mu = profile["annual_return"] / 252
        sigma = profile["annual_vol"] / np.sqrt(252)
        shocks = rng.normal(loc=mu, scale=sigma, size=len(dates))
        nav = 100 * np.exp(np.cumsum(shocks))
        frames.append(pd.DataFrame({"date": dates, "fund": fund, "nav": nav}))
    return pd.concat(frames, ignore_index=True)


def _load_navs_from_s3(bucket: str) -> pd.DataFrame:
    import boto3

    s3 = boto3.client("s3")
    body = s3.get_object(Bucket=bucket, Key=NAV_KEY)["Body"].read()
    frame = pd.read_csv(io.BytesIO(body), parse_dates=["date"])
    expected = {"date", "fund", "nav"}
    missing = expected - set(frame.columns)
    if missing:
        raise ValueError(
            f"NAV data in s3://{bucket}/{NAV_KEY} is missing columns: {sorted(missing)}"
        )
    return frame


def load_navs() -> pd.DataFrame:
    """Load NAV history from S3 when configured, otherwise synthesize it."""
    bucket = os.environ.get(DATA_BUCKET_ENV)
    if bucket:
        return _load_navs_from_s3(bucket)
    return generate_synthetic_navs()


def nav_series(navs: pd.DataFrame, fund: str) -> pd.Series:
    """NAV history for one fund as a date-indexed Series."""
    subset = navs[navs["fund"] == fund].sort_values("date")
    return subset.set_index("date")["nav"]
