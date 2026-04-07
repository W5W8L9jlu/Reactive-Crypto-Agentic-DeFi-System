# 线程间对接单

- 上游线程: `execution_compiler`
- 下游线程: `not verified yet`
- Wave: `wave2`
- handoff 日期: `2026-04-03`
- 当前分支: `w1-gate-fail-fix`
- 当前 HEAD: `c5afba2`
- 模块相关历史 commit: `1211b50`

## 1. 上游已经稳定的东西
- 编译入口与合约输入冻结：
  - `compile_execution_plan(context: CompilationContext) -> ExecutionPlan`
  - `freeze_contract_call_inputs(plan: ExecutionPlan) -> ContractRegisterCallInputs`
- 稳定对象：
  - `RegisterPayload`、`ExecutionHardConstraints`、`ExecutionPlan`
  - `ChainStateSnapshot`、`CompilerConfig`、`CompilationContext`、`RegistrationContext`
- 稳定错误：
  - `ExecutionCompilerError`、`CompilationInputError`、`ChainStateError`、`ConstraintViolationError`、`TokenPrecisionError`、`CompilationConfigError`

## 2. 下游必须按此消费
### 输入对象（CompilationContext）
```json
{
  "strategy_intent": "StrategyIntent",
  "trade_intent": "TradeIntent",
  "registration_context": {
    "intent_id": "str",
    "owner": "str",
    "input_token": "str",
    "output_token": "str"
  },
  "chain_state": {
    "base_fee_gwei": "int >= 0",
    "max_priority_fee_gwei": "int >= 0",
    "block_number": "PositiveInt",
    "block_timestamp": "int",
    "input_token_decimals": "0..18",
    "output_token_decimals": "0..18",
    "input_output_price": "Decimal",
    "input_token_usd_price": "Decimal"
  },
  "config": {
    "gas_buffer_multiplier": "Decimal > 1",
    "max_gas_price_cap_gwei": "int >= 0",
    "ttl_buffer_seconds": "int >= 0",
    "slippage_tolerance_buffer_bps": "int >= 0"
  }
}
```

### 输出对象（ExecutionPlan + 合约输入）
```json
{
  "trade_intent_id": "str",
  "register_payload": {
    "intentId": "str",
    "owner": "str",
    "inputToken": "str",
    "outputToken": "str",
    "plannedEntrySize": "int",
    "entryAmountOutMinimum": "int",
    "entryValidUntil": "int",
    "maxGasPriceGwei": "int",
    "stopLossSlippageBps": "int",
    "takeProfitSlippageBps": "int",
    "exitMinOutFloor": "int"
  },
  "hard_constraints": {
    "max_slippage_bps": "int",
    "ttl_seconds": "PositiveInt",
    "stop_loss_bps": "int",
    "take_profit_bps": "int"
  }
}
```

### 异常模型
```text
ExecutionCompilerError
CompilationInputError
ChainStateError
ConstraintViolationError
TokenPrecisionError
CompilationConfigError
```

## 3. 约束
- 不允许：
  - 在本模块生成 calldata
  - 将 `DecisionMeta.ttl_seconds` 作为注册到期真相来源
  - 隐式推断 `registration_context` 与 `chain_state` 字段
- 仅允许：
  - 在注册时编译并冻结合约面 inputs
  - 使用 `freeze_contract_call_inputs(...)` 作为 register 调用适配
- 单位与精度约定:
  - `entryAmountOutMinimum` / `maxGasPriceGwei` / `entryValidUntil` / `stopLossSlippageBps` / `takeProfitSlippageBps` / `exitMinOutFloor` 的字段名与语义在 `HEAD` 模型注释中可见
  - `input_output_price`、`gas_buffer_multiplier` 使用 `Decimal`
  - `ttl_seconds`、`*_bps`、`*_gwei`、timestamps 使用整数
- 空值 / 默认值约定:
  - `CompilerConfig` 在 `HEAD` 中有默认值
  - 其余编译 happy path 的缺省行为: `not verified yet`

## 4. 示例
- sample request：已在当前工作区通过内联顺序调用验证（见 W2 gate / exit 证据）
- sample response：`plan_ok: intent-001 1710000540 100000000000000000000`
- sample failure：
  - `ConstraintViolationError` 当 `exitMinOutFloor >= entryAmountOutMinimum`

## 5. 未完成项
- TODO：
  - 执行 `execution_compiler -> reactive_runtime` 的真实 handoff
  - 补充跨模块端到端验证路径（非单模块职责）
- 当前风险：
  - Gate 仍依赖 dirty 工作树证据，需在干净提交上冻结
