# Draft Summary

- `模块：` Execution Compiler (`execution_compiler`)
- `阶段：` Registration and Execution
- `目标：` Implement module scope: 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil; 生成 stopLossSlippageBps/takeProfitSlippageBps; 产出完整 ExecutionPlan 与 register payload

## 重点验收

- 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil
- 生成 stopLossSlippageBps/takeProfitSlippageBps
- 产出完整 ExecutionPlan 与 register payload

## 重点非目标

- 触发时重新编译
- 运行时执行 swap
- 替代合约运行时检查

## 重点风险

- 编译只发生在注册时
- AI 不生成 calldata
- 入场是绝对约束；出场是相对 slippage BPS

# Full Draft

# Draft Task Card

## Header

- `模块：` Execution Compiler (`execution_compiler`)
- `负责人 agent：` Backend Architect
- `状态：` Draft
- `来源：` 用户目标 / contract / prompt / knowledge

## 1. 目标

- Implement module scope: 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil; 生成 stopLossSlippageBps/takeProfitSlippageBps; 产出完整 ExecutionPlan 与 register payload

## 2. 验收标准

- [ ] 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil
- [ ] 生成 stopLossSlippageBps/takeProfitSlippageBps
- [ ] 产出完整 ExecutionPlan 与 register payload
- [ ] 编译结果字段完整性
- [ ] 入场/出场约束分离测试
- [ ] 非法输入异常测试

## 3. 非目标

- 触发时重新编译
- 运行时执行 swap
- 替代合约运行时检查

## 4. 风险

- 编译只发生在注册时
- AI 不生成 calldata
- 入场是绝对约束；出场是相对 slippage BPS
- 失败快速抛异常，不做局部吞异常
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。

## 5. 依据

- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/04_execution/01_execution_compiler.md`
- `docs/contracts/execution_compiler.contract.md`
- `docs/prompts/execution_compiler.prompt.md`