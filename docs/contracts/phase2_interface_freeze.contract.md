# Phase2 Interface Freeze Contract

## Module Purpose

Freeze the interfaces required for Phase2 parallel development before implementation lanes start. W0 exists to prevent agents from independently inventing schemas, ABI fields, events, fixtures, or error names.

## Phase2 Scope

This contract covers W0 only:

- Pydantic truth models
- Solidity interface and event surface
- execution persistence shape
- CLI command skeleton
- fixtures
- error taxonomy
- feature flags

## Out of Scope

- production execution behavior
- complete Approval Flow
- Shadow Monitor daemon
- Aave Protection
- Uniswap V3
- cross-chain execution
- webhook alerts

## Required Pydantic Models

- `StrategyTemplate`
- `TradeIntent`
- `ValidationResult`
- `PreRegistrationCheckResult`
- `ExecutionPlan`
- `InvestmentIntentPayload`
- `ExecutionRecord`
- `FeatureFlags`

All models must be Pydantic v2 models and must be able to export JSON Schema.

## Required Solidity Surface

The Phase2 contract surface must include:

- `registerInvestmentIntent(InvestmentIntent calldata intent) returns (uint256 intentId)`
- `executeReactiveTrigger(uint256 intentId)`
- `emergencyForceClose(uint256 intentId, uint256 maxSlippageBps)`
- `IntentState`: `PendingEntry`, `ActivePosition`, `Closed`, `Cancelled`, `Expired`
- `CloseReason`: `None`, `TakeProfit`, `StopLoss`, `EmergencyForceClose`, `Cancelled`, `Expired`

## Required Events

- `IntentRegistered(uint256 indexed intentId, address indexed owner)`
- `EntryExecuted(uint256 indexed intentId, uint256 amountIn, uint256 amountOut)`
- `ExitExecuted(uint256 indexed intentId, uint256 positionSize, uint256 amountOut, CloseReason reason)`
- `IntentExpired(uint256 indexed intentId)`
- `IntentCancelled(uint256 indexed intentId)`
- `EmergencyForceClosed(uint256 indexed intentId, uint256 amountOut)`
- `TriggerSkipped(uint256 indexed intentId, string reason)`

## Required Fixtures

- `happy_path_strategy_template.json`
- `happy_path_trade_intent.json`
- `happy_path_execution_plan.json`
- `happy_path_execution_record_pending.json`
- `happy_path_execution_record_active.json`
- `happy_path_execution_record_closed.json`
- `rejected_crosschain_intent.json`
- `rejected_uniswap_v3_intent.json`
- `rejected_approval_required_intent.json`

## Error Taxonomy

- `ValidationError`
- `UnsupportedFeatureError`
- `ApprovalRequiredError`
- `InsufficientBalanceError`
- `InsufficientAllowanceError`
- `ExpiredIntentError`
- `GasTooHighError`
- `GasToProfitTooHighError`
- `SlippageTooHighError`
- `UnsupportedPairError`
- `UnsupportedDexError`
- `ContractStateError`
- `EventSyncError`

## Forbidden Behavior

- Do not introduce a second Phase2 schema family outside the frozen models.
- Do not let Solidity fields drift from `InvestmentIntentPayload`.
- Do not add cross-chain, Aave, Uniswap V3, or approval queue behavior to the main path.
- Do not allow disabled features to silently fall through.

## Tests

W0 must prove:

- Pydantic models export JSON Schema.
- fixtures load and validate.
- Solidity interface or contract build target compiles.
- disabled features default to disabled.
- CLI skeleton commands exist or are explicitly stubbed.

## Acceptance Criteria

- W0 Wave Gate is satisfied.
- downstream Waves can depend on the frozen schema, ABI, events, fixtures, and errors.
- any later interface change requires a documented interface change request.
