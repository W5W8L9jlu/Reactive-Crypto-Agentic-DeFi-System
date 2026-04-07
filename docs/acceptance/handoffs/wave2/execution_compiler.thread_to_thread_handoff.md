# 线程间对接单

- 上游线程: `execution_compiler`
- 下游线程: `not verified yet`
- Wave: `wave2`
- handoff 日期: `2026-04-03`
- 当前分支: `w1-gate-fail-fix`
- 当前 HEAD: `c5afba2`
- 模块相关历史 commit: `1211b50`

## 1. 上游已经稳定的东西
- 仅有 schema / error 层在 `HEAD` 中可核实:
  - `backend/execution/compiler/errors.py`
  - `backend/execution/compiler/models.py`
- `HEAD` 中可核实的对象:
  - `RegisterPayload`
  - `ExecutionHardConstraints`
  - `ExecutionPlan`
  - `ChainStateSnapshot`
  - `CompilerConfig`
  - `CompilationContext`
- `HEAD` 中可核实的错误:
  - `ExecutionCompilerError`
  - `CompilationInputError`
  - `ChainStateError`
  - `ConstraintViolationError`
  - `TokenPrecisionError`
  - `CompilationConfigError`
- 当前工作树中虽然存在:
  - `backend/execution/compiler/__init__.py`
  - `backend/execution/compiler/compiler.py`
  - `backend/execution/compiler/test_execution_compiler.py`
  但这三者均为未跟踪 quarantine 文件，不属于稳定 handoff 面。

## 2. 下游必须按此消费

### 输入对象
`HEAD` 中仅能核实 schema-level 输入，不存在已提交 compile entrypoint：

```json
{
  "strategy_intent": "StrategyIntent",
  "trade_intent": "TradeIntent",
  "chain_state": {
    "base_fee_gwei": "int >= 0",
    "max_priority_fee_gwei": "int >= 0",
    "block_number": "PositiveInt",
    "block_timestamp": "int",
    "input_token_decimals": "0..18",
    "output_token_decimals": "0..18",
    "input_output_price": "Decimal"
  },
  "config": {
    "gas_buffer_multiplier": "Decimal > 1",
    "max_gas_price_cap_gwei": "int >= 0",
    "ttl_buffer_seconds": "int >= 0",
    "slippage_tolerance_buffer_bps": "int >= 0"
  }
}
```

### 输出对象
`HEAD` 中仅能核实 schema-level 输出，不存在已提交 compile entrypoint：

```json
{
  "trade_intent_id": "str",
  "register_payload": {
    "intent_id": "str",
    "owner": "str",
    "input_token": "str",
    "output_token": "str",
    "planned_entry_size": "int",
    "entry_amount_out_minimum": "int",
    "entry_valid_until": "int",
    "max_gas_price_gwei": "int",
    "stop_loss_slippage_bps": "int",
    "take_profit_slippage_bps": "int",
    "exit_min_out_floor": "int"
  },
  "hard_constraints": {
    "max_slippage_bps": "int",
    "ttl_seconds": "PositiveInt",
    "stop_loss_bps": "int",
    "take_profit_bps": "int"
  },
  "compiled_at": "datetime",
  "compiler_version": "str"
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
- 不允许:
  - 把当前工作树中的 `compiler.py` / `__init__.py` / `test_execution_compiler.py` 当成稳定交付面
  - 假设 `HEAD` 已冻结 `compile_execution_plan(...)`
  - 假设 `HEAD` 已冻结 contract-facing register call input adapter
  - 假设 `execution_compiler -> reactive_runtime` 已完成真实 handoff
- 仅允许:
  - 在明确说明“schema-level only”的前提下消费 `HEAD` 中的 model / error 定义
  - 继续以 contract / knowledge 中的 registration-time compiler invariants 作为设计约束
- 单位与精度约定:
  - `entryAmountOutMinimum` / `maxGasPriceGwei` / `entryValidUntil` / `stopLossSlippageBps` / `takeProfitSlippageBps` / `exitMinOutFloor` 的字段名与语义在 `HEAD` 模型注释中可见
  - `input_output_price`、`gas_buffer_multiplier` 使用 `Decimal`
  - `ttl_seconds`、`*_bps`、`*_gwei`、timestamps 使用整数
- 空值 / 默认值约定:
  - `CompilerConfig` 在 `HEAD` 中有默认值
  - 其余编译 happy path 的缺省行为: `not verified yet`

## 4. 示例
- sample request: `not verified yet`
  - 原因: `HEAD` 中不存在已提交的 compile entrypoint
- sample response: `not verified yet`
  - 原因: `HEAD` 中不存在已提交的 compile happy path 输出
- sample failure:
  - error class 名称可核实
  - 实际抛出路径与触发条件: `not verified yet`

## 5. 未完成项
- TODO:
  - 提交并冻结活跃的 compile entrypoint
  - 提交并冻结 contract-facing register payload freeze
  - 以已提交测试证明 registration-time compile happy path
  - 执行 `execution_compiler -> reactive_runtime` 真实 handoff
- 当前风险:
  - `W2_验收包` 将本模块列为 Wave 2 模块，但 `HEAD` 的 W2 gate / exit / handoff 只把它记为 `schema-compared` seam
  - 当前工作树包含 quarantine 文件，容易与 `HEAD` 上的稳定面混淆
