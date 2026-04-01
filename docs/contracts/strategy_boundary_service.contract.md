# Implementation Contract: Strategy Boundary Service

## Module ID
`strategy_boundary_service`

## Working Directory
`backend/strategy`

## Primary Knowledge File
- `docs/knowledge/03_strategy_validation/01_strategy_boundary.md`

## Scope
本模块只负责以下职责：
- 能够根据模板规则分流 auto/manual/reject
- 边界判定结果可追溯

## Inputs
- `StrategyTemplate`
- `StrategyIntent`
- `TradeIntent`

## Outputs
- `boundary decision(auto/manual/reject)`

## Canonical Files To Touch
- `backend/strategy/`

## Must Read Before Coding
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/03_strategy_validation/02_validation_engine.md`

## Hard Invariants
- 只做边界与模板版本管理
- 不做 RPC 真相确认
- 不做执行编译

## Non-goals
- 链上状态确认
- 执行
- calldata 生成

## Definition of Done
- 能够根据模板规则分流 auto/manual/reject
- 边界判定结果可追溯

## Minimum Verification
- 模板内通过
- 模板外审批
- 越界直接拒绝

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
