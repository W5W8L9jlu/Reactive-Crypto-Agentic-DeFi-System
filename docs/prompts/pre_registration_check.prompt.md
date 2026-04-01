# Prompt Template: PreRegistrationCheck

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `pre_registration_check` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/03_strategy_validation/03_pre_registration_check.md
4. docs/contracts/pre_registration_check.contract.md

Optional supporting files:
- docs/knowledge/07_data/02_source_of_truth_rules.md
- docs/knowledge/04_execution/01_execution_compiler.md

Only edit these paths:
- backend/validation/pre_registration_check.py

Do not:
- 运行时 require 检查
- 触发后重新决策

Hard invariants to preserve:
- 注册前检查只信 RPC
- 必须校验 Gas / Expected Profit
- 只负责注册时可行性，不做运行时最终防守
- 失败快速抛异常

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 复核 reserve/slippage/balance/allowance/gas/TTL
- 给出明确 abort reason

Verification:
- gas 太高拒绝
- TTL 过期拒绝
- allowance/balance 不足拒绝

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
