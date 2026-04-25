# Phase2 Wave Plan

## Goal

Phase2 delivers one minimum viable on-chain conditional execution loop:

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
-> ExecutionRecord
-> JSON / Audit Markdown / Investment Memo export
```

Phase2 is single-chain, long-only, Uniswap V2-compatible, and uses register-time `tokenIn` custody.

## Wave 0: Contract Freeze

Freeze the interfaces needed for parallel work:

- Pydantic schemas and JSON Schema export
- Solidity ABI and events
- `ExecutionRecord` / intent mapping persistence shape
- CLI command skeleton
- fixtures
- error taxonomy
- feature flags and disabled feature behavior

Exit condition: all frozen artifacts have a contract and fixture-backed test target.

## Wave 1: Offline Core Loop

Run a fixture-only path without chain access:

```text
fixture TradeIntent -> Validation -> PreRegistrationCheck fixture result -> ExecutionPlan -> export
```

Exit condition: the dry-run fixture smoke passes and JSON/Audit/Memo fields align.

## Wave 2: Local Chain Mock Loop

Run the state machine on local chain or mock DEX:

```text
register -> PendingEntry -> entry swap -> ActivePosition -> exit swap -> Closed
```

Exit condition: local chain smoke proves custody, state transitions, events, and repeat-trigger guards.

## Wave 3: Fork/Testnet E2E Loop

Replace mock chain assumptions with real RPC and Uniswap V2-compatible environment.

Exit condition: fork/testnet smoke proves register, entry, exit, event sync, and ExecutionRecord recovery.

## Wave 4: Reactive + Hardening + Export Closure

Add ReactiveExecutorAdapter v1 and close reliability gaps:

- idempotent event sync
- domain-specific failures
- disabled feature fast-fail tests
- export closure
- handoff evidence

Exit condition: Phase2 DoD passes and every Wave Gate has delivery evidence.

## Merge Rule

No Wave may merge if its smoke test regresses an earlier Wave. Interface changes after W0 require an interface change request and downstream impact note.
