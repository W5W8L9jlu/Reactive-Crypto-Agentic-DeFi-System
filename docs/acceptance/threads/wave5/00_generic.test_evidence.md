# 线程测试证据（2026-04-09）

## 测试目标
- 验证 fix-plan 阻塞项是否被消除：CLI surface、cryptoagents adapter、execution layer、emergency 接口一致性。
- 验证 monitor/emergency 最小联动路径在当前环境的真实可运行状态（pass/skip/不可验证）。

## 覆盖场景
- happy path：
  - CLI 路由与展示命令可调用。
  - cryptoagents adapter 输出结构化对象并保持 thesis 分离。
  - execution layer/runtime 基础执行回执链路可记录。
  - emergency 合约入口与状态机回归通过。
- failure path：
  - `intent_id` 非 bytes32 hex 时，emergency 映射抛域错误。
- edge case：
  - `web3/anvil` 不可用时，web3 集成用例被显式 `skipped`（不是假通过）。

## 输入样例
```json
{
  "recommendation": {
    "intent_id": "0x2222222222222222222222222222222222222222222222222222222222222222",
    "reason_code": "TAKE_PROFIT_BREACH"
  },
  "max_slippage_bps": 900
}
```

## 输出样例
```json
{
  "intent_id": "0x2222222222222222222222222222222222222222222222222222222222222222",
  "max_slippage_bps": 900,
  "status": "success"
}
```

## 命令
```bash
pytest backend/cli/test_app.py -q
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

## 实际结果
- 首条命令：`ERROR (ModuleNotFoundError: backend)`（环境变量未设）。
- 其余结果：
  - `5 passed`
  - `7 passed`
  - `1 passed`
  - `1 passed`
  - `3 passed`
  - `3 skipped`
  - `2 passed`
  - `2 passed`
  - `58 passed`
  - `12 passed, 0 failed`
- 共同警告：`PytestCacheWarning`（当前环境无 `.pytest_cache` 写权限）。

## 结论
- fix-plan 的核心回归在本环境已通过。
- `web3/anvil` 集成闭环仍是 `not verified yet`（本次仅拿到 skipped 证据）。
