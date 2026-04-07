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
  - precheck 输出是否已被 compiler 稳定消费：`not verified yet`

## C. Invariants 检查
- 执行前检查是否仍然只信 RPC：是
- 是否仍然不生成最终 calldata：是
- 是否仍然不承载运行时最终防守：是
- 是否保留显式 abort reason：是
- 是否存在静默 fallback：未发现

## D. 验证证据
- 已运行命令：
  - `git diff --name-only HEAD`
    - 结果：输出包含 `backend/validation/pre_registration_check.py`，同时还有大量与本模块无关的改动
  - `git log --oneline -n 10`
    - 结果：当前仅看到 2 条最近提交，均未能从 commit message 直接确认是本模块提交
  - `git branch --show-current`
    - 结果：`w1-gate-fail-fix`
  - `git status --short -- backend/validation/pre_registration_check.py docs/acceptance`
    - 结果：`backend/validation/pre_registration_check.py` 为修改态；`docs/acceptance/` 下存在大量无关修改/删除
  - `Get-ChildItem -Recurse -File backend | Where-Object { $_.Name -match 'pre_registration_check|pre-registration-check' } | Select-Object FullName`
    - 结果：只看到 `backend/validation/pre_registration_check.py` 与其 `__pycache__`，未发现专门测试文件
  - `python -m py_compile backend/validation/pre_registration_check.py`
    - 结果：成功，无输出
  - `@' from backend.validation.pre_registration_check import run_pre_registration_check; print(run_pre_registration_check) '@ | python -`
    - 结果：失败，导入 `backend.validation.pre_registration_check` 时触发 `ImportError`；根因是 `backend.validation.__init__` 继续导入 `.models`，而当前工作树中的 `backend.execution.compiler.models` 已被 quarantine，缺少 `RegisterPayload`

## E. Known gaps
- `backend/validation/test_pre_registration_check.py`：`not verified yet`；当前 repo 未发现专门测试文件
- 通过包路径导入模块的运行时 smoke：失败，受上游导入链阻塞
- 与 `execution_compiler` 的端到端对接：`not verified yet`
- `expected_profit_usd`、`max_gas_price_gwei`、`ttl_buffer_seconds` 由哪个上游模块提供：`not verified yet`
- `health_factor` 阈值来源与默认策略：`not verified yet`

## F. 可交付结论
- 状态：`PARTIAL`
- 说明：
  - 单文件实现与 contract 基本对齐
  - 语法级检查通过
  - 当前工作树下的包级运行时导入被上游 `execution_compiler.models` 隔离状态阻塞，因此线程运行时可交付性不能标记为完全通过
