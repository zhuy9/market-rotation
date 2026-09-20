# Security Policy

## Scope

This is a personal, open-source market-monitoring dashboard. It reads public
market data via `yfinance` and requires no credentials to run.

## Reporting a Vulnerability

If you find a security issue (e.g. a way to inject data, crash the API, or
leak local files through an endpoint), please open a private security
advisory on GitHub ("Security" tab → "Report a vulnerability") rather than a
public issue.

## What this project does NOT store

- No user accounts or authentication.
- No brokerage credentials or API keys are required by default.
- No personal or portfolio data is collected.

## Handling of data

- Market data is cached locally in DuckDB (`backend/data/`), which is
  git-ignored and never committed.
- If an optional provider requiring an API key is added in the future, the
  key must be read from an environment variable and never committed. See
  `.env.example`.
