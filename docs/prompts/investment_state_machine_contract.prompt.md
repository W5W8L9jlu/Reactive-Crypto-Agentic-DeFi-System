# Prompt Template: Investment Position State Machine Contract

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `investment_state_machine_contract` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/05_reactive_contracts/02_investment_state_machine.md
4. docs/contracts/investment_state_machine_contract.contract.md

Optional supporting files:
- docs/knowledge/01_core/01_system_invariants.md
- docs/knowledge/04_execution/01_execution_compiler.md

Only edit these paths:
- backend/contracts/interfaces/IReactiveInvestmentCompiler.sol
- backend/contracts/core/ReactiveInvestmentCompiler.sol

Do not:
- 链下信号后再执行的混合模式
- 自由策略决策

Hard invariants to preserve:
- 状态只能是 PendingEntry -> ActivePosition -> Closed
- Closed 不得再次触发
- 入场成功后记录 actualPositionSize
- 入场和出场运行时检查不同

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 实现 registerInvestmentIntent
- 实现 executeReactiveTrigger
- 实现状态流转与 require 检查

Verification:
- 状态机流转测试
- PendingEntry require 测试
- ActivePosition exit minOut 测试
- Closed 重入拒绝测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
