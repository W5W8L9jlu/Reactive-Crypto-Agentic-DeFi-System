# Phase2 Disabled Features Prompt

## Read First

1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
3. `docs/contracts/phase2_interface_freeze.contract.md`
4. `docs/contracts/phase2_core_execution_loop.contract.md`
5. `docs/contracts/phase2_disabled_features.contract.md`
6. `docs/acceptance/waves/P2_W1.wave_gate.md`
7. relevant `scaffold/backend/*/AGENTS.md`

## Goal

Implement only W1 offline disabled-feature behavior so unsupported Phase3/Phase4 capabilities fail fast before registration.

## Allowed Paths

- `backend/**/feature*`
- `backend/**/errors*`
- `backend/**/schemas*`
- `backend/validation/**`
- `tests/phase2/w1/**`
- `fixtures/**`
- `docs/acceptance/threads/phase2_wave1/**`

Use narrower paths if the repository already has exact modules for feature flags or domain errors.

## Forbidden Paths

- `backend/contracts/**`
- `backend/reactive/**`
- `backend/monitor/**`
- production deployment config
- secret or environment files
- Phase3/Phase4 implementation paths

## Must Not Implement

- complete Approval Flow queue
- Shadow Monitor daemon
- Aave Protection
- Uniswap V3 execution
- Hyperlane / cross-chain execution
- webhook alerts
- Postgres / Redis

## Inputs

- `FeatureFlags`
- `TradeIntent`
- disabled feature fixtures:
  - `rejected_crosschain_intent.json`
  - `rejected_uniswap_v3_intent.json`
  - `rejected_approval_required_intent.json`

## Outputs

- clear domain error for each disabled feature
- deterministic failure result usable by W1 offline smoke

## Required Errors

- `UnsupportedFeatureError`
- `ApprovalRequiredError`
- `UnsupportedDexError`

## Required Tests

- `crosschain=true` fails before registration.
- `dex=uniswap_v3` fails before registration.
- `requires_manual_approval=true` raises `ApprovalRequiredError`.
- disabled features do not reach ExecutionCompiler.
- disabled features do not emit registration payloads.

## Smoke Command

```powershell
pytest tests/phase2/w1/test_disabled_features.py
```

If this path does not exist yet, create the smallest focused W1 test path or record the repository's equivalent command in test evidence.

## Delivery Evidence

- `docs/acceptance/threads/phase2_wave1/disabled_features.delivery_note.md`
- `docs/acceptance/threads/phase2_wave1/disabled_features.test_evidence.md`
- `docs/acceptance/threads/phase2_wave1/disabled_features.thread_acceptance.md`

## Acceptance Criteria

- disabled features fail fast with explicit errors.
- no disabled feature silently falls through.
- no Phase3/Phase4 feature enters the W1 offline Core Loop.
