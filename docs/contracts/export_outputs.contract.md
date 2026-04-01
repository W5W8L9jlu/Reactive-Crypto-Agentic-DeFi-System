# Implementation Contract: Export Outputs

## Module ID
`export_outputs`

## Working Directory
`backend/export`

## Primary Knowledge File
- `docs/knowledge/08_delivery/01_export_outputs.md`

## Scope
本模块只负责以下职责：
- 三轨输出边界清晰
- Audit 与 JSON 字段 1:1 可追溯

## Inputs
- `DecisionArtifact`
- `ExecutionRecord`

## Outputs
- `Machine Truth JSON`
- `Audit Markdown`
- `Investment Memo`

## Canonical Files To Touch
- `backend/export/`

## Must Read Before Coding
- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`

## Hard Invariants
- 执行 = JSON 真相
- 审计 = 摘抄
- 报告 = 生成
- Audit Markdown 不得改写结论

## Non-goals
- 执行
- 策略判断
- 审批逻辑

## Definition of Done
- 三轨输出边界清晰
- Audit 与 JSON 字段 1:1 可追溯

## Minimum Verification
- JSON/Audit 一致性测试
- Memo 不污染 machine truth 测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
