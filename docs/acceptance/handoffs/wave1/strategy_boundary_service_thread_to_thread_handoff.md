# Thread Handoff: strategy_boundary_service

- Upstream thread: `strategy_boundary_service`
- Downstream consumer status: `validation_engine schema-aligned; execution compiler not implemented in W1`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`

## Stable interfaces

- Service entry points:
  - `register_template(...)`
  - `get_template(...)`
  - `get_latest_version(...)`
  - `evaluate(...)`
- Stable models:
  - `StrategyTemplate`
  - `StrategyIntent`
  - `TradeIntent`
  - `BoundaryDecisionResult`
- Stable enums:
  - `BoundaryDecision`
  - `RuleDecision`

## Contract-facing mapping hints

| Source field | Target field | Binding kind | Unit | Owner |
| --- | --- | --- | --- | --- |
| `trade_intent.position_usd` | `investment_intent.plannedEntrySize` | `compiler_derived` | `usd_notional` | `execution_compiler` |
| `trade_intent.max_slippage_bps` | `investment_intent.entryMinOut` | `compiler_derived` | `bps` | `execution_compiler` |
| `trade_intent.stop_loss_bps` | `runtime_exit_policy.stop_loss_bps` | `runtime_derived` | `bps` | `reactive_runtime` |
| `trade_intent.take_profit_bps` | `runtime_exit_policy.take_profit_bps` | `runtime_derived` | `bps` | `reactive_runtime` |
| `trade_intent.ttl_seconds` | `execution_plan.hard_constraints.ttl_seconds` | `compiler_derived` | `seconds` | `execution_compiler` |

## Constraints for downstream work

- Do not move RPC checks into this module.
- Do not compile register payloads here.
- Do not treat the hints above as final calldata or final on-chain numeric values.
- If a downstream module needs stricter numeric semantics, it must document them explicitly in its own contract before implementation.

## Verification source

- `pytest backend/strategy/tests/test_strategy_boundary_service.py -q`
  - Result: `4 passed`

## Remaining TODOs

- Quote-time conversion from `position_usd` to `plannedEntrySize` remains downstream work.
- Absolute `entryMinOut` / exit floor numeric derivation remains downstream work.
