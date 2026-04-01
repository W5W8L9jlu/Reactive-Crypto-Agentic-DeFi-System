# Prompt Template: DecisionContextBuilder

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `decision_context_builder` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/02_decision/02_context_builder.md
4. docs/contracts/decision_context_builder.contract.md

Optional supporting files:
- docs/knowledge/01_core/02_domain_models.md
- docs/knowledge/07_data/01_provider_architecture.md
- docs/knowledge/07_data/02_source_of_truth_rules.md

Only edit these paths:
- backend/data/context_builder/
- backend/data/fetchers/

Do not:
- 链上执行
- 最终风控裁决
- Schema 外推

Hard invariants to preserve:
- 以趋势/资金流/风险环境为主，不喂 tick 级噪声
- 执行真相不在本模块产生
- 统一屏蔽 provider 差异

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 统一输出完整 DecisionContext
- Provider 失败时抛明确异常而非吞异常
- 可替换/扩展数据源而不污染上层接口

Verification:
- context 完整性测试
- provider fallback 测试
- 缺数据 / 延迟异常测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
