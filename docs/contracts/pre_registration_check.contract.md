# Implementation Contract: PreRegistrationCheck

## Module ID
`pre_registration_check`

## Working Directory
`backend/validation`

## Primary Knowledge File
- `docs/knowledge/03_strategy_validation/03_pre_registration_check.md`

## Scope
本模块只负责以下职责：
- 复核 reserve/slippage/balance/allowance/gas/TTL
- 给出明确 abort reason

## Inputs
- `TradeIntent`
- `StrategyIntent`
- `RPC state snapshot`

## Outputs
- `registration allowed / abort + reason`

## Canonical Files To Touch
- `backend/validation/pre_registration_check.py`

## Must Read Before Coding
- `docs/knowledge/07_data/02_source_of_truth_rules.md`
- `docs/knowledge/04_execution/01_execution_compiler.md`

## Hard Invariants
- 注册前检查只信 RPC
- 必须校验 Gas / Expected Profit
- 只负责注册时可行性，不做运行时最终防守
- 失败快速抛异常

## Non-goals
- 运行时 require 检查
- 触发后重新决策

## Definition of Done
- 复核 reserve/slippage/balance/allowance/gas/TTL
- 给出明确 abort reason

## Minimum Verification
- gas 太高拒绝
- TTL 过期拒绝
- allowance/balance 不足拒绝

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
