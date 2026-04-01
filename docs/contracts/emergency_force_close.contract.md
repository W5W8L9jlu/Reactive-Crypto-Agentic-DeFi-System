# Implementation Contract: Emergency Force Close

## Module ID
`emergency_force_close`

## Working Directory
`backend/contracts/core`

## Primary Knowledge File
- `docs/knowledge/05_reactive_contracts/03_emergency_force_close.md`

## Scope
本模块只负责以下职责：
- break-glass 路径可用
- 与 shadow monitor 告警联动

## Inputs
- `intentId`
- `maxSlippageBps`

## Outputs
- `forced close tx`
- `state set to Closed first`

## Canonical Files To Touch
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`

## Must Read Before Coding
- `docs/knowledge/06_cli_ops/02_shadow_monitor.md`
- `docs/knowledge/05_reactive_contracts/02_investment_state_machine.md`

## Hard Invariants
- 仅 owner/authorized relayer 调用
- 仅 ActivePosition 时允许
- 先写 Closed 再紧急卖出
- 后续迟滞回调必须 Revert

## Non-goals
- 日常执行路径
- 替代正常 reactive callback

## Definition of Done
- break-glass 路径可用
- 与 shadow monitor 告警联动

## Minimum Verification
- 权限测试
- 非 ActivePosition 拒绝测试
- force-close 后迟滞回调 revert 测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
