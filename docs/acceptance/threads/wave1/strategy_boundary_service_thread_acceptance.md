# Thread Acceptance: strategy_boundary_service

- Module / prompt: `strategy_boundary_service`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`
- Working directory: `backend/strategy`
- Status: `PASS_WITH_NOTES`

## Why this thread was reworked

- The Wave 1 gate recorded that this module only had schema-level alignment with downstream validation.
- No explicit contract-facing mapping seam was frozen for the fields that later feed registration-time execution semantics.

## What is now evidenced

- `StrategyBoundaryService.evaluate(...)` still only performs template/version/rule boundary triage.
- `BoundaryDecisionResult` now carries `contract_binding_hints` for the Wave 1 contract-facing seam:
  - `trade_intent.position_usd -> investment_intent.plannedEntrySize`
  - `trade_intent.max_slippage_bps -> investment_intent.entryMinOut`
  - `trade_intent.stop_loss_bps -> runtime_exit_policy.stop_loss_bps`
  - `trade_intent.take_profit_bps -> runtime_exit_policy.take_profit_bps`
  - `trade_intent.ttl_seconds -> execution_plan.hard_constraints.ttl_seconds`
- Ownership stays explicit:
  - compiler-derived bindings remain owned by `execution_compiler`
  - runtime-derived exit policy inputs remain owned by `reactive_runtime`

## Invariants preserved

- No RPC truth confirmation was added.
- No execution compilation was added.
- No calldata generation was added.
- Boundary triage still collapses only to `auto_register`, `manual_approval`, or `reject`.

## Verification

- `pytest backend/strategy/tests/test_strategy_boundary_service.py -q`
  - Result: `4 passed`

## Remaining notes

- The hints freeze ownership and field intent, not numeric register-payload conversion.
- Exact quote-to-amount conversion still belongs to the registration-time compiler layer.
