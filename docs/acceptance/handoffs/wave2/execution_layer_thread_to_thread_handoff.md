# 线程间对接单

- 上游线程：`execution_compiler` + `reactive_runtime` 输入对象（按 contract）
- 下游线程：`export_outputs` / `wave2` 集成方
- Wave：`wave2`
- handoff 日期：`2026-04-01`
- 上游 commit：`not verified yet`

## 1. 上游已经稳定的东西
- 接口：`execute_runtime_trigger(execution_plan, runtime_trigger, executor, executed_at=None) -> ExecutionRecord`
- 对象：
  - `RuntimeTrigger`
  - `ChainReceipt`
  - `ExecutionRecord`
  - `CompiledExecutionPlan` 最小消费形状
- 异常：
  - `ExecutionPlanError`
  - `RuntimeGateError`
  - `RuntimeTriggerError`
  - `ReceiptConsistencyError`
  - `ExecutionAdapterError`
- 文件路径：
  - `backend/execution/runtime/execution_layer.py`
  - `backend/execution/runtime/models.py`
  - `backend/execution/runtime/errors.py`
  - `backend/execution/runtime/__init__.py`

## 2. 下游必须按此消费
### 输入对象
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
  }
}
```

### 输出对象
```json
{
  "trade_intent_id": "trade-intent-001",
  "intent_id": "0xintent001",
  "trigger_id": "trigger-001",
  "trigger_source": "reactive.runtime",
  "triggered_at": "2026-04-01T09:05:00+00:00",
  "executed_at": "2026-04-01T09:05:30+00:00",
  "execution_status": "succeeded",
  "receipt": {
    "transaction_hash": "0xtx-success",
    "block_number": 22222222,
    "gas_used": 210000,
    "status": 1,
    "logs": [],
    "effective_gas_price_wei": 12000000000,
    "revert_reason": null
  }
}
```

### 异常模型
```text
ExecutionPlanError
RuntimeGateError
RuntimeTriggerError
ReceiptConsistencyError
ExecutionAdapterError
```

## 3. 约束
- 不允许：
  - 在 `onchain_checks_passed=False` 时发起链上调用
  - 在 execution layer 内做自由决策、重新编译或替代状态机
  - 传入不匹配的 `trade_intent_id`
- 仅允许：
  - 消费已编译计划
  - 消费 runtime trigger
  - 通过显式 executor 端口执行
  - 返回 / 导出结构化 `ExecutionRecord`
- 单位与精度约定：
  - `gas_used`、`block_number`、`effective_gas_price_wei` 保持链上原始整数
  - `triggered_at`、`executed_at` 必须为带时区的 UTC datetime
- 空值 / 默认值约定：
  - `logs` 默认空列表
  - `metadata` 默认空对象
  - `effective_gas_price_wei`、`revert_reason` 可为空
  - 缺失 `trade_intent_id` 或 `register_payload.intent_id` 时抛 `ExecutionPlanError`

## 4. 示例
- sample request：`execute_runtime_trigger(execution_plan=..., runtime_trigger=..., executor=...)`
- sample response：返回 `ExecutionRecord`；`model_dump(mode="json")` 已验证可被 `export_outputs` 消费
- sample failure：
  - `onchain_checks_passed=False` -> `RuntimeGateError`
  - `trade_intent_id` 不匹配 -> `RuntimeTriggerError`
  - executor 缺少 `execute_reactive_trigger(...)` -> `ExecutionAdapterError`

## 5. 未完成项
- TODO：知识库尚未冻结细粒度 `RuntimeTrigger` schema
- TODO：知识库尚未冻结正式 `ExecutionRecord` schema
- 临时 workaround：executor 当前既可返回 `ChainReceipt`，也可返回可被 `ChainReceipt.model_validate(...)` 接受的 dict
- 风险提示：
  - 真实链上 adapter 与真实回执尚未验证
  - 当前仓库没有 git 提交历史，无法引用稳定 commit 作为 handoff 锚点
