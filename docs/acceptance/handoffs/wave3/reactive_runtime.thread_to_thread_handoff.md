# reactive_runtime 线程间对接单

- 上游线程：`reactive_runtime`
- 下游线程：`execution_layer`、`cli_surface`、其他运行时编排线程
- Wave：`wave3`
- handoff 日期：`2026-04-08`
- 当前分支：`w3-reactive-runtime`
- 当前 HEAD：`b920945`
- 上游 commit：`not verified yet`

## 1. 上游当前已实现（工作树）
- 入口：
  - `run_reactive_runtime_or_raise(...) -> ReactiveRuntimeResult`
  - `run_reactive_runtime(...) -> ReactiveRuntimeResult`
- 运行时状态机接口：
  - `InvestmentStateMachinePort.get_position_state(intent_id)`
  - `InvestmentStateMachinePort.execute_entry_callback(intent, trigger)`
  - `InvestmentStateMachinePort.execute_exit_callback(intent, trigger)`
- 触发与回调模型：
  - `ReactiveTriggerType`: `entry | stop_loss | take_profit`
  - `ReactiveCallbackType`: `entry_callback | exit_stop_loss_callback | exit_take_profit_callback`
  - `InvestmentPositionState`: `PendingEntry | ActivePosition | Closed`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "registered_intent": {
    "intent_id": "str",
    "trade_intent_id": "str | null"
  },
  "reactive_trigger": {
    "trigger_type": "entry | stop_loss | take_profit",
    "intent_id": "str",
    "trade_intent_id": "str | null",
    "triggered_at": "datetime",
    "metadata": "dict"
  },
  "state_machine_port": "implements InvestmentStateMachinePort"
}
```

### 输出对象
```json
{
  "is_executed": "bool",
  "callback_verified": "bool",
  "intent_id": "str | null",
  "trade_intent_id": "str | null",
  "trigger_type": "ReactiveTriggerType | null",
  "callback_type": "ReactiveCallbackType | null",
  "state_before": "InvestmentPositionState | null",
  "state_after": "InvestmentPositionState | null",
  "callback_ref": "str | null",
  "abort_reason": {
    "code": "str",
    "message": "str",
    "field_path": "str | null"
  }
}
```

## 3. 异常模型
```text
ReactiveRuntimeError
MissingReactiveRuntimeSpecError
TriggerBindingError
StateMachineInvariantError
CallbackVerificationError
```

## 4. 约束
- 不允许：
  - 在 reactive runtime 内做自由决策
  - 在 callback 路径重新编译 execution plan
  - 绕过状态机直接假设状态迁移成功
- 仅允许：
  - 基于触发事件路由 entry/exit callback
  - 对 callback 类型与状态迁移做验证
  - 通过结构化错误向下游暴露失败原因

## 5. 示例
- sample request：
```json
{
  "registered_intent": {
    "intent_id": "intent-001",
    "trade_intent_id": "ti-001"
  },
  "reactive_trigger": {
    "trigger_type": "stop_loss",
    "intent_id": "intent-001",
    "trade_intent_id": "ti-001"
  }
}
```
- sample response（单测路径）：
```json
{
  "is_executed": true,
  "callback_verified": true,
  "callback_type": "exit_stop_loss_callback",
  "state_before": "ActivePosition",
  "state_after": "Closed",
  "callback_ref": "tx-exit-001",
  "abort_reason": null
}
```
- sample failure：
  - `stop_loss` on `PendingEntry` -> `StateMachineInvariantError`
  - callback 未产生期望状态迁移 -> `CallbackVerificationError`

## 6. 剩余问题
- 上游 commit 锚点：`not verified yet`
- 与真实 Investment Position State Machine 合约适配：`not verified yet`
- 与 execution_layer 的 tx receipt/log 串联：`not verified yet`
- 仅基于当前工作树验证，不是冻结 tag 基线：`not verified yet`
