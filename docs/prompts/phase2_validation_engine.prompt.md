# Phase2 Validation Engine Prompt

## Read First

1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. `docs/knowledge/03_strategy_validation/02_validation_engine.md`
4. `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
5. `docs/contracts/phase2_interface_freeze.contract.md`
6. `docs/contracts/phase2_core_execution_loop.contract.md`
7. `docs/contracts/phase2_disabled_features.contract.md`
8. `docs/contracts/validation_engine.contract.md`
9. `docs/acceptance/waves/P2_W1.wave_gate.md`
10. `scaffold/backend/validation/AGENTS.md`

## Goal

Implement only W1 offline Validation Engine behavior for Phase2 Core Execution Loop fixtures.

## Allowed Paths

- `backend/validation/**`
- `backend/**/schemas/**`
- `tests/phase2/w1/**`
- `fixtures/**`
- `docs/acceptance/threads/phase2_wave1/**`

Prefer existing validation and schema paths if they already exist.

## Forbidden Paths

- `backend/execution/**` except shared type imports already established by the repo
- `backend/contracts/**`
- `backend/reactive/**`
- `backend/monitor/**`
- RPC provider implementation paths
- secret or environment files

## Must Not Implement

- RPC access
- pool reserve reads
- gas estimation
- calldata generation
- on-chain registration
- approval queue
- Shadow Monitor behavior
- Uniswap V3 / Aave / cross-chain support

## Inputs

- `StrategyTemplate`
- `StrategyIntent`
- `TradeIntent`
- `FeatureFlags`
- W1 fixtures

## Outputs

- `ValidationResult`
- explicit domain error for unsupported or disabled inputs

## Required Errors

- `ValidationError`
- `UnsupportedFeatureError`
- `ApprovalRequiredError`
- `UnsupportedPairError`
- `UnsupportedDexError`

## Required Tests

- valid single-chain long-only Uniswap V2-compatible intent passes.
- `crosschain=true` fails.
- `side != buy` fails.
- `dex != uniswap_v2` fails.
- size over template max fails.
- slippage over template max fails.
- `requires_manual_approval=true` raises `ApprovalRequiredError`.
- Validation Engine does not access RPC.

## Smoke Command

```powershell
pytest tests/phase2/w1/test_validation_engine.py
```

If this path does not exist yet, create the smallest focused W1 test path or record the repository's equivalent command in test evidence.

## Delivery Evidence

- `docs/acceptance/threads/phase2_wave1/validation_engine.delivery_note.md`
- `docs/acceptance/threads/phase2_wave1/validation_engine.test_evidence.md`
- `docs/acceptance/threads/phase2_wave1/validation_engine.thread_acceptance.md`

## Acceptance Criteria

- all W1 validation decisions are deterministic and fixture-driven.
- validation never reads chain state.
- validation output can feed the W1 offline smoke task.
