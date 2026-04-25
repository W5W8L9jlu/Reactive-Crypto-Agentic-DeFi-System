# Phase2 Execution Compiler Prompt

## Read First

1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. `docs/knowledge/04_execution/01_execution_compiler.md`
4. `docs/knowledge/08_delivery/04_phase2_prd_alignment.md`
5. `docs/contracts/phase2_interface_freeze.contract.md`
6. `docs/contracts/phase2_core_execution_loop.contract.md`
7. `docs/contracts/phase2_disabled_features.contract.md`
8. `docs/contracts/phase2_price_oracle_adapter.contract.md`
9. `docs/contracts/execution_compiler.contract.md`
10. `docs/acceptance/waves/P2_W1.wave_gate.md`
11. `scaffold/backend/execution/AGENTS.md`

## Goal

Implement only W1 offline ExecutionCompiler behavior: deterministic `TradeIntent + template + fixture metadata -> ExecutionPlan`.

## Allowed Paths

- `backend/execution/compiler/**`
- `backend/execution/**/compiler*`
- `backend/**/schemas/**`
- `tests/phase2/w1/**`
- `fixtures/**`
- `docs/acceptance/threads/phase2_wave1/**`

Prefer existing compiler paths if they already exist.

## Forbidden Paths

- `backend/contracts/**`
- `backend/reactive/**`
- `backend/monitor/**`
- transaction sender paths
- event syncer paths
- RPC provider implementation paths
- secret or environment files

## Must Not Implement

- trigger-time recompilation
- runtime swap execution
- tx sending
- receipt parsing
- Reactive callback logic
- Uniswap V3 / Aave / cross-chain support
- LLM-generated calldata

## Inputs

- `TradeIntent`
- `StrategyTemplate`
- `ValidationResult`
- W1 fixture token metadata
- W1 fixture price / quote inputs using `phase2_price_oracle_adapter` semantics

## Outputs

- `ExecutionPlan`
- `InvestmentIntentPayload`

## Required Errors

- `UnsupportedFeatureError`
- `UnsupportedDexError`
- `ValidationError`
- domain error for missing fixture metadata

## Required Tests

- deterministic `ExecutionPlan` from happy-path fixture.
- `amountIn` calculated from NAV and `size_pct_nav`.
- `entryAmountOutMinimum` uses trigger price and slippage, not arbitrary spot fallback.
- `stopLossPriceE18` and `takeProfitPriceE18` are calculated deterministically.
- USDC 6 decimals and WETH 18 decimals fixture passes.
- disabled features do not compile.
- compiler does not access RPC.

## Smoke Command

```powershell
pytest tests/phase2/w1/test_execution_compiler.py
```

If this path does not exist yet, create the smallest focused W1 test path or record the repository's equivalent command in test evidence.

## Delivery Evidence

- `docs/acceptance/threads/phase2_wave1/execution_compiler.delivery_note.md`
- `docs/acceptance/threads/phase2_wave1/execution_compiler.test_evidence.md`
- `docs/acceptance/threads/phase2_wave1/execution_compiler.thread_acceptance.md`

## Acceptance Criteria

- compiler output maps to the frozen `InvestmentIntentPayload`.
- compilation happens only for registration.
- output can feed the W1 offline smoke task.
