# 线程测试证据

## 测试目标
- 验证 execution layer 只在 `Reactive trigger` 且 `onchain_checks_passed=True` 时发起执行
- 验证成功 / 失败链上回执都能生成与回执一致的 `ExecutionRecord`
- 验证 `ExecutionRecord` 能被现有 `export_outputs` 模块消费

## 覆盖的场景
- happy path：成功回执生成 `execution_status="succeeded"`
- failure path：失败回执生成 `execution_status="failed"` 并保留 `revert_reason`
- gate path：`onchain_checks_passed=False` 时抛出 `RuntimeGateError`，且不触发 executor
- compatibility path：`ExecutionRecord.model_dump(mode="json")` 与 `export_outputs` 的 `ExecutionRecord` wrapper 兼容

## 输入
```json
{
  "execution_plan": {
    "trade_intent_id": "trade-intent-001",
    "register_payload": {
      "intent_id": "0xintent001"
    }
  },
  "runtime_trigger": {
    "trigger_id": "trigger-001",
    "trade_intent_id": "trade-intent-001",
    "trigger_source": "reactive.runtime",
    "triggered_at": "2026-04-01T09:05:00+00:00",
    "onchain_checks_passed": true,
    "metadata": {
      "condition": "take_profit"
    }
  },
  "chain_receipt": {
    "transaction_hash": "0xtx-success",
    "block_number": 22222222,
    "gas_used": 210000,
    "status": 1,
    "logs": [
      {
        "address": "0xpool",
        "topics": [
          "0xabc"
        ],
        "data": "0x01"
      }
    ],
    "effective_gas_price_wei": 12000000000
  }
}
```

## 输出
```json
{
  "trade_intent_id": "trade-intent-001",
  "intent_id": "0xintent001",
  "trigger_id": "trigger-001",
  "trigger_source": "reactive.runtime",
  "execution_status": "succeeded",
  "receipt": {
    "transaction_hash": "0xtx-success",
    "status": 1
  }
}
```

## 命令
```bash
python -m unittest -v backend/execution/runtime/test_execution_layer.py
```

## 实际结果
- 通过：`test_success_receipt_produces_execution_record`
- 通过：`test_failed_receipt_is_recorded_without_guessing_success`
- 通过：`test_runtime_checks_must_pass_before_any_chain_call`
- 通过：`test_execution_record_json_dump_is_export_compatible`
- 统计：`Ran 4 tests ... OK`
- 未覆盖：
  - 真实链上 RPC / 合约调用
  - 持久化存储或回执落库
  - 跨模块端到端 happy path

## 备注
- 测试使用 `RecordingExecutor` stub，验证的是 execution layer 的边界和 record 形状，不是链上集成
- 当前仓库未验证 `pytest` 或其他测试框架，仅实际运行了 `unittest`
