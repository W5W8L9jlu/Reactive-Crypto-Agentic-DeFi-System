# CLI Phase-1 Runtime Quickstart

## 1) Environment

Copy `.env.example` to `.env` and fill required values:

- `SEPOLIA_RPC_URL` (or `BASE_SEPOLIA_RPC_URL`)
- `SEPOLIA_PRIVATE_KEY`
- `REACTIVE_INVESTMENT_COMPILER_ADDRESS`

Optional:

- `REACTIVE_CLI_DB_PATH`
- `REACTIVE_INVESTMENT_COMPILER_ARTIFACT`
- `REACTIVE_MAINCHAIN_REQUEST_JSON` (advanced request-file mode)

## 2) Smoke Commands

```bash
python -m backend.cli.entrypoint doctor
python -m backend.cli.entrypoint strategy create
python -m backend.cli.entrypoint strategy list
python -m backend.cli.entrypoint decision dry-run --strategy <strategy_id>
```

With full chain wiring:

```bash
python -m backend.cli.entrypoint decision run --strategy <strategy_id>
python -m backend.cli.entrypoint execution force-close <intent_id>
```

## 3) Phase-1 Regression

```bash
python -m pytest -q backend/cli backend/decision backend/execution
python scripts/run_phase1_regression.py
```
