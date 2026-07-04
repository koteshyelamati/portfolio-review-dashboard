# Portfolio Review Dashboard

A Python/Dash analytics dashboard for portfolio review teams: fund
performance, asset-allocation drift against targets, and advisor coverage,
in one place. Built to run locally with zero setup and to deploy to AWS with
an S3-backed data layer.

## Features

- **Fund performance** - interactive multi-fund comparison of growth-of-1
  charts with CAGR, annualized volatility, Sharpe ratio and max drawdown
  computed per fund.
- **Asset allocation** - current allocation versus policy targets with a
  drift view that flags asset classes more than 2% off target.
- **Advisor overview** - coverage table for advisor review meetings.
- **Pluggable data layer** - reads NAV history from S3 when
  `PORTFOLIO_DATA_BUCKET` is set; otherwise generates a deterministic
  synthetic dataset so the app runs anywhere.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8050.

## Architecture

```
app.py          Dash UI: tabs, charts, callbacks
metrics.py      Pure metric functions (CAGR, vol, Sharpe, drawdown, drift)
data_loader.py  Data access: S3 (boto3) or synthetic fallback
```

The metric functions are pure and dataframe-in/dataframe-out, so they are
unit-testable and reusable in batch jobs or notebooks outside the dashboard.

### Data contract

`s3://$PORTFOLIO_DATA_BUCKET/funds/nav.csv` with columns `date,fund,nav`.
Malformed files fail fast with a clear error instead of rendering an empty
dashboard.

## Deploying to AWS

The container is stateless, so it fits ECS Fargate or App Runner directly:

```bash
docker build -t portfolio-review .
docker run -p 8050:8050 -e PORTFOLIO_DATA_BUCKET=my-fund-data portfolio-review
```

- Grant the task role `s3:GetObject` on the data bucket only.
- Put the service behind an ALB with health checks on `/`.
- CloudWatch: log the container stdout; alarm on 5xx from the ALB.

## Testing

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
```

S3 access is tested against [moto](https://github.com/getmoto/moto), so the
suite needs no AWS credentials. CI runs lint + tests on Python 3.11 and 3.12
via GitHub Actions.
