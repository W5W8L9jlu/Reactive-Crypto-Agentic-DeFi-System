# strategy_boundary_service

Minimal boundary service for:
- StrategyTemplate read + version boundary judgement
- StrategyIntent / TradeIntent triage:
  - `auto_register`
  - `manual_approval`
  - `reject`

## Module boundary

This module only handles template/version/rule boundaries.

Not in scope:
- On-chain state confirmation
- Execution
- Calldata generation
- Execution plan compilation

## Interface

- `StrategyBoundaryService.register_template(template)`
- `StrategyBoundaryService.get_template(template_id, version)`
- `StrategyBoundaryService.get_latest_version(template_id)`
- `StrategyBoundaryService.evaluate(strategy_intent, trade_intent) -> BoundaryDecisionResult`

## Traceability

`BoundaryDecisionResult.trace` contains per-rule decision records:
- `rule_name`
- `decision` (`auto`/`manual`/`reject`)
- `observed`
- `note`

## TODO policy for missing spec

When critical template boundary rules are missing, this module raises domain errors instead of inventing behavior:
- `MissingBoundaryRuleError`
- `TemplateNotFoundError`

This follows the contract requirement: unresolved behavior must be explicit and non-silent.
