# cli_surface 线程交付说明（更新于 2026-04-09）

## 基本信息
- 模块名：`cli_surface`
- Prompt 文件：`docs/prompts/cli_surface.prompt.md`
- Wave：`wave3`
- 负责人：`codex（待人工签收）`
- 分支：`codex/wave5`
- HEAD commit：`8e56fbd`

## 本次交付内容
- CLI 子命令面补齐（PRD 全子命令）：
  - `strategy create/list/show/edit`
  - `decision run/dry-run`
  - `approval list/show/approve/reject`
  - `execution show/logs/force-close/fork-replay`
  - `export json/markdown/memo`
  - `monitor alerts/shadow-status`
- 默认启动 wiring 改为生产组装：
  - `create_default_cli_app()` -> `build_production_services()`
  - 命令实跑不再依赖空绑定，不再直接触发 `RouteBindingMissingError`
- 高危专用渲染补齐：
  - critical 告警时输出专用 banner
  - banner 明确输出 `agent-cli execution force-close <intent_id>`

## 修改了哪些文件（本线程核心）
- `backend/cli/app.py`
- `backend/cli/wiring.py`
- `backend/cli/test_app.py`
- `backend/cli/test_wiring.py`
- `backend/cli/views/alerts.py`

## 本线程实际执行过的命令
```bash
python -m unittest backend.cli.test_app backend.cli.test_wiring backend.cli.views.test_alerts backend.cli.approval.test_approval_flow backend.export.test_export_outputs backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration backend.decision.orchestrator.test_main_chain_service backend.decision.adapters.test_cryptoagents_runner
```

## 命令结果摘要
- 退出码：`0`
- 测试结果：`Ran 30 tests in 5.483s`，`OK`

## 未交付内容 / 风险
- 默认 `build_production_services()` 仍含占位返回（`decision.*` 为 `status=todo`），尚非真实生产执行链路。
- `execution force-close` 在 CLI 默认 wiring 仍是占位提交文案，尚未直连真实链上调用。
- Sepolia smoke 证据缺失，因此不满足“Phase 1 完成”判定。

## 对下游影响
- 下游可依赖：完整命令面、统一路由入口、critical 告警强提示。
- 下游仍需补：真实 service adapter 绑定与 testnet 端到端 smoke。

