# Prompt Template: Execution Layer

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `execution_layer` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/04_execution/02_execution_layer.md
4. docs/contracts/execution_layer.contract.md

Optional supporting files:
- docs/knowledge/05_reactive_contracts/01_reactive_runtime.md
- docs/knowledge/07_data/02_source_of_truth_rules.md

Only edit these paths:
- backend/execution/runtime/

Do not:
- 自由决策
- 重新编译
- 替代状态机

Hard invariants to preserve:
- 不在校验通过后立即 swap
- 只在 Reactive 触发后执行
- 只负责链上调用和回执记录

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 能消费 runtime trigger 并记录执行回执
- ExecutionRecord 与链上回执一致

Verification:
- 执行成功回执测试
- 链上失败回执测试
- record/export 一致性测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
