# pre_registration_check 线程测试证据

## 测试目标
- 确认 `pre_registration_check` 实现文件至少满足语法可编译
- 确认仓库内是否存在专门测试文件
- 尝试做最小运行时 smoke，检查模块是否能通过当前包路径被导入

## 覆盖的场景
- 语法检查：
  - `backend/validation/pre_registration_check.py` 可被 `py_compile`
- 仓库结构检查：
  - 是否存在 `pre_registration_check` 专门测试文件
- 运行时 smoke：
  - 通过 `backend.validation.pre_registration_check` 包路径导入模块
  - 顺序执行 `run_pre_registration_check_or_raise(...)` 与 `compile_execution_plan(...)`

## 命令
```bash
$env:PYTHONPATH='.'; Get-ChildItem -Recurse -File backend | Where-Object { $_.Name -match 'pre_registration_check|pre-registration-check' } | Select-Object FullName
$env:PYTHONPATH='.'; python -m py_compile backend/validation/pre_registration_check.py
@'
from backend.validation.pre_registration_check import run_pre_registration_check, run_pre_registration_check_or_raise
from backend.execution.compiler.models import ChainStateSnapshot, CompilerConfig, RegistrationContext, CompilationContext
from backend.execution.compiler.compiler import compile_execution_plan
from backend.strategy.models import StrategyIntent, TradeIntent
from decimal import Decimal

si = StrategyIntent(strategy_intent_id="si_001", template_id="tpl_001", template_version=1, execution_mode="conditional")
ti = TradeIntent(trade_intent_id="ti_001", strategy_intent_id="si_001", pair="ETH/USDC", dex="uniswap_v3", position_usd=Decimal("100"), max_slippage_bps=200, stop_loss_bps=300, take_profit_bps=800, entry_conditions=["price<=2000"], ttl_seconds=600)

rpc = {
  "block_number": 123,
  "block_timestamp": 1710000000,
  "input_token_usd_price": Decimal("1"),
  "input_token_reserve": Decimal("100000"),
  "output_token_reserve": Decimal("50"),
  "wallet_input_balance": Decimal("500"),
  "wallet_input_allowance": Decimal("500"),
  "base_fee_gwei": 20,
  "max_priority_fee_gwei": 2,
  "max_gas_price_gwei": 50,
  "estimated_gas_used": 200000,
  "native_token_usd_price": Decimal("3000"),
  "expected_profit_usd": Decimal("50"),
  "ttl_buffer_seconds": 60
}

r = run_pre_registration_check_or_raise(strategy_intent=si, trade_intent=ti, rpc_state_snapshot=rpc)
print("precheck_allowed:", r.is_allowed, "ttl_remaining:", r.observations.remaining_ttl_seconds if r.observations else None)

cs = ChainStateSnapshot(base_fee_gwei=20, max_priority_fee_gwei=2, block_number=123, block_timestamp=1710000000, input_token_decimals=18, output_token_decimals=6, input_output_price=Decimal("0.0005"), input_token_usd_price=Decimal("1"))
rc = RegistrationContext(intent_id="intent-001", owner="0xowner", input_token="0xIn", output_token="0xOut")
ctx = CompilationContext(strategy_intent=si, trade_intent=ti, chain_state=cs, registration_context=rc, config=CompilerConfig())
plan = compile_execution_plan(ctx)
print("plan_ok:", plan.register_payload.intent_id, plan.register_payload.entry_valid_until, plan.register_payload.planned_entry_size)
'@ | python -
```

## 输入
- 文件搜索输入：`backend/**`
- 语法检查输入：`backend/validation/pre_registration_check.py`
- 运行时 smoke 输入：`backend.validation.pre_registration_check`

## 输出
- 文件搜索输出：
  - `backend/validation/pre_registration_check.py`
- 语法检查输出：无输出，exit code 0
- 运行时 smoke 输出：
  - `precheck_allowed: True ttl_remaining: 540`
  - `plan_ok: intent-001 1710000540 100000000000000000000`

## 实际结果
- 通过：
  - `python -m py_compile backend/validation/pre_registration_check.py`
  - 包路径导入与顺序 `precheck -> compile` 运行时 smoke
- 未覆盖：
  - dedicated unit tests：`not verified yet`
  - gas / TTL / allowance / balance / slippage / profitability 的自动化断言：`not verified yet`

## 备注
- 当前 repo 中未发现 `pre_registration_check` 专门测试文件。
- 当前证据表明：
  - 模块 import 成功，abort-path 与顺序 happy path 可复现
  - 与编译器的冻结适配器未定义，后续需要明确归属
