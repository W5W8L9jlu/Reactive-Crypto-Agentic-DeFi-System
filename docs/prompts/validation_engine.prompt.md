# Prompt Template: Validation Engine

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `validation_engine` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/03_strategy_validation/02_validation_engine.md
4. docs/contracts/validation_engine.contract.md

Optional supporting files:
- docs/knowledge/01_core/02_domain_models.md
- docs/knowledge/03_strategy_validation/01_strategy_boundary.md

Only edit these paths:
- backend/validation/

Do not:
- RPC 查询
- calldata 编译
- 审批展示

Hard invariants to preserve:
- 必须基于 Pydantic v2
- 禁止散落 if/else schema 校验
- 不做链上状态确认

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 所有核心对象先解析为强类型对象
- 抛出清晰 ValidationError 或领域异常
- 输出 ValidationResult

Verification:
- 字段范围校验
- 跨字段 model_validator 校验
- 非法对象拒绝测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
