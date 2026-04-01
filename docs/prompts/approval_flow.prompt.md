# Prompt Template: Approval Flow

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `approval_flow` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/03_strategy_validation/04_approval_flow.md
4. docs/contracts/approval_flow.contract.md

Optional supporting files:
- docs/knowledge/06_cli_ops/01_cli_surface.md
- docs/knowledge/08_delivery/01_export_outputs.md

Only edit these paths:
- backend/cli/views/approval_battle_card.py
- backend/cli/approval/

Do not:
- 机器真相生成
- 执行编译
- 链上执行

Hard invariants to preserve:
- 默认不展示 raw JSON
- 必须显示 TTL 倒计时
- 过期意图禁止审批
- 战报必须由结构化对象映射，不由 LLM 自由生成

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- approval show 默认展示人话战报
- approval show --raw 能看到机器真相
- approve/reject 路径清晰

Verification:
- TTL 过期阻止审批
- --raw 与 machine truth 一致
- 数值映射一致性测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
