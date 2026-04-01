# Prompt Template: Strategy Boundary Service

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `strategy_boundary_service` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/03_strategy_validation/01_strategy_boundary.md
4. docs/contracts/strategy_boundary_service.contract.md

Optional supporting files:
- docs/knowledge/01_core/02_domain_models.md
- docs/knowledge/03_strategy_validation/02_validation_engine.md

Only edit these paths:
- backend/strategy/

Do not:
- 链上状态确认
- 执行
- calldata 生成

Hard invariants to preserve:
- 只做边界与模板版本管理
- 不做 RPC 真相确认
- 不做执行编译

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 能够根据模板规则分流 auto/manual/reject
- 边界判定结果可追溯

Verification:
- 模板内通过
- 模板外审批
- 越界直接拒绝

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
