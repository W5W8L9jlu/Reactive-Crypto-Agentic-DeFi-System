# Phase2 Local Executor Contract

## Module Purpose

Define `LocalExecutorAdapter`, the Phase2 local/fork/testnet trigger adapter used to run the Core Execution Loop before real Reactive integration is available.

## Phase2 Scope

LocalExecutorAdapter is allowed only for:

- local chain smoke tests
- fork smoke tests
- testnet smoke tests
- deterministic debugging of `executeReactiveTrigger(intentId)`

## Out of Scope

- production automation
- free strategy decisions
- direct swaps from Python
- state mutation outside the contract
- bypassing runtime checks
- cross-chain execution

## Public Interface

```python
class LocalExecutorAdapter(Protocol):
    def trigger(self, intent_id: int) -> TxReceipt:
        ...
```

The concrete receipt type should match the repository's runtime/receipt abstraction.

## Required Behavior

- Calls contract `executeReactiveTrigger(intent_id)`.
- Uses the same compiled `ExecutionPlan` / registered on-chain intent as ReactiveExecutorAdapter.
- Does not decide whether a strategy is good.
- Does not modify `InvestmentIntent` state directly.
- Does not call router swap directly.
- Does not bypass contract runtime checks.
- Returns a transaction receipt or domain error.

## State Expectations

- `PendingEntry` with satisfied entry condition may trigger entry.
- `ActivePosition` with satisfied stop-loss or take-profit condition may trigger exit.
- `Closed` must fail or revert on repeat trigger.
- Unsatisfied price conditions must fail, revert, or emit `TriggerSkipped` according to contract behavior.

## Failure Modes

- `ContractStateError`
- `UnsupportedFeatureError`
- transaction revert surfaced as a domain error
- RPC send/receipt error surfaced explicitly

## Forbidden Behavior

- Do not implement Reactive callback logic inside LocalExecutorAdapter.
- Do not call private strategy logic.
- Do not generate calldata using LLM output.
- Do not swallow receipt or revert errors.
- Do not mutate local `ExecutionRecord` without receipt/event evidence.

## Tests

Tests must cover:

- entry trigger from `PendingEntry`.
- exit trigger from `ActivePosition`.
- repeat trigger failure from `Closed`.
- skipped/failed trigger when condition is not satisfied.
- receipt parsing compatible with EventSyncer.

## Acceptance Criteria

- W2 can complete local chain/mock DEX loop using LocalExecutorAdapter.
- W3 can reuse LocalExecutorAdapter for fork/testnet debugging.
- W4 proves ReactiveExecutorAdapter does not invalidate LocalExecutor baseline behavior.
