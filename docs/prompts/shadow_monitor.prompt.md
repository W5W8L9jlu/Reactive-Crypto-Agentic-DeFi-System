# Prompt Template: Shadow Monitor

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `shadow_monitor` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/06_cli_ops/02_shadow_monitor.md
4. docs/contracts/shadow_monitor.contract.md

Optional supporting files:
- docs/knowledge/05_reactive_contracts/03_emergency_force_close.md
- docs/knowledge/07_data/02_source_of_truth_rules.md

Only edit these paths:
- backend/monitor/shadow_monitor.py
- backend/monitor/reconciliation_daemon.py

Do not:
- 正常执行链路
- 日常决策

Hard invariants to preserve:
- 独立于 Reactive 运行
- 只看不摸，除非报警
- 使用备用 RPC 对账
- 有 Grace Period，避免与正常回调竞争

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 能发现该死却没死的持仓
- 能输出高危警报与额外损失估算

Verification:
- Grace Period 测试
- 延迟告警测试
- 状态已关闭不重复报警测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
