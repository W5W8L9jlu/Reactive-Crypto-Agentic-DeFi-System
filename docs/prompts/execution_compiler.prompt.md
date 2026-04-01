# Prompt Template: Execution Compiler

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `execution_compiler` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/04_execution/01_execution_compiler.md
4. docs/contracts/execution_compiler.contract.md

Optional supporting files:
- docs/knowledge/01_core/01_system_invariants.md
- docs/knowledge/01_core/02_domain_models.md
- docs/knowledge/03_strategy_validation/03_pre_registration_check.md
- docs/knowledge/05_reactive_contracts/02_investment_state_machine.md

Only edit these paths:
- backend/execution/compiler/

Do not:
- 触发时重新编译
- 运行时执行 swap
- 替代合约运行时检查

Hard invariants to preserve:
- 编译只发生在注册时
- AI 不生成 calldata
- 入场是绝对约束；出场是相对 slippage BPS
- 失败快速抛异常，不做局部吞异常

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 生成 entryAmountOutMinimum/maxGasPriceGwei/entryValidUntil
- 生成 stopLossSlippageBps/takeProfitSlippageBps
- 产出完整 ExecutionPlan 与 register payload

Verification:
- 编译结果字段完整性
- 入场/出场约束分离测试
- 非法输入异常测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
