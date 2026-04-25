# Phase2 PreRegistrationCheck Prompt

## Read First

1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. `docs/knowledge/03_strategy_validation/03_pre_registration_check.md`
4. `docs/knowledge/07_data/02_source_of_truth_rules.md`
5. `docs/contracts/phase2_interface_freeze.contract.md`
6. `docs/contracts/phase2_core_execution_loop.contract.md`
7. `docs/contracts/phase2_disabled_features.contract.md`
8. `docs/contracts/phase2_price_oracle_adapter.contract.md`
9. `docs/contracts/pre_registration_check.contract.md`
10. `docs/acceptance/waves/P2_W1.wave_gate.md`
11. `scaffold/backend/validation/AGENTS.md`
12. `scaffold/backend/execution/AGENTS.md`

## Goal

Implement only W1 offline PreRegistrationCheck behavior using deterministic fixture/stub results. Real RPC checks belong to W3.

## Allowed Paths

- `backend/validation/**`
- `backend/execution/**/pre*`
- `backend/**/schemas/**`
- `tests/phase2/w1/**`
- `fixtures/**`
- `docs/acceptance/threads/phase2_wave1/**`

Prefer the repository's existing precheck path if present.

## Forbidden Paths

- live RPC provider implementation
- `backend/contracts/**`
- `backend/reactive/**`
- `backend/monitor/**`
- transaction sender paths
- event syncer paths
- secret or environment files

## Must Not Implement

- live RPC calls in W1
- runtime contract checks
- trigger-time decisions
- tx sending
- calldata generation
- approval queue
- Shadow Monitor daemon
- Uniswap V3 / Aave / cross-chain support

## Inputs

- `TradeIntent`
- `ValidationResult`
- `PreRegistrationCheckResult` fixture/stub input
- fixture balance / allowance / TTL / gas / reserve / slippage / gas-profit values

## Outputs

- deterministic `PreRegistrationCheckResult`
- explicit domain errors for failing fixture cases

## Required Errors

- `InsufficientBalanceError`
- `InsufficientAllowanceError`
- `ExpiredIntentError`
- `GasTooHighError`
- `GasToProfitTooHighError`
- `ReserveUnavailableError`
- `SlippageTooHighError`
- `UnsupportedFeatureError`

## Required Tests

- happy-path fixture returns allow.
- balance insufficient fixture rejects.
- allowance insufficient fixture rejects.
- TTL expired fixture rejects.
- gas too high fixture rejects.
- reserve unavailable fixture rejects.
- slippage too high fixture rejects.
- gas/profit too high fixture rejects.
- W1 implementation does not access live RPC.

## Smoke Command

```powershell
pytest tests/phase2/w1/test_pre_registration_check.py
```

If this path does not exist yet, create the smallest focused W1 test path or record the repository's equivalent command in test evidence.

## Delivery Evidence

- `docs/acceptance/threads/phase2_wave1/pre_registration_check.delivery_note.md`
- `docs/acceptance/threads/phase2_wave1/pre_registration_check.test_evidence.md`
- `docs/acceptance/threads/phase2_wave1/pre_registration_check.thread_acceptance.md`

## Acceptance Criteria

- W1 precheck is deterministic and fixture-driven.
- no live RPC is required in W1.
- output can feed ExecutionCompiler and W1 offline smoke task.
