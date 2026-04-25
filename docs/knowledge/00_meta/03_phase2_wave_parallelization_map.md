# Phase2 Wave Parallelization Map

## Purpose

This file maps the Phase2 source documents into the repository's existing documentation system. Phase2 does not create a parallel documentation architecture. It reuses the Phase1 skeleton and adds Core Execution Loop deltas, Wave Gates, and agent-ready contracts.

## Source Document Roles

| Source | Role | How to Use |
| --- | --- | --- |
| `prd_final_v11_phase2_core_execution_loop.md` | Boundary source | Defines the Phase2 product boundary: single-chain, long-only, Uniswap V2-compatible, register-time custody, Core Execution Loop. |
| `prd_phase2_lite_agile_v1.md` | Daily development input | Provides Sprint goals, stories, acceptance criteria, DoD, and minimum model/contract expectations. |
| `phase2_wave_development_plan_v1.md` | Delivery cadence | Defines W0-W4, lane ownership, smoke tests, exit criteria, merge policy, and risk handling. |
| `phase2_vibe_coding_development_paradigm_v1.md` | Documentation production rule | Defines how to convert Phase2 requirements into `knowledge -> contracts -> prompts -> scaffold -> acceptance`. |

## Reuse / Update / Create Decisions

| Area | Decision | Notes |
| --- | --- | --- |
| Core invariants | Reuse | AI does not sign, does not generate final calldata, RPC is execution truth, JSON is Machine Truth. |
| Domain models | Update as needed | Phase2 freezes `StrategyTemplate`, `TradeIntent`, `ExecutionPlan`, `ValidationResult`, `PreRegistrationCheckResult`, `ExecutionRecord`, and feature flags. |
| Existing module knowledge | Add Phase2 delta | Existing modules keep their names; add Core Execution Loop scope instead of creating `phase2_knowledge`. |
| Existing module contracts | Add Phase2 contract sections | Validation, precheck, compiler, state machine, execution, and export contracts get Phase2-specific constraints. |
| New Phase2 contracts | Create | Interface freeze, disabled features, price oracle adapter, local executor, and event syncer need independent contracts. |
| Prompts | Create Phase2 task prompts after W0 | Prompts must not precede interface freeze. |
| Scaffold AGENTS | Patch only | Update directory guardrails only where Phase2 adds constraints. |
| Acceptance | Create Wave Gates | Phase2 parallel development closes through W0-W4 Wave Gates and thread evidence. |

## Wave Model

```text
W0: Contract Freeze
 -> freeze schemas, ABI, events, DB schema, CLI skeleton, fixtures, errors, feature flags

W1: Offline Core Loop
 -> fixture-only dry-run from TradeIntent through ExecutionPlan and export

W2: Local Chain Mock Loop
 -> local chain/mock DEX state machine from register to Closed

W3: Fork/Testnet E2E Loop
 -> real RPC and Uniswap V2-compatible route with event sync

W4: Reactive + Hardening + Export Closure
 -> ReactiveExecutorAdapter v1, idempotency, domain errors, disabled feature tests, export closure
```

## Lane Model

| Lane | Scope | Primary Contracts |
| --- | --- | --- |
| A: Schema / Validation | Pydantic truth models, template boundary, validation failures | `phase2_interface_freeze`, `validation_engine` |
| B: Compiler / PreCheck | RPC checks and deterministic register payload | `phase2_interface_freeze`, `pre_registration_check`, `execution_compiler` |
| C: Contract / Foundry | Solidity state machine, custody, swaps, oracle adapter | `phase2_interface_freeze`, `phase2_core_execution_loop`, `phase2_price_oracle_adapter` |
| D: Runtime / Event Sync | tx sender, receipt parser, event-to-record sync | `phase2_core_execution_loop`, `phase2_event_syncer` |
| E: CLI / Export | `decision`, `execution`, `export` commands and outputs | `phase2_core_execution_loop`, `export_outputs` |
| F: QA / Fixtures / Docs | fixtures, smoke tests, Wave Gates, acceptance evidence | all Phase2 contracts and gates |

## Dependency Rule

Wave 0 must complete before W1-W4 parallel work starts. After W0, lanes may move in parallel only if they consume the frozen schema, ABI, event, fixture, and error taxonomy instead of inventing local variants.

## Phase2 Non-Goals

These capabilities must not enter the Phase2 main path:

- full Approval Flow queue
- Shadow Monitor daemon
- Aave Protection implementation
- Uniswap V3 execution
- Hyperlane or other cross-chain execution
- webhook alerts
- Postgres / Redis deployment path

They may exist only as disabled feature flags, interfaces, stubs, or fast-fail paths.
