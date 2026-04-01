# Task Routing Matrix

| 任务 | 模块 | 必读文件 | 建议工作目录 |
|---|---|---|---|
| 改 Portfolio Manager 输出为结构化对象 | `cryptoagents_adapter` | `docs/knowledge/02_decision/01_cryptoagents_adapter.md` + `docs/contracts/cryptoagents_adapter.contract.md` | `backend/decision` |
| 统一 provider 输出并构建 DecisionContext | `decision_context_builder` | `docs/knowledge/02_decision/02_context_builder.md` + `docs/contracts/decision_context_builder.contract.md` | `backend/data` |
| 实现模板内/外分流 | `strategy_boundary_service` | `docs/knowledge/03_strategy_validation/01_strategy_boundary.md` + `docs/contracts/strategy_boundary_service.contract.md` | `backend/strategy` |
| 补 Pydantic 校验 | `validation_engine` | `docs/knowledge/03_strategy_validation/02_validation_engine.md` + `docs/contracts/validation_engine.contract.md` | `backend/validation` |
| 加注册前 gas/profit 检查 | `pre_registration_check` | `docs/knowledge/03_strategy_validation/03_pre_registration_check.md` + `docs/contracts/pre_registration_check.contract.md` | `backend/validation` |
| 实现 battle card 审批展示 | `approval_flow` | `docs/knowledge/03_strategy_validation/04_approval_flow.md` + `docs/contracts/approval_flow.contract.md` | `backend/cli` |
| 生成 register payload | `execution_compiler` | `docs/knowledge/04_execution/01_execution_compiler.md` + `docs/contracts/execution_compiler.contract.md` | `backend/execution/compiler` |
| 接入 reactive 后的执行回执 | `execution_layer` | `docs/knowledge/04_execution/02_execution_layer.md` + `docs/contracts/execution_layer.contract.md` | `backend/execution/runtime` |
| 实现 stop/tp 触发适配 | `reactive_runtime` | `docs/knowledge/05_reactive_contracts/01_reactive_runtime.md` + `docs/contracts/reactive_runtime.contract.md` | `backend/reactive` |
| 实现链上状态机 | `investment_state_machine_contract` | `docs/knowledge/05_reactive_contracts/02_investment_state_machine.md` + `docs/contracts/investment_state_machine_contract.contract.md` | `backend/contracts/core` |
| 实现紧急平仓 | `emergency_force_close` | `docs/knowledge/05_reactive_contracts/03_emergency_force_close.md` + `docs/contracts/emergency_force_close.contract.md` | `backend/contracts/core` |
| 补 CLI 命令面 | `cli_surface` | `docs/knowledge/06_cli_ops/01_cli_surface.md` + `docs/contracts/cli_surface.contract.md` | `backend/cli` |
| 实现备用 RPC 对账告警 | `shadow_monitor` | `docs/knowledge/06_cli_ops/02_shadow_monitor.md` + `docs/contracts/shadow_monitor.contract.md` | `backend/monitor` |
| 实现 provider 抽象层 | `provider_architecture` | `docs/knowledge/07_data/01_provider_architecture.md` + `docs/contracts/provider_architecture.contract.md` | `backend/data/providers` |
| 导出 JSON/Audit/Memo | `export_outputs` | `docs/knowledge/08_delivery/01_export_outputs.md` + `docs/contracts/export_outputs.contract.md` | `backend/export` |