# Implementation Contract: Shadow Monitor

## Module ID
`shadow_monitor`

## Working Directory
`backend/monitor`

## Primary Knowledge File
- `docs/knowledge/06_cli_ops/02_shadow_monitor.md`

## Scope
本模块只负责以下职责：
- 能发现该死却没死的持仓
- 能输出高危警报与额外损失估算

## Inputs
- `ActivePosition intents`
- `backup RPC quotes/state`

## Outputs
- `alerts`
- `force-close recommendation`

## Canonical Files To Touch
- `backend/monitor/shadow_monitor.py`
- `backend/monitor/reconciliation_daemon.py`

## Must Read Before Coding
- `docs/knowledge/05_reactive_contracts/03_emergency_force_close.md`
- `docs/knowledge/07_data/02_source_of_truth_rules.md`

## Hard Invariants
- 独立于 Reactive 运行
- 只看不摸，除非报警
- 使用备用 RPC 对账
- 有 Grace Period，避免与正常回调竞争

## Non-goals
- 正常执行链路
- 日常决策

## Definition of Done
- 能发现该死却没死的持仓
- 能输出高危警报与额外损失估算

## Minimum Verification
- Grace Period 测试
- 延迟告警测试
- 状态已关闭不重复报警测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
