# Implementation Contract: Approval Flow

## Module ID
`approval_flow`

## Working Directory
`backend/cli`

## Primary Knowledge File
- `docs/knowledge/03_strategy_validation/04_approval_flow.md`

## Scope
本模块只负责以下职责：
- approval show 默认展示人话战报
- approval show --raw 能看到机器真相
- approve/reject 路径清晰

## Inputs
- `TradeIntent`
- `ExecutionPlan`
- `ValidationResult`
- `DecisionMeta`

## Outputs
- `ApprovalBattleCard`
- `approve/reject action`

## Canonical Files To Touch
- `backend/cli/views/approval_battle_card.py`
- `backend/cli/approval/`

## Must Read Before Coding
- `docs/knowledge/06_cli_ops/01_cli_surface.md`
- `docs/knowledge/08_delivery/01_export_outputs.md`

## Hard Invariants
- 默认不展示 raw JSON
- 必须显示 TTL 倒计时
- 过期意图禁止审批
- 战报必须由结构化对象映射，不由 LLM 自由生成

## Non-goals
- 机器真相生成
- 执行编译
- 链上执行

## Definition of Done
- approval show 默认展示人话战报
- approval show --raw 能看到机器真相
- approve/reject 路径清晰

## Minimum Verification
- TTL 过期阻止审批
- --raw 与 machine truth 一致
- 数值映射一致性测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
