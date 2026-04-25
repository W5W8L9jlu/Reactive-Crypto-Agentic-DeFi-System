# Phase2 PRD Alignment

## 目的

将 Phase2 文档统一收敛到 PRD v11 的 Core Execution Loop 边界。若历史 PRD v10、旧 Phase Plan 或旧验收文件与 v11 冲突，以 v11 Phase2 边界为准，并在本文件记录调整。

## Phase2 总边界

Phase2 只交付一个最小可用链上条件执行闭环：

```text
TradeIntent
-> Validation
-> PreRegistrationCheck
-> ExecutionCompiler
-> registerInvestmentIntent
-> PendingEntry
-> ActivePosition
-> Closed
-> ExecutionRecord
-> Export
```

固定约束：

- single-chain only
- long-only only
- Uniswap V2-compatible only
- register-time `tokenIn` custody
- LocalExecutor first, ReactiveExecutorAdapter v1 later
- JSON and chain events are execution truth
- disabled features fail fast

## Source Documents

| Source | Alignment Role |
| --- | --- |
| `prd_final_v11_phase2_core_execution_loop.md` | Phase2 product and safety boundary |
| `prd_phase2_lite_agile_v1.md` | stories, acceptance criteria, DoD |
| `phase2_wave_development_plan_v1.md` | W0-W4 delivery cadence |
| `phase2_vibe_coding_development_paradigm_v1.md` | documentation production workflow |

## PRD 条目映射

| PRD v11 条目 | 仓库落点 | 验收要点 |
| --- | --- | --- |
| Phase2 schemas | `shared/schemas`, `docs/contracts/phase2_interface_freeze.contract.md` | Pydantic v2 models and JSON Schema export |
| Validation Engine v1 | `validation_engine` | template boundary, long-only, single-chain, V2-only, disabled feature rejection |
| PreRegistrationCheck v1 | `pre_registration_check` | RPC truth for balance, allowance, TTL, gas, reserves, slippage, gas/profit |
| Execution Compiler v1 | `execution_compiler` | registration-time payload compilation, no trigger-time recompilation |
| ReactiveInvestmentCompiler v1 | `investment_state_machine_contract` | custody, PendingEntry, ActivePosition, Closed, emergencyForceClose |
| Price Oracle Adapter | `phase2_price_oracle_adapter.contract.md` | E18 price and V2 quote behavior |
| LocalExecutorAdapter | `phase2_local_executor.contract.md` | local/fork/testnet trigger path |
| ReactiveExecutorAdapter v1 | `reactive_runtime` | callback adapter, no free decision |
| Event Syncer | `phase2_event_syncer.contract.md` | events to ExecutionRecord, idempotent sync |
| Export | `export_outputs` | JSON / Audit Markdown / Investment Memo, with Audit as excerpt only |

## Moved Out of Phase2

| Capability | Phase2 Treatment | Target Stage |
| --- | --- | --- |
| complete Approval Flow | `ApprovalRequiredError`, abort registration | Phase 3 |
| Shadow Monitor daemon | keep events and escape hatch only | Phase 3 |
| Aave Protection | disabled feature / adapter skeleton only | Phase 3.5 |
| Uniswap V3 | disabled feature / adapter skeleton only | Phase 3.5 / Phase 4 |
| Hyperlane / cross-chain | disabled feature / interface only | Phase 4 |
| webhook alerts | disabled interface only | Phase 3 optional |
| Postgres / Redis | not in default path | later deployment stage |

## Wave Gate 对齐

- W0 freezes interfaces before parallel development.
- W1 proves offline fixture dry-run.
- W2 proves local chain/mock DEX state machine.
- W3 proves fork/testnet E2E with real RPC and V2-compatible route.
- W4 proves Reactive adapter, hardening, disabled feature failures, and export closure.

## 冲突处理规则

- Phase boundary conflict: PRD v11 wins.
- Implementation conflict: system invariants and module contracts win.
- Wave conflict: W0 frozen interface wins until an interface change request is accepted.
- Evidence conflict: chain events and Machine Truth JSON win over Markdown summaries.
