# Prompt Template: CLI Surface

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `cli_surface` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/06_cli_ops/01_cli_surface.md
4. docs/contracts/cli_surface.contract.md

Optional supporting files:
- docs/knowledge/03_strategy_validation/04_approval_flow.md
- docs/knowledge/06_cli_ops/02_shadow_monitor.md

Only edit these paths:
- backend/cli/

Do not:
- 业务核心计算
- 状态机逻辑
- provider logic

Hard invariants to preserve:
- CLI 只负责路由/展示/操作入口
- 不承担复杂业务计算
- 继承 CryptoAgents CLI 风格并扩展审批/监控/导出

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- strategy/decision/approval/execution/export/monitor 命令面完整
- 视图清晰可追溯

Verification:
- 命令路由测试
- 审批显示测试
- alert 视图测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
