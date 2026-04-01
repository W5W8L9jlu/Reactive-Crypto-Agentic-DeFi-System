# Implementation Contract: Execution Layer

## Module ID
`execution_layer`

## Working Directory
`backend/execution/runtime`

## Primary Knowledge File
- `docs/knowledge/04_execution/02_execution_layer.md`

## Scope
本模块只负责以下职责：
- 能消费 runtime trigger 并记录执行回执
- ExecutionRecord 与链上回执一致

## Inputs
- `compiled execution plan`
- `runtime trigger`
- `on-chain checks passed`

## Outputs
- `ExecutionRecord`
- `tx receipt`

## Canonical Files To Touch
- `backend/execution/runtime/`

## Must Read Before Coding
- `docs/knowledge/05_reactive_contracts/01_reactive_runtime.md`
- `docs/knowledge/07_data/02_source_of_truth_rules.md`

## Hard Invariants
- 不在校验通过后立即 swap
- 只在 Reactive 触发后执行
- 只负责链上调用和回执记录

## Non-goals
- 自由决策
- 重新编译
- 替代状态机

## Definition of Done
- 能消费 runtime trigger 并记录执行回执
- ExecutionRecord 与链上回执一致

## Minimum Verification
- 执行成功回执测试
- 链上失败回执测试
- record/export 一致性测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
