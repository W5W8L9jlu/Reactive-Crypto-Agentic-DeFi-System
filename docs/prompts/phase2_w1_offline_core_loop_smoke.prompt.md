# Phase2 W1 Offline Core Loop Smoke Prompt

## Read First

1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
4. `docs/knowledge/08_delivery/05_phase2_wave_plan.md`
5. `docs/knowledge/09_testing/04_phase2_wave_smoke_tests.md`
6. `docs/contracts/phase2_interface_freeze.contract.md`
7. `docs/contracts/phase2_core_execution_loop.contract.md`
8. `docs/contracts/phase2_disabled_features.contract.md`
9. `docs/acceptance/waves/P2_W1.wave_gate.md`
10. P0 module prompts:
    - `docs/prompts/phase2_disabled_features.prompt.md`
    - `docs/prompts/phase2_validation_engine.prompt.md`
    - `docs/prompts/phase2_execution_compiler.prompt.md`
    - `docs/prompts/phase2_pre_registration_check.prompt.md`

## Goal

Create the W1 offline smoke task that proves a fixture-only Core Execution Loop through validation, precheck stub, compiler, and export shell.

## Required Path

```text
fixture TradeIntent
-> Validation Engine
-> PreRegistrationCheck stub / fixture result
-> Execution Compiler
-> ExecutionPlan
-> Export JSON / Audit Markdown / Memo shell
```

## Allowed Paths

- `tests/phase2/w1/**`
- `fixtures/**`
- existing W1-relevant backend paths required by P0 prompts
- `docs/acceptance/threads/phase2_wave1/**`

## Forbidden Paths

- live RPC paths
- Solidity / contract implementation
- Reactive implementation
- Uniswap live integration
- Aave implementation
- cross-chain implementation
- Shadow Monitor daemon
- Approval Flow queue
- secret or environment files

## Must Not Implement

- W2 local chain behavior
- W3 fork/testnet behavior
- W4 Reactive adapter behavior
- tx sending
- event syncer
- production export formatting beyond W1 shell needs

## Inputs

- happy-path `StrategyTemplate` fixture
- happy-path `TradeIntent` fixture
- happy-path `PreRegistrationCheckResult` fixture
- rejected `crosschain=true` fixture
- rejected `side=sell` fixture
- rejected `dex=uniswap_v3` fixture
- rejected `requires_manual_approval=true` fixture

## Outputs

- deterministic `ExecutionPlan`
- JSON export derived from Machine Truth
- Audit Markdown excerpt shell
- Investment Memo narrative shell
- W1 test evidence

## Required Tests

- legal `TradeIntent` passes.
- `crosschain=true` fails.
- `side=sell` fails.
- `dex=uniswap_v3` fails.
- `requires_manual_approval=true` aborts.
- PreRegistrationCheck stub returns deterministic allow result.
- ExecutionCompiler generates deterministic `ExecutionPlan`.
- JSON export matches `ExecutionPlan`.
- Audit Markdown only excerpts structured fields.
- Memo does not mutate Machine Truth.

## Smoke Command

```powershell
pytest tests/phase2/w1/test_offline_core_loop.py
```

## Delivery Evidence

- `docs/acceptance/threads/phase2_wave1/offline_core_loop_smoke.delivery_note.md`
- `docs/acceptance/threads/phase2_wave1/offline_core_loop_smoke.test_evidence.md`
- `docs/acceptance/threads/phase2_wave1/offline_core_loop_smoke.thread_acceptance.md`

## Acceptance Criteria

- W1 offline smoke can run without RPC, Solidity, Reactive, or Uniswap integration.
- output artifacts are deterministic.
- W1 evidence can be evaluated against `P2_W1.wave_gate.md`.
