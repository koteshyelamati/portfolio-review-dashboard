import boto3
import pandas as pd
import pytest
from moto import mock_aws

import data_loader


def test_synthetic_navs_are_deterministic():
    first = data_loader.generate_synthetic_navs()
    second = data_loader.generate_synthetic_navs()
    pd.testing.assert_frame_equal(first, second)
    assert set(first.columns) == {"date", "fund", "nav"}
    assert first["nav"].gt(0).all()


def test_load_navs_falls_back_to_synthetic(monkeypatch):
    monkeypatch.delenv(data_loader.DATA_BUCKET_ENV, raising=False)
    navs = data_loader.load_navs()
    assert sorted(navs["fund"].unique()) == sorted(data_loader.FUND_PROFILES)


@mock_aws
def test_load_navs_reads_from_s3(monkeypatch):
    bucket = "portfolio-data-test"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket)
    csv = "date,fund,nav\n2026-01-02,Test Fund,100.0\n2026-01-05,Test Fund,101.5\n"
    s3.put_object(Bucket=bucket, Key=data_loader.NAV_KEY, Body=csv)
    monkeypatch.setenv(data_loader.DATA_BUCKET_ENV, bucket)

    navs = data_loader.load_navs()

    assert list(navs["fund"].unique()) == ["Test Fund"]
    assert len(navs) == 2
    assert navs["nav"].iloc[-1] == pytest.approx(101.5)


@mock_aws
def test_load_navs_rejects_malformed_csv(monkeypatch):
    bucket = "portfolio-data-test"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket)
    s3.put_object(
        Bucket=bucket, Key=data_loader.NAV_KEY, Body="date,price\n2026-01-02,1\n"
    )
    monkeypatch.setenv(data_loader.DATA_BUCKET_ENV, bucket)

    with pytest.raises(ValueError, match="missing columns"):
        data_loader.load_navs()


def test_nav_series_is_sorted_and_indexed():
    navs = data_loader.generate_synthetic_navs()
    fund = next(iter(data_loader.FUND_PROFILES))
    series = data_loader.nav_series(navs, fund)
    assert series.index.is_monotonic_increasing
    assert series.name == "nav"
