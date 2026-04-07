# Thread Handoff: validation_engine

- Upstream thread: `validation_engine`
- Downstream consumer status: `execution_plan seam frozen; compiler layer still pending`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`

## Stable interfaces

- Entry points:
  - `validate_inputs(...)`
  - `validate_inputs_or_raise(...)`
- Stable models:
  - `ExecutionHardConstraints`
  - `ExecutionPlan`
  - `ValidationIssue`
  - `ValidationResult`
  - `ContractBinding`

## Contract bindings emitted on success

| Source field | Target field | Unit |
| --- | --- | --- |
| `strategy_template.template_id` | `strategy_intent.template_id` | `identity` |
| `strategy_template.version` | `strategy_intent.template_version` | `identity` |
| `strategy_template.execution_mode` | `strategy_intent.execution_mode` | `identity` |
| `trade_intent.trade_intent_id` | `execution_plan.trade_intent_id` | `identity` |
| `trade_intent.max_slippage_bps` | `execution_plan.hard_constraints.max_slippage_bps` | `bps` |
| `trade_intent.ttl_seconds` | `execution_plan.hard_constraints.ttl_seconds` | `seconds` |
| `trade_intent.stop_loss_bps` | `execution_plan.hard_constraints.stop_loss_bps` | `bps` |
| `trade_intent.take_profit_bps` | `execution_plan.hard_constraints.take_profit_bps` | `bps` |

## Constraints for downstream work

- Do not reinterpret `contract_bindings` as final contract register payloads.
- Do not add RPC checks in this module.
- Do not add approval rendering or calldata generation here.
- Downstream compiler work must keep `ExecutionPlan.hard_constraints` at least as strict as the validated trade intent.

## Verification source

- `python -m unittest backend.validation.test_validation_engine`
  - Result: `6 tests OK`

## Remaining TODOs

- Final `ExecutionPlan -> InvestmentIntent` register payload mapping remains downstream work.
- Template behavior for empty allowlists remains an explicit documented TODO path.
