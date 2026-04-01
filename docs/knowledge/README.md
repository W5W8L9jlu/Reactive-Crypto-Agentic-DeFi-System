# PRD 模块化知识库

此目录将原始 PRD 拆分为可并行开发的知识块，目标是：

- 降低单次上下文体积
- 明确模块职责与边界
- 支持多人并行开发
- 支持 Codex / GPT 按需装载上下文

## 推荐并行开发分组

### Track A：Decision / Schema
- `01_core/01_system_invariants.md`
- `01_core/02_domain_models.md`
- `02_decision/01_cryptoagents_adapter.md`
- `02_decision/02_context_builder.md`

### Track B：Strategy / Validation / Approval
- `03_strategy_validation/01_strategy_boundary.md`
- `03_strategy_validation/02_validation_engine.md`
- `03_strategy_validation/03_pre_registration_check.md`
- `03_strategy_validation/04_approval_flow.md`

### Track C：Execution / Reactive / Contracts
- `04_execution/01_execution_compiler.md`
- `04_execution/02_execution_layer.md`
- `05_reactive_contracts/01_reactive_runtime.md`
- `05_reactive_contracts/02_investment_state_machine.md`
- `05_reactive_contracts/03_emergency_force_close.md`

### Track D：CLI / Monitor / Export
- `06_cli_ops/01_cli_surface.md`
- `06_cli_ops/02_shadow_monitor.md`
- `08_delivery/01_export_outputs.md`

### Track E：Data / Infra / Test
- `07_data/01_provider_architecture.md`
- `07_data/02_source_of_truth_rules.md`
- `08_delivery/02_repo_layout_and_stack.md`
- `09_testing/01_test_plan.md`

## 使用方式

每次开发只加载：
1. 当前模块文件
2. 依赖的 domain models
3. system invariants
4. 接口契约文件

## 原始文件
- Source: `prd_final_v10.md`
