# Implementation Contract: Investment Position State Machine Contract

## Module ID
`investment_state_machine_contract`

## Working Directory
`backend/contracts/core`

## Primary Knowledge File
- `docs/knowledge/05_reactive_contracts/02_investment_state_machine.md`

## Scope
本模块只负责以下职责：
- 实现 registerInvestmentIntent
- 实现 executeReactiveTrigger
- 实现状态流转与 require 检查

## Inputs
- `InvestmentIntent register payload`
- `reactive trigger`

## Outputs
- `state transitions`
- `on-chain execution`

## Canonical Files To Touch
- `backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`

## Must Read Before Coding
- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/04_execution/01_execution_compiler.md`

## Hard Invariants
- 状态只能是 PendingEntry -> ActivePosition -> Closed
- Closed 不得再次触发
- 入场成功后记录 actualPositionSize
- 入场和出场运行时检查不同

## Non-goals
- 链下信号后再执行的混合模式
- 自由策略决策

## Definition of Done
- 实现 registerInvestmentIntent
- 实现 executeReactiveTrigger
- 实现状态流转与 require 检查

## Minimum Verification
- 状态机流转测试
- PendingEntry require 测试
- ActivePosition exit minOut 测试
- Closed 重入拒绝测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
