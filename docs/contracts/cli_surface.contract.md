# Implementation Contract: CLI Surface

## Module ID
`cli_surface`

## Working Directory
`backend/cli`

## Primary Knowledge File
- `docs/knowledge/06_cli_ops/01_cli_surface.md`

## Scope
本模块只负责以下职责：
- strategy/decision/approval/execution/export/monitor 命令面完整
- 视图清晰可追溯

## Inputs
- `user commands`

## Outputs
- `rendered views`
- `command dispatch`

## Canonical Files To Touch
- `backend/cli/`

## Must Read Before Coding
- `docs/knowledge/03_strategy_validation/04_approval_flow.md`
- `docs/knowledge/06_cli_ops/02_shadow_monitor.md`

## Hard Invariants
- CLI 只负责路由/展示/操作入口
- 不承担复杂业务计算
- 继承 CryptoAgents CLI 风格并扩展审批/监控/导出

## Non-goals
- 业务核心计算
- 状态机逻辑
- provider logic

## Definition of Done
- strategy/decision/approval/execution/export/monitor 命令面完整
- 视图清晰可追溯

## Minimum Verification
- 命令路由测试
- 审批显示测试
- alert 视图测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
