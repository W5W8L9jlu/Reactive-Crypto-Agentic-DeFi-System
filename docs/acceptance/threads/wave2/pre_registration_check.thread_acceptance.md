# pre_registration_check 线程内验收清单

- 模块 / contract：`pre_registration_check` / `docs/contracts/pre_registration_check.contract.md`
- Wave：`wave2`
- 分支：`w1-gate-fail-fix`
- 最近提交：
  - `c5afba2 docs: 更新Wave2验收与交接文档`
  - `1211b50 feat: 实现Wave2执行层与验收文档回填`
- 改动目录：`backend/validation/`
- 模块实现改动文件（从 `git diff --name-only HEAD` 可见）：`backend/validation/pre_registration_check.py`

## A. 职责边界
- 当前代码快照在 [pre_registration_check.py](/D:/reactive-crypto-agentic-DeFi-system/backend/validation/pre_registration_check.py) 中实现了：
  - `RPCStateSnapshot`
  - `PreRegistrationCheckResult`
  - `PreRegistrationCheckObservations`
  - `run_pre_registration_check`
  - `run_pre_registration_check_or_raise`
- 已覆盖的注册前检查项：
  - reserve / slippage
  - balance / allowance
  - gas / expected profit
  - TTL
  - 可选 `health_factor`
- 未发现本文件内引入运行时 require 检查或触发后重新决策逻辑。

## B. Contract 对齐
- 输入对齐：是。代码入口接收 `StrategyIntent`、`TradeIntent`、`RPCStateSnapshot`。
- 输出对齐：是。代码返回 `PreRegistrationCheckResult`，包含 `is_allowed`、`abort_reason`、`observations`。
- Hard invariants 对齐：
  - 注册前检查只信 RPC：是；当前只消费 `RPCStateSnapshot`。
  - 必须校验 Gas / Expected Profit：是；当前显式校验 gas cap 和 gas cost 覆盖率。
  - 只负责注册时可行性：是；未实现运行时状态机或 require 防守。
  - 失败快速抛异常：是；`run_pre_registration_check_or_raise` 直接抛显式 domain error。
- 未完全验证项：
  - 与真实 RPC provider 的接线：`not verified yet`
  - 与编译器的直接适配器 contract：`not verified yet`

## C. Invariants 检查
- 执行前检查是否仍然只信 RPC：是
- 是否仍然不生成最终 calldata：是
- 是否仍然不承载运行时最终防守：是
- 是否保留显式 abort reason：是
- 是否存在静默 fallback：未发现

## D. 验证证据
- 已运行命令（当前工作区）：
  - `$env:PYTHONPATH='.'; pytest backend/data/fetchers/test_aggregated_fetchers.py backend/data/context_builder/test_context_builder.py -q`
    - 结果：`14 passed, 2 warnings`
  - `python -m unittest backend.execution.compiler.test_execution_compiler -v`
    - 结果：`2 tests OK`
  - `python -m unittest backend.validation.test_validation_engine -v`
    - 结果：`6 tests OK`
  - `python -m unittest backend.export.test_export_outputs -v`
    - 结果：`4 tests OK`
  - `python -m unittest backend.cli.approval.test_approval_flow -v`
    - 结果：`5 tests OK`
  - `from backend.validation.pre_registration_check import run_pre_registration_check`
    - 结果：import smoke `passed`
  - 内联 Python 顺序调用：
    - `run_pre_registration_check_or_raise(...)` -> `is_allowed=True`, `remaining_ttl_seconds=540`
    - `compile_execution_plan(...)` -> `intentId='intent-001'`, `entryValidUntil=1710000540`, `plannedEntrySize=100000000000000000000`

## E. Known gaps
- `backend/validation/test_pre_registration_check.py`：`not verified yet`；当前 repo 未发现专门测试文件
- 与 `execution_compiler` 的直接适配器 contract：`not verified yet`
- `expected_profit_usd`、`max_gas_price_gwei`、`ttl_buffer_seconds` 的上游权威来源：`not verified yet`
- `health_factor` 阈值来源与默认策略：`not verified yet`

## F. 可交付结论
- 状态：`DELIVERED WITH NOTES`
- 说明：
  - 实现与 contract 对齐，import smoke 通过
  - 中止路径与顺序 `precheck -> compile` 的 happy path 在当前工作区可复现
  - 仍缺少直连编译器的冻结适配器与专门测试文件
