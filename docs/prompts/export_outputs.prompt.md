# Prompt Template: Export Outputs

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `export_outputs` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/08_delivery/01_export_outputs.md
4. docs/contracts/export_outputs.contract.md

Optional supporting files:
- docs/knowledge/01_core/01_system_invariants.md
- docs/knowledge/01_core/02_domain_models.md

Only edit these paths:
- backend/export/

Do not:
- 执行
- 策略判断
- 审批逻辑

Hard invariants to preserve:
- 执行 = JSON 真相
- 审计 = 摘抄
- 报告 = 生成
- Audit Markdown 不得改写结论

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 三轨输出边界清晰
- Audit 与 JSON 字段 1:1 可追溯

Verification:
- JSON/Audit 一致性测试
- Memo 不污染 machine truth 测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
