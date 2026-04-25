# Phase2 Core Execution Loop Contract

## Module Purpose

Define the only Phase2 success path. Phase2 is complete only when the single-chain Core Execution Loop closes from `TradeIntent` to exported execution evidence.

## Phase2 Scope

Phase2 supports:

- single-chain execution
- long-only intent
- Uniswap V2-compatible router and pair
- register-time `tokenIn` custody
- `tokenIn -> tokenOut` entry
- `tokenOut -> tokenIn` stop-loss / take-profit exit
- LocalExecutor first
- ReactiveExecutorAdapter v1 as callback adapter
- SQLite or fixture-first persistence
- JSON / Audit Markdown / Investment Memo export

## Out of Scope

- multi-chain and cross-chain execution
- Uniswap V3 execution
- Aave Protection
- complete approval queue
- Shadow Monitor daemon
- webhook alerts
- production multi-user deployment

## Required Flow

```text
TradeIntent
-> Validation
-> PreRegistrationCheck
-> ExecutionCompiler
-> registerInvestmentIntent
-> tokenIn custody
-> PendingEntry
-> executeReactiveTrigger
-> entry swap
-> ActivePosition
-> executeReactiveTrigger
-> stop-loss / take-profit exit swap
-> Closed
-> EventSyncer
-> ExecutionRecord
-> JSON / Audit Markdown / Investment Memo export
```

## Required Behavior

- Validation rejects unsupported pair, side, slippage, size, cross-chain, and disabled DEX paths before precheck.
- `requires_manual_approval == true` raises `ApprovalRequiredError` in Phase2 and does not enter registration.
- PreRegistrationCheck uses RPC truth for balance, allowance, gas, reserves, TTL, slippage, and gas/profit checks.
- ExecutionCompiler compiles at registration time only.
- The contract takes custody of `tokenIn` during `registerInvestmentIntent`.
- Entry moves state from `PendingEntry` to `ActivePosition`.
- Exit moves state from `ActivePosition` to `Closed`.
- `Closed` intents cannot execute again.
- EventSyncer reconstructs `ExecutionRecord` from contract events.
- Audit Markdown only excerpts Machine Truth fields.
- Investment Memo never mutates execution parameters.

## Failure Modes

- unsupported feature: `UnsupportedFeatureError`
- approval needed: `ApprovalRequiredError`
- precheck failure: domain-specific precheck error
- invalid contract state: revert or `ContractStateError`
- event sync failure: `EventSyncError`

## Forbidden Behavior

- trigger-time recompilation
- AI-generated final calldata
- AI signing or fund custody
- indexer data as execution truth
- cross-chain registration
- Uniswap V3 registration
- half-implemented disabled features entering the main path

## Tests

Required evidence must cover:

- W1 fixture dry-run
- W2 local chain/mock DEX loop
- W3 fork/testnet E2E loop
- W4 Reactive/hardening/export closure

## Acceptance Criteria

- All P2_W0 through P2_W4 Wave Gates pass.
- Phase2 Go/No-Go result is `GO`.
- Every execution record can be traced to structured JSON and chain events.
