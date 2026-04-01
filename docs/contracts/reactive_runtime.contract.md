# Implementation Contract: Reactive Runtime

## Module ID
`reactive_runtime`

## Working Directory
`backend/reactive`

## Primary Knowledge File
- `docs/knowledge/05_reactive_contracts/01_reactive_runtime.md`

## Scope
本模块只负责以下职责：
- 支持入场/止损/止盈触发
- 与状态机契约对接

## Inputs
- `registered investment intent`
- `reactive trigger`

## Outputs
- `entry/exit callback execution`

## Canonical Files To Touch
- `backend/reactive/adapters/`

## Must Read Before Coding
- `docs/knowledge/05_reactive_contracts/02_investment_state_machine.md`
- `docs/knowledge/04_execution/02_execution_layer.md`

## Hard Invariants
- Reactive 负责事件驱动与 callback，不做自由决策
- 入场与出场都经由状态机
- 保留事件驱动逻辑与 callback 验证

## Non-goals
- 投资建议
- 策略评估
- 链下兜底决策

## Definition of Done
- 支持入场/止损/止盈触发
- 与状态机契约对接

## Minimum Verification
- entry trigger 测试
- stop/take trigger 测试
- callback 验证测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
