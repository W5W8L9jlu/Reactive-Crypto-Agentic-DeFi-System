# 线程交付说明

## 基本信息
- 模块名: `00_generic`
- Prompt 文件: `not verified yet`
- Wave: `wave5`
- 负责人: `not verified yet`
- 分支: `codex/wave5`
- HEAD commit: `8e56fbd`

## 本次交付做了什么（事实）
- 修复 `cli_surface` 阻塞问题：Typer 参数从 `str | None` 改为兼容写法，并补齐 Phase 1 命令面。
- 打通 emergency 映射最小闭环：`recommendation -> emergencyForceClose` 参数转换、gateway 调用、对应单测。
- 对齐 emergency 合约接口：`IReactiveInvestmentCompiler` 补齐声明，合约与测试同步到同一签名语义。
- 复跑 fix-plan 指定测试与跨模块回归，补充当前可复现证据。

## 修改了哪些文件（本轮关注）
- `backend/cli/app.py`
- `backend/cli/views/alerts.py`
- `backend/cli/test_app.py`
- `backend/cli/test_wiring.py`（新）
- `backend/cli/wiring.py`（新）
- `backend/execution/runtime/contract_gateway.py`（未跟踪）
- `backend/execution/runtime/errors.py`（未跟踪）
- `backend/execution/runtime/test_contract_gateway.py`（未跟踪）
- `backend/execution/runtime/test_web3_contract_gateway_integration.py`（未跟踪）
- `backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`
- `backend/contracts/test/ReactiveInvestmentCompiler.t.sol`
- `backend/decision/schemas/cryptoagents_adapter.py`（未跟踪）
- `backend/decision/schemas/test_cryptoagents_adapter.py`（未跟踪）

## 没有交付的项
- `backend/decision/`、`backend/execution/runtime/` 尚未纳入已跟踪快照（仍为 `??`）。
- `shadow_monitor -> emergency` 真链路（web3/anvil）在当前环境仅 `skipped`，未形成通过证据。
- 发布快照治理未完成（生成物目录改动仍较多）。

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status --short --branch

$env:PYTHONPATH='.'; pytest backend/cli/test_app.py -q
$env:PYTHONPATH='.'; pytest backend/cli/approval/test_approval_flow.py backend/cli/views/test_alerts.py -q
$env:PYTHONPATH='.'; pytest backend/decision/schemas/test_cryptoagents_adapter.py -q
$env:PYTHONPATH='.'; pytest backend/execution/runtime/test_execution_layer.py -q
$env:PYTHONPATH='.'; pytest backend/execution/runtime/test_contract_gateway.py -q
$env:PYTHONPATH='.'; pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q
$env:PYTHONPATH='.'; pytest backend/decision/orchestrator/test_main_chain_service.py -q
$env:PYTHONPATH='.'; pytest backend/decision/adapters/test_cryptoagents_runner.py -q
$env:PYTHONPATH='.'; pytest backend/cli/test_app.py backend/cli/test_wiring.py backend/cli/approval/test_approval_flow.py backend/cli/views/test_alerts.py backend/decision/schemas/test_cryptoagents_adapter.py backend/execution/compiler/test_execution_compiler.py backend/execution/runtime/test_contract_gateway.py backend/execution/runtime/test_execution_layer.py backend/reactive/adapters/test_reactive_runtime.py backend/export/test_export_outputs.py backend/validation/test_validation_engine.py backend/strategy/tests/test_strategy_boundary_service.py backend/data/fetchers/test_aggregated_fetchers.py backend/data/context_builder/test_context_builder.py -q

forge test --root . --contracts backend/contracts/test --match-path backend/contracts/test/ReactiveInvestmentCompiler.t.sol -vv
```

## 命令结果摘要
- 首次直接跑 `pytest backend/cli/test_app.py -q` 报 `ModuleNotFoundError: backend`；加 `PYTHONPATH=.` 后恢复。
- fix-plan 关键命令结果：`5 passed`、`7 passed`、`1 passed`、`1 passed`、`3 passed`、`3 skipped`。
- adapter/orchestrator 补充命令结果：`2 passed`、`2 passed`。
- 扩展回归：`58 passed`。
- 合约回归：`12 passed, 0 failed`。

## 对下游线程的影响
- CLI 层可直接消费 `execution force-close <intent-id>` 与 `monitor shadow-status` 命令。
- Runtime 层新增 `build_emergency_force_close_call` 约束：`intent_id` 必须 bytes32 hex、`max_slippage_bps` 必须在 `[0,10000]`。
- 合约接口消费方可统一依赖 `IReactiveInvestmentCompiler` emergency 声明；但 web3/anvil E2E 仍需补证。
