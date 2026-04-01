# 测试证据

- 模块: `reactive_runtime`
- Wave: `wave2`
- 证据日期: `2026-04-01`

## 1. 测试目标
- 验证 entry trigger 会通过状态机执行
- 验证 stop-loss / take-profit trigger 会通过状态机执行
- 验证 callback 在错误状态下会被拒绝

## 2. 覆盖场景
- `test_entry_trigger_executes_via_state_machine`
  - 目标: `PendingEntry` 状态收到 `entry` 触发时，调用状态机执行接口
- `test_stop_and_take_profit_triggers_execute_via_state_machine`
  - 目标: `ActivePosition` 状态收到 `stop_loss` 和 `take_profit` 触发时，调用状态机执行接口并闭合状态
- `test_callback_validation_rejects_exit_trigger_before_entry`
  - 目标: `PendingEntry` 状态下收到 exit trigger 时抛出 `CallbackValidationError`

## 3. 实际运行命令
- `python -m unittest backend.reactive.adapters.test_reactive_runtime -v`
  - 实际结果:
    - `test_callback_validation_rejects_exit_trigger_before_entry ... ok`
    - `test_entry_trigger_executes_via_state_machine ... ok`
    - `test_stop_and_take_profit_triggers_execute_via_state_machine ... ok`
    - `Ran 3 tests in 0.001s`
    - `OK`
- `python -m unittest discover -s backend/reactive/adapters -p 'test_*.py' -v`
  - 实际结果:
    - `test_callback_validation_rejects_exit_trigger_before_entry ... ok`
    - `test_entry_trigger_executes_via_state_machine ... ok`
    - `test_stop_and_take_profit_triggers_execute_via_state_machine ... ok`
    - `Ran 3 tests in 0.001s`
    - `OK`

## 4. 测试输入与输出
- 输入对象:
  - `ReactiveExecutionPlan`
    - `trade_intent_id`
    - `register_payload.intent_id`
    - `register_payload.entry_amount_out_minimum`
    - `register_payload.exit_min_out_floor`
    - `hard_constraints.stop_loss_bps`
    - `hard_constraints.take_profit_bps`
  - `ReactiveTrigger`
    - `intent_id`
    - `kind`
    - `observed_out`
    - `runtime_exit_min_out`
- 观察输出:
  - 假状态机收到 `register_investment_intent(...)`
  - 假状态机收到 `execute_reactive_trigger(intent_id, observed_out, runtime_exit_min_out)`
  - 状态从 `PendingEntry` 进入 `ActivePosition` 或 `Closed`
  - 非法 callback 抛出 `CallbackValidationError`

## 5. 未验证项
- 真实链上状态机合约调用: `not verified yet`
- 真实 RPC / 交易回执: `not verified yet`
- callback 来源认证: `not verified yet`
- 与其他模块的端到端 happy path: `not verified yet`
