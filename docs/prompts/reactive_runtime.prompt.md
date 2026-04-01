# Prompt Template: Reactive Runtime

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `reactive_runtime` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/05_reactive_contracts/01_reactive_runtime.md
4. docs/contracts/reactive_runtime.contract.md

Optional supporting files:
- docs/knowledge/05_reactive_contracts/02_investment_state_machine.md
- docs/knowledge/04_execution/02_execution_layer.md

Only edit these paths:
- backend/reactive/adapters/

Do not:
- 投资建议
- 策略评估
- 链下兜底决策

Hard invariants to preserve:
- Reactive 负责事件驱动与 callback，不做自由决策
- 入场与出场都经由状态机
- 保留事件驱动逻辑与 callback 验证

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 支持入场/止损/止盈触发
- 与状态机契约对接

Verification:
- entry trigger 测试
- stop/take trigger 测试
- callback 验证测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
