# Implementation Contract: DecisionContextBuilder

## Module ID
`decision_context_builder`

## Working Directory
`backend/data`

## Primary Knowledge File
- `docs/knowledge/02_decision/02_context_builder.md`

## Scope
本模块只负责以下职责：
- 统一输出完整 DecisionContext
- Provider 失败时抛明确异常而非吞异常
- 可替换/扩展数据源而不污染上层接口

## Inputs
- `strategy constraints`
- `provider snapshots`

## Outputs
- `DecisionContext`

## Canonical Files To Touch
- `backend/data/context_builder/`
- `backend/data/fetchers/`

## Must Read Before Coding
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/07_data/01_provider_architecture.md`
- `docs/knowledge/07_data/02_source_of_truth_rules.md`

## Hard Invariants
- 以趋势/资金流/风险环境为主，不喂 tick 级噪声
- 执行真相不在本模块产生
- 统一屏蔽 provider 差异

## Non-goals
- 链上执行
- 最终风控裁决
- Schema 外推

## Definition of Done
- 统一输出完整 DecisionContext
- Provider 失败时抛明确异常而非吞异常
- 可替换/扩展数据源而不污染上层接口

## Minimum Verification
- context 完整性测试
- provider fallback 测试
- 缺数据 / 延迟异常测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
