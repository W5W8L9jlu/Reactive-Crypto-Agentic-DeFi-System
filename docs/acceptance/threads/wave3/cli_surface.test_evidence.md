# cli_surface 线程测试证据（更新于 2026-04-09）

## 测试目标
- 覆盖 PRD 要求的 CLI 子命令面（strategy/decision/approval/execution/export/monitor）。
- 验证高危告警专用渲染与 force-close 文案提示。
- 验证默认 wiring 可运行（不再触发 `RouteBindingMissingError`）。

## 执行命令（本次实测）
```bash
python -m unittest backend.cli.test_app backend.cli.test_wiring backend.cli.views.test_alerts backend.cli.approval.test_approval_flow backend.export.test_export_outputs backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration backend.decision.orchestrator.test_main_chain_service backend.decision.adapters.test_cryptoagents_runner
```

## 关键覆盖点
- CLI 子命令调用覆盖：
  - `strategy create/list/show/edit`
  - `decision run/dry-run`
  - `approval list/show/approve/reject`
  - `execution show/logs/force-close/fork-replay`
  - `export json/markdown/memo`
  - `monitor alerts/shadow-status`
- 高危告警渲染覆盖：
  - `monitor alerts --critical-only` 输出 `CRITICAL ALERT`
  - 输出明确指令：`agent-cli execution force-close intent-001`
- wiring 覆盖：
  - `build_production_services()` 可绑定全部 CLI route
  - `create_cli_app(services=build_production_services())` 可直接执行命令并返回 `exit_code=0`

## 实际结果
- 退出码：`0`
- 总计：`Ran 30 tests in 5.483s`
- 结果：`OK`

## 未验证项
- Sepolia 真链 smoke（含审批到注册执行再到 monitor/force-close 的完整链路）尚未形成可复现记录。
- `agent-cli` shell 级可执行入口在当前环境未安装（仅 Typer app 与测试层可调用）。
