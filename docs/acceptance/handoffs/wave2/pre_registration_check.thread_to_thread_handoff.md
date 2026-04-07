# pre_registration_check 线程间对接单

- 上游线程：`pre_registration_check`
- 建议下游线程：`execution_compiler` 及所有需要消费注册前可行性结果的线程
- Wave：`wave2`
- handoff 日期：`2026-04-03`
- 上游 commit：`not verified yet`

## 1. 当前代码快照中已经稳定的东西
- 入口：
  - `run_pre_registration_check -> PreRegistrationCheckResult`
  - `run_pre_registration_check_or_raise -> PreRegistrationCheckResult`
- 输入对象：
  - `RPCStateSnapshot`
  - `StrategyIntent`
  - `TradeIntent`
- 输出对象：
  - `PreRegistrationCheckResult`
  - `PreRegistrationCheckObservations`
  - `AbortReason`
- 错误模型：
  - `PreRegistrationCheckDomainError`
  - `MissingPreRegistrationSpecError`
  - `StrategyIntentBindingError`
  - `GasTooHighError`
  - `SlippageExceededError`
  - `ExpiredIntentError`
  - `InsufficientBalanceError`
  - `InsufficientAllowanceError`
  - `UnprofitableRegistrationError`
  - `HealthFactorTooLowError`

## 2. 下游必须按此消费
### 输入 shape
```json
{
  "strategy_intent": "StrategyIntent",
  "trade_intent": "TradeIntent",
  "rpc_state_snapshot": {
    "block_number": "PositiveInt",
    "block_timestamp": "PositiveInt",
    "input_token_usd_price": "Decimal > 0",
    "input_token_reserve": "Decimal > 0",
    "output_token_reserve": "Decimal > 0",
    "wallet_input_balance": "Decimal >= 0",
    "wallet_input_allowance": "Decimal >= 0",
    "base_fee_gwei": "int >= 0",
    "max_priority_fee_gwei": "int >= 0",
    "max_gas_price_gwei": "int >= 0",
    "estimated_gas_used": "PositiveInt",
    "native_token_usd_price": "Decimal > 0",
    "expected_profit_usd": "Decimal >= 0",
    "ttl_buffer_seconds": "int >= 0",
    "health_factor": "Decimal | null",
    "minimum_health_factor": "Decimal | null"
  }
}
```

### 输出 shape
```json
{
  "is_allowed": "bool",
  "checked_at": "datetime",
  "strategy_intent_id": "str | null",
  "trade_intent_id": "str | null",
  "checked_objects": [
    "StrategyIntent",
    "TradeIntent",
    "RPCStateSnapshot"
  ],
  "observations": "PreRegistrationCheckObservations | null",
  "abort_reason": {
    "code": "str",
    "message": "str",
    "field_path": "str | null"
  }
}
```

## 3. 约束
- 不允许：
  - 在此模块内做运行时 require 检查
  - 在此模块内做触发后重新决策
  - 静默 fallback 缺失快照字段
- 仅允许：
  - 基于 RPC 快照做注册前可行性判断
  - 返回结构化结果或抛显式 domain error
- 当前代码快照里的判断项：
  - reserve / slippage
  - balance / allowance
  - gas cap
  - expected profit 覆盖 gas cost
  - TTL buffer
  - 可选 health factor

## 4. 示例
- sample request（shape only，运行时未完全验证）：
```json
{
  "strategy_intent": {
    "strategy_intent_id": "si_001",
    "template_id": "tpl_001",
    "template_version": 1,
    "execution_mode": "conditional"
  },
  "trade_intent": {
    "trade_intent_id": "ti_001",
    "strategy_intent_id": "si_001",
    "pair": "ETH/USDC",
    "dex": "uniswap_v3",
    "position_usd": "100",
    "max_slippage_bps": 200,
    "stop_loss_bps": 300,
    "take_profit_bps": 800,
    "entry_conditions": ["price <= 2000"],
    "ttl_seconds": 600
  },
  "rpc_state_snapshot": {
    "block_number": 123,
    "block_timestamp": 1710000000,
    "input_token_usd_price": "1",
    "input_token_reserve": "100000",
    "output_token_reserve": "50",
    "wallet_input_balance": "500",
    "wallet_input_allowance": "500",
    "base_fee_gwei": 20,
    "max_priority_fee_gwei": 2,
    "max_gas_price_gwei": 50,
    "estimated_gas_used": 200000,
    "native_token_usd_price": "3000",
    "expected_profit_usd": "50",
    "ttl_buffer_seconds": 60
  }
}
```
- sample response（shape only，运行时未完全验证）：
```json
{
  "is_allowed": true,
  "strategy_intent_id": "si_001",
  "trade_intent_id": "ti_001",
  "abort_reason": null
}
```
- sample failure：
```text
GasTooHighError
ExpiredIntentError
InsufficientBalanceError
InsufficientAllowanceError
SlippageExceededError
UnprofitableRegistrationError
```

## 5. 剩余问题
- 当前工作树中的 `backend.execution.compiler.models` 已被 quarantine，导致通过 `backend.validation` 包路径做运行时 smoke 时出现导入阻塞
- `pre_registration_check` 专门测试文件：`not verified yet`
- 下游 compiler 是否已经稳定消费 `PreRegistrationCheckResult`：`not verified yet`
- `expected_profit_usd`、`max_gas_price_gwei`、`ttl_buffer_seconds` 的上游提供者和冻结来源：`not verified yet`
