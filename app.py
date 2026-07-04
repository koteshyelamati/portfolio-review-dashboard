"""Portfolio Review dashboard.

A Dash application for reviewing fund performance, asset-allocation drift
and advisor coverage. Run locally with ``python app.py`` or serve the
``server`` object with gunicorn in a container.
"""

from __future__ import annotations

import dash
import plotly.graph_objects as go
from dash import Input, Output, dash_table, dcc, html

import data_loader
import metrics

NAVS = data_loader.load_navs()
FUNDS = sorted(NAVS["fund"].unique())

app = dash.Dash(__name__, title="Portfolio Review")
server = app.server


def _metric_rows(fund: str) -> list[dict]:
    nav = data_loader.nav_series(NAVS, fund)
    return [
        {"metric": "CAGR", "value": f"{metrics.cagr(nav):.2%}"},
        {
            "metric": "Volatility (ann.)",
            "value": f"{metrics.annualized_volatility(nav):.2%}",
        },
        {"metric": "Sharpe ratio", "value": f"{metrics.sharpe_ratio(nav):.2f}"},
        {"metric": "Max drawdown", "value": f"{metrics.max_drawdown(nav):.2%}"},
    ]


def performance_figure(funds: list[str]) -> go.Figure:
    fig = go.Figure()
    for fund in funds:
        nav = data_loader.nav_series(NAVS, fund)
        growth = metrics.cumulative_returns(nav)
        fig.add_trace(
            go.Scatter(x=growth.index, y=growth.values, name=fund, mode="lines")
        )
    fig.update_layout(
        yaxis_title="Growth of 1.00",
        margin={"l": 40, "r": 20, "t": 30, "b": 40},
        legend={"orientation": "h", "y": -0.15},
    )
    return fig


def allocation_figures() -> tuple[go.Figure, go.Figure]:
    drift = metrics.allocation_drift(
        data_loader.TARGET_ALLOCATION, data_loader.CURRENT_ALLOCATION
    )
    pie = go.Figure(
        go.Pie(labels=drift["asset_class"], values=drift["current"], hole=0.45)
    )
    pie.update_layout(title="Current allocation", margin={"t": 40, "b": 20})
    bars = go.Figure(
        go.Bar(
            x=drift["asset_class"],
            y=drift["drift"],
            marker_color=[
                "#d62728" if d > 0.02 or d < -0.02 else "#1f77b4"
                for d in drift["drift"]
            ],
        )
    )
    bars.update_layout(
        title="Drift vs target (current - target)",
        yaxis_tickformat=".0%",
        margin={"t": 40, "b": 20},
    )
    return pie, bars


pie_fig, drift_fig = allocation_figures()

app.layout = html.Div(
    style={"fontFamily": "system-ui, sans-serif", "margin": "0 2rem"},
    children=[
        html.H1("Portfolio Review"),
        dcc.Tabs(
            [
                dcc.Tab(
                    label="Fund performance",
                    children=[
                        html.Div(
                            style={"margin": "1rem 0"},
                            children=dcc.Dropdown(
                                id="fund-select",
                                options=FUNDS,
                                value=FUNDS[:2],
                                multi=True,
                            ),
                        ),
                        dcc.Graph(id="performance-chart"),
                        html.H3(id="metrics-title"),
                        dash_table.DataTable(
                            id="metrics-table",
                            columns=[
                                {"name": "Metric", "id": "metric"},
                                {"name": "Value", "id": "value"},
                            ],
                            style_cell={"textAlign": "left", "padding": "6px"},
                            style_table={"maxWidth": "420px"},
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Asset allocation",
                    children=html.Div(
                        style={"display": "flex", "flexWrap": "wrap", "gap": "2rem"},
                        children=[
                            dcc.Graph(figure=pie_fig, style={"flex": "1 1 380px"}),
                            dcc.Graph(figure=drift_fig, style={"flex": "1 1 380px"}),
                        ],
                    ),
                ),
                dcc.Tab(
                    label="Advisors",
                    children=dash_table.DataTable(
                        data=data_loader.ADVISORS,
                        columns=[
                            {"name": "Advisor", "id": "advisor"},
                            {"name": "Funds managed", "id": "funds"},
                            {"name": "AUM ($M)", "id": "aum_musd"},
                            {"name": "Review rating", "id": "rating"},
                        ],
                        style_cell={"textAlign": "left", "padding": "6px"},
                        style_table={"maxWidth": "640px", "marginTop": "1rem"},
                    ),
                ),
            ]
        ),
    ],
)


@app.callback(
    Output("performance-chart", "figure"),
    Output("metrics-table", "data"),
    Output("metrics-title", "children"),
    Input("fund-select", "value"),
)
def update_performance(selected: list[str] | str | None):
    if not selected:
        selected = FUNDS[:1]
    if isinstance(selected, str):
        selected = [selected]
    first = selected[0]
    return performance_figure(selected), _metric_rows(first), f"Key metrics: {first}"


if __name__ == "__main__":
    app.run(debug=True)
