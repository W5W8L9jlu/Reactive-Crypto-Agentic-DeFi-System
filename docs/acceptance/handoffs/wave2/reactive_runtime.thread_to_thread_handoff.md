# 线程间对接单

- 上游线程: `execution_compiler` 提供注册期 plan; `investment_state_machine_contract` 提供状态机接口面
- 下游线程: `execution_layer` / `wave2` 集成与更真实的链上 adapter
- Wave: `wave2`
- handoff 日期: `2026-04-01`
- 上游 commit: `not verified yet`

## 1. 已稳定的东西
- 接口:
  - `ReactiveRuntime.register_execution_plan(execution_plan) -> ReactiveExecutionPlan`
  - `ReactiveRuntime.handle_trigger(trigger) -> None`
  - `InvestmentPositionStateMachinePort.register_investment_intent(intent_id, intent) -> None`
  - `InvestmentPositionStateMachinePort.execute_reactive_trigger(intent_id, observed_out, runtime_exit_min_out) -> None`
  - `InvestmentPositionStateMachinePort.get_position_state(intent_id) -> ReactivePositionState | str`
- 对象:
  - `ReactiveExecutionPlan`
  - `ReactiveRegisterPayload`
  - `ReactiveExecutionHardConstraints`
  - `ReactiveTrigger`
  - `InvestmentStateMachineIntent`
  - `ReactivePositionState`
  - `ReactiveTriggerKind`
- 枚举:
  - `ReactivePositionState = PendingEntry | ActivePosition | Closed`
  - `ReactiveTriggerKind = entry | stop_loss | take_profit`
- 异常:
  - `UnknownReactiveIntentError`
  - `CallbackValidationError`
  - `MissingReactiveRuntimeSpecError`
- 文件路径:
  - `backend/reactive/adapters/models.py`
  - `backend/reactive/adapters/runtime.py`
  - `backend/reactive/adapters/errors.py`
  - `backend/reactive/adapters/__init__.py`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "execution_plan": {
    "trade_intent_id": "trade-1111",
    "register_payload": {
      "intent_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
      "owner": "0x1111111111111111111111111111111111111111",
      "input_token": "0x2222222222222222222222222222222222222222",
      "output_token": "0x3333333333333333333333333333333333333333",
      "planned_entry_size": 1000,
      "entry_amount_out_minimum": 950,
      "entry_valid_until": 1900000000,
      "max_gas_price_gwei": 200,
      "stop_loss_slippage_bps": 250,
      "take_profit_slippage_bps": 400,
      "exit_min_out_floor": 700
    },
    "hard_constraints": {
      "max_slippage_bps": 30,
      "ttl_seconds": 3600,
      "stop_loss_bps": 250,
      "take_profit_bps": 400
    }
  },
  "trigger": {
    "intent_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
    "kind": "entry",
    "observed_out": 980,
    "runtime_exit_min_out": null
  }
}
```

### 输出对象
```json
{
  "register_side_effect": {
    "method": "register_investment_intent",
    "intent_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
    "intent": {
      "owner": "0x1111111111111111111111111111111111111111",
      "input_token": "0x2222222222222222222222222222222222222222",
      "output_token": "0x3333333333333333333333333333333333333333",
      "planned_entry_size": 1000,
      "entry_min_out": 950,
      "exit_min_out_floor": 700
    }
  },
  "trigger_side_effect": {
    "method": "execute_reactive_trigger",
    "intent_id": "0x1111111111111111111111111111111111111111111111111111111111111111",
    "observed_out": 980,
    "runtime_exit_min_out": 0
  }
}
```

### 异常模型
```text
UnknownReactiveIntentError
CallbackValidationError
MissingReactiveRuntimeSpecError
```

## 3. 约束
- 不允许:
  - 在 runtime 内做自由决策
  - 在 runtime 内重编译 execution plan
  - 在 `PendingEntry` 状态执行 `stop_loss` 或 `take_profit`
  - 在 `ActivePosition` 状态再次执行 `entry`
  - 在 `Closed` 状态继续消费 callback
- 仅允许:
  - 消费已注册的 `ReactiveExecutionPlan`
  - 消费显式 `ReactiveTrigger`
  - 通过状态机 port 做注册和触发
- 单位与精度约定:
  - `planned_entry_size` / `entry_min_out` / `exit_min_out_floor` / `observed_out` / `runtime_exit_min_out` 保持整数
  - `stop_loss_bps` / `take_profit_bps` / `max_slippage_bps` 使用 bps 整数
- 空值 / 默认值约定:
  - `entry` 触发允许 `runtime_exit_min_out = null`, 转发时固定为 `0`
  - `stop_loss` / `take_profit` 触发不允许缺少 `runtime_exit_min_out`

## 4. 示例
- sample request:
  - `register_execution_plan(execution_plan)`
  - `handle_trigger(trigger)`
- sample response:
  - 注册返回 `ReactiveExecutionPlan`
  - trigger 处理无直接返回, 以状态机 side effect 为准
- sample failure:
  - 未注册 intent 收到 callback -> `UnknownReactiveIntentError`
  - `PendingEntry` 状态收到 exit trigger -> `CallbackValidationError`
  - 状态机返回未知状态 -> `MissingReactiveRuntimeSpecError`

## 5. 未完成项
- TODO: callback 来源认证机制未冻结
- TODO: 真实链上状态机 adapter 未落地
- 临时 workaround:
  - 当前以 `InvestmentPositionStateMachinePort` 作为唯一对接面
  - 真实链上调用方需自行实现该 port
- 风险提示:
  - 当前仅有模块级单元测试
  - 仓库无 commit 历史, 无法提供稳定 commit 锚点
