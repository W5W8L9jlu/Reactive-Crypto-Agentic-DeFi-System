# Phase2 Event Syncer Contract

## Module Purpose

Define how contract events are converted into `ExecutionRecord` updates. EventSyncer is the bridge between chain truth and local Machine Truth persistence.

## Phase2 Scope

EventSyncer covers:

- contract event decoding
- block cursor tracking
- receipt/event reconciliation
- `local_intent_id <-> onchain_intent_id` mapping
- idempotent `ExecutionRecord` updates
- minimal reorg tolerance for fork/testnet smoke

## Out of Scope

- Shadow Monitor daemon
- cross-chain reconciliation
- indexer-only truth
- alert escalation
- manual force-close operations

## Event Mapping

| Event | ExecutionRecord Update |
| --- | --- |
| `IntentRegistered` | set `onchain_intent_id`, `register_tx_hash`, `state=PendingEntry` |
| `EntryExecuted` | set `entry_tx_hash`, `actual_position_size`, `state=ActivePosition` |
| `ExitExecuted` | set `exit_tx_hash`, `actual_exit_amount`, `close_reason`, `state=Closed` |
| `IntentExpired` | set `state=Expired`, `close_reason=Expired` when applicable |
| `IntentCancelled` | set `state=Cancelled`, `close_reason=Cancelled` when applicable |
| `EmergencyForceClosed` | set `state=Closed`, `close_reason=EmergencyForceClose`, `actual_exit_amount` |
| `TriggerSkipped` | append execution log; do not mutate terminal state |

## Cursor and Idempotency

EventSyncer must track:

- chain id
- contract address
- last scanned block
- transaction hash
- log index

The idempotency key is:

```text
chain_id + contract_address + tx_hash + log_index
```

Reprocessing the same event must not create duplicate records or duplicate state transitions.

## Receipt Parser Boundary

- tx sender/receipt parser captures immediate transaction result and tx hash.
- EventSyncer is responsible for durable event-to-record state.
- receipt parser may provide hints, but EventSyncer is the authoritative local updater for event-derived fields.

## Reorg Tolerance

Phase2 only requires minimal fork/testnet tolerance:

- configurable confirmation depth
- ability to rescan from last safe block
- duplicate-safe event application

Full production reorg policy belongs to later operational hardening.

## Failure Modes

- `EventSyncError`
- missing local intent mapping
- unknown event signature
- unsupported state transition
- RPC log fetch failure

## Forbidden Behavior

- Do not use indexer data as execution truth.
- Do not mutate `ExecutionRecord` without chain event or receipt evidence.
- Do not create duplicate records when replaying events.
- Do not let `TriggerSkipped` overwrite `Closed`, `Cancelled`, or `Expired`.
- Do not hide missing mappings with silent fallback values.

## Tests

Tests must cover:

- each event mapping.
- idempotent replay.
- missing mapping error.
- terminal state protection.
- block cursor advancement.
- rescan from safe block.

## Acceptance Criteria

- W3 can recover `ExecutionRecord` from fork/testnet events.
- W4 can rerun event sync without duplicate mutation.
- Export outputs can trace execution facts to EventSyncer-updated records.
