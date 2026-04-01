# Prompt Template: Emergency Force Close

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `emergency_force_close` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/05_reactive_contracts/03_emergency_force_close.md
4. docs/contracts/emergency_force_close.contract.md

Optional supporting files:
- docs/knowledge/06_cli_ops/02_shadow_monitor.md
- docs/knowledge/05_reactive_contracts/02_investment_state_machine.md

Only edit these paths:
- backend/contracts/core/ReactiveInvestmentCompiler.sol

Do not:
- 日常执行路径
- 替代正常 reactive callback

Hard invariants to preserve:
- 仅 owner/authorized relayer 调用
- 仅 ActivePosition 时允许
- 先写 Closed 再紧急卖出
- 后续迟滞回调必须 Revert

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- break-glass 路径可用
- 与 shadow monitor 告警联动

Verification:
- 权限测试
- 非 ActivePosition 拒绝测试
- force-close 后迟滞回调 revert 测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
