# cli_surface 线程内验收清单（更新于 2026-04-09）

- 模块 / prompt：`cli_surface` / `docs/prompts/cli_surface.prompt.md`
- Wave：`wave3`
- 线程负责人：`codex（待人工签收）`
- 分支：`codex/wave5`
- HEAD commit：`8e56fbd`
- 模块相关改动文件（当前工作树）：
  - `backend/cli/app.py`
  - `backend/cli/wiring.py`
  - `backend/cli/test_app.py`
  - `backend/cli/test_wiring.py`
  - `backend/cli/views/alerts.py`
- 是否保持 CLI 模块职责：是（路由/展示/操作入口），但默认 wiring 仍含占位返回。

## A. 职责边界
- 本模块目标职责是否覆盖：是（`strategy/decision/approval/execution/export/monitor` 六组命令可调用）。
- PRD 要求子命令覆盖情况：
  - `strategy create/show/edit`：已覆盖
  - `decision dry-run`：已覆盖
  - `approval list`：已覆盖
  - `execution show/logs/force-close`：已覆盖
  - `export json/markdown/memo`：已覆盖
  - `monitor shadow-status`：已覆盖
- 是否引入 CLI 外核心业务：否（核心业务仍在 service/runtime/contracts）。

## B. Contract 对齐
- 对齐 `docs/contracts/cli_surface.contract.md`：是（CLI 仍为 route + rendering）。
- 已完成对齐点：
  - 默认入口 `create_default_cli_app()` 走 `build_production_services()`，不再走空绑定启动。
  - monitor critical 告警可渲染专用高危 banner，并给出 `agent-cli execution force-close <intent_id>` 指令文案。
- 未完成对齐点：
  - 默认 wiring 的多个 handler 仍为占位响应（例如 `decision.*` 返回 `{"status":"todo"}`）。
  - `execution force-close` 在 CLI 默认 wiring 中尚未直连真实链上执行端口。

## C. Invariants 检查
- CLI 未生成 calldata / 未做签名：满足。
- CLI 未吞掉核心异常：满足（通过显式错误与测试路径验证）。
- CLI 未承载合约状态机：满足。

## D. 验证证据（本次重跑）
- `python -m unittest backend.cli.test_app backend.cli.test_wiring backend.cli.views.test_alerts backend.cli.approval.test_approval_flow backend.export.test_export_outputs backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration backend.decision.orchestrator.test_main_chain_service backend.decision.adapters.test_cryptoagents_runner`
  - 结果：`Ran 30 tests in 5.483s`，`OK`

## E. Known gaps
- 缺少 Sepolia 链上 smoke 证据（`decision dry-run -> approval -> register/execute -> export -> monitor -> force-close`）。
- 本机无 `agent-cli` 可执行入口（命令名未注册到 shell）。
- 默认 `build_production_services()` 仍以占位实现为主，不应视为“生产完成”。

## F. 可交付结论
- 线程状态：`PASS_WITH_BLOCKERS`
- 是否可进入线程间对接：可以（作为 CLI 面能力基线），但不能据此宣告 Phase 1 完成。

