# 线程测试证据

## 测试目标
- 验证 `reactive_runtime` 最小闭环是否覆盖：
  - entry trigger
  - stop/take trigger
  - callback 验证

## 覆盖场景
- `entry` 在 `PendingEntry` 状态触发入场 callback 并迁移到 `ActivePosition`
- `stop_loss` 在 `ActivePosition` 触发出场 callback 并迁移到 `Closed`
- `take_profit` 在 `ActivePosition` 触发出场 callback 并迁移到 `Closed`
- callback 返回与预期状态迁移不一致时抛 `CallbackVerificationError`
- 非 `ActivePosition` 状态触发 `stop_loss` 时抛 `StateMachineInvariantError`

## 命令
```bash
$env:PYTHONPATH='.'; python -m unittest backend.reactive.adapters.test_reactive_runtime -v
```

## 输入（测试夹具）
```json
{
  "registered_intent": {
    "intent_id": "intent-001",
    "trade_intent_id": "ti-001"
  },
  "trigger_types": ["entry", "stop_loss", "take_profit"],
  "state_machine": "FakeStateMachine"
}
```

## 输出（关键断言）
```json
{
  "entry": {
    "callback_type": "entry_callback",
    "state_before": "PendingEntry",
    "state_after": "ActivePosition",
    "callback_verified": true
  },
  "stop_loss": {
    "callback_type": "exit_stop_loss_callback",
    "state_before": "ActivePosition",
    "state_after": "Closed",
    "callback_verified": true
  },
  "take_profit": {
    "callback_type": "exit_take_profit_callback",
    "state_before": "ActivePosition",
    "state_after": "Closed",
    "callback_verified": true
  }
}
```

## 实际结果
- 命令输出：
  - `Ran 5 tests in 0.001s`
  - `OK`
- 单测明细：
  - `test_entry_trigger_executes_entry_callback_from_pending_entry` -> `ok`
  - `test_stop_loss_trigger_executes_exit_callback_from_active_position` -> `ok`
  - `test_take_profit_trigger_executes_exit_callback_from_active_position` -> `ok`
  - `test_callback_verification_fails_when_state_machine_does_not_transition_state` -> `ok`
  - `test_stop_loss_trigger_is_blocked_when_position_not_active` -> `ok`

## 未验证项
- 真实链上状态机适配器集成测试：`not verified yet`
- callback 到 execution layer tx receipt/log 落库链路：`not verified yet`
- 与其他 wave3 模块串联 dry-run：`not verified yet`
