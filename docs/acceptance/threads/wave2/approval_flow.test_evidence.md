# approval_flow 线程测试证据

## 测试目标
- 验证默认审批展示输出 battle card，不泄露 raw JSON
- 验证 `raw=True` 透传 machine truth
- 验证 TTL 过期阻止 approve
- 验证 battle card 数值映射一致
- 验证 compiler/validation/export 基线与审批模块兼容

## 覆盖的场景
- happy path：
  - `show_approval(...)` 默认展示 battle card
  - `show_approval(raw=True)` 返回 machine truth
  - `compile_execution_plan(...)` 输出冻结值符合预期
- failure path：
  - `approve_intent(...)` 在过期条件下抛 `ApprovalExpiredError`
- edge case：
  - `reject_intent(...)` 返回 `ApprovalRejectedResult`
  - `freeze_contract_call_inputs(...)` 固化合约入参 shape

## 输入
```json
{
  "trade_intent": {
    "trade_intent_id": "trade-001",
    "strategy_intent_id": "strategy-001",
    "pair": "ETH/USDC",
    "dex": "uniswap-v3",
    "position_usd": "1500",
    "max_slippage_bps": 100,
    "stop_loss_bps": 300,
    "take_profit_bps": 800,
    "ttl_seconds": 300
  },
  "execution_plan.register_payload": {
    "intentId": "intent-001",
    "plannedEntrySize": 600000000,
    "entryAmountOutMinimum": 1450000000,
    "entryValidUntil": 1772484240,
    "maxGasPriceGwei": 55,
    "exitMinOutFloor": 1305000000
  },
  "decision_meta": {
    "trade_intent_id": "trade-001",
    "created_at": "2026-04-03T10:00:00Z",
    "ttl_seconds": 300
  }
}
```

## 输出
```json
{
  "compiler_tests": "2 passed",
  "validation_tests": "6 passed",
  "export_tests": "4 passed",
  "approval_flow_tests": "5 passed",
  "sample_show_output_contains": [
    "Approval Battle Card",
    "TTL Remaining: 5m 0s",
    "Approve: allowed"
  ]
}
```

## 命令
```bash
python -m unittest backend.execution.compiler.test_execution_compiler -v
python -m unittest backend.validation.test_validation_engine -v
python -m unittest backend.export.test_export_outputs -v
python -m unittest backend.cli.approval.test_approval_flow -v
@'
# python inline: call show_approval(...) with structured models
'@ | python -
```

## 实际结果
- `python -m unittest backend.execution.compiler.test_execution_compiler -v`
  - 通过，2 个测试
- `python -m unittest backend.validation.test_validation_engine -v`
  - 通过，6 个测试
- `python -m unittest backend.export.test_export_outputs -v`
  - 通过，4 个测试
- `python -m unittest backend.cli.approval.test_approval_flow -v`
  - 通过，5 个测试
- Python inline `show_approval(...)`
  - 成功输出 battle card 文本，包含 `TTL Remaining: 5m 0s`

## 备注
- 当前验证集中未覆盖 CLI route / adapter 端到端调用，记为 `not verified yet`
