# Phase2 Wave Smoke Tests

## Purpose

Phase2 smoke tests prove vertical increments, not isolated module completion. Each Wave must leave executable evidence in `docs/acceptance/threads/phase2_wave*/`.

## W0: Interface Freeze Smoke

Required checks:

```powershell
python scripts/workflow.py audit-manifest --strict
python scripts/workflow.py check validation_engine --execute --strict
python scripts/workflow.py check execution_compiler --execute --strict
```

Additional implementation checks should cover:

- Pydantic models can export JSON Schema.
- frozen fixtures can be loaded by tests.
- Solidity interface or contract artifacts build.
- disabled feature flags are present and default to disabled.

## W1: Offline Core Loop Smoke

Required path:

```text
fixture TradeIntent
-> ValidationResult allow
-> PreRegistrationCheckResult allow from fixture
-> ExecutionPlan
-> JSON / Audit Markdown / Investment Memo export
```

No RPC access is required in W1.

## W2: Local Chain Mock Loop Smoke

Required path:

```text
registerInvestmentIntent
-> tokenIn custody
-> PendingEntry
-> executeReactiveTrigger entry
-> ActivePosition
-> executeReactiveTrigger stop-loss or take-profit
-> Closed
```

Evidence must include register, entry, exit tx hashes or local receipts, emitted events, and final state.

## W3: Fork/Testnet E2E Smoke

Required path:

```text
real RPC / fork RPC
-> Uniswap V2-compatible reserve and price read
-> register
-> entry
-> exit
-> event sync
-> ExecutionRecord recovery
```

The Graph or indexers may support analysis but cannot replace RPC execution truth.

## W4: Reactive + Hardening Smoke

Required path:

```text
LocalExecutor baseline
-> ReactiveExecutorAdapter v1 trigger path
-> idempotent event sync
-> disabled feature fast-fail
-> final export closure
```

Evidence must include failure-mode tests for unsupported approval queue, shadow daemon, Aave, Uniswap V3, cross-chain, and webhook paths.
