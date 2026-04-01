# Implementation Contract: Execution Compiler

## Module ID
`execution_compiler`

## Working Directory
`backend/execution/compiler`

## Primary Knowledge File
- `docs/knowledge/04_execution/01_execution_compiler.md`

## Scope
本模块只负责以下职责：
- 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil
- 生成 stopLossSlippageBps/takeProfitSlippageBps
- 产出完整 ExecutionPlan 与 register payload

## Inputs
- `StrategyIntent`
- `TradeIntent`
- `registration-time chain state`

## Outputs
- `ExecutionPlan`
- `InvestmentIntent register payload`

## Canonical Files To Touch
- `backend/execution/compiler/`

## Must Read Before Coding
- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/03_strategy_validation/03_pre_registration_check.md`
- `docs/knowledge/05_reactive_contracts/02_investment_state_machine.md`

## Hard Invariants
- 编译只发生在注册时
- AI 不生成 calldata
- 入场是绝对约束；出场是相对 slippage BPS
- 失败快速抛异常，不做局部吞异常

## Non-goals
- 触发时重新编译
- 运行时执行 swap
- 替代合约运行时检查

## Definition of Done
- 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil
- 生成 stopLossSlippageBps/takeProfitSlippageBps
- 产出完整 ExecutionPlan 与 register payload

## Minimum Verification
- 编译结果字段完整性
- 入场/出场约束分离测试
- 非法输入异常测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
