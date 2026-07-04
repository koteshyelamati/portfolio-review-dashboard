"""Smoke tests: the app imports and its callback returns sane output."""

import app


def test_layout_builds():
    assert app.app.layout is not None
    assert app.FUNDS, "expected at least one fund"


def test_update_performance_callback():
    fig, rows, title = app.update_performance([app.FUNDS[0]])
    assert len(fig.data) == 1
    assert {row["metric"] for row in rows} == {
        "CAGR",
        "Volatility (ann.)",
        "Sharpe ratio",
        "Max drawdown",
    }
    assert app.FUNDS[0] in title


def test_update_performance_handles_empty_selection():
    fig, rows, _ = app.update_performance(None)
    assert len(fig.data) == 1
    assert rows
