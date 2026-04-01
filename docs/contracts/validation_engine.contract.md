# Implementation Contract: Validation Engine

## Module ID
`validation_engine`

## Working Directory
`backend/validation`

## Primary Knowledge File
- `docs/knowledge/03_strategy_validation/02_validation_engine.md`

## Scope
本模块只负责以下职责：
- 所有核心对象先解析为强类型对象
- 抛出清晰 ValidationError 或领域异常
- 输出 ValidationResult

## Inputs
- `StrategyTemplate`
- `StrategyIntent`
- `TradeIntent`

## Outputs
- `ValidationResult`

## Canonical Files To Touch
- `backend/validation/`

## Must Read Before Coding
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/03_strategy_validation/01_strategy_boundary.md`

## Hard Invariants
- 必须基于 Pydantic v2
- 禁止散落 if/else schema 校验
- 不做链上状态确认

## Non-goals
- RPC 查询
- calldata 编译
- 审批展示

## Definition of Done
- 所有核心对象先解析为强类型对象
- 抛出清晰 ValidationError 或领域异常
- 输出 ValidationResult

## Minimum Verification
- 字段范围校验
- 跨字段 model_validator 校验
- 非法对象拒绝测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
