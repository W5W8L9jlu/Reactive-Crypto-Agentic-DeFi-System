# pre_registration_check 线程交付说明

## 基本信息
- 模块名：`pre_registration_check`
- Wave：`wave2`
- 分支：`w1-gate-fail-fix`
- module commit：`not verified yet`

## 本次交付做了什么
- 在 [pre_registration_check.py](/D:/reactive-crypto-agentic-DeFi-system/backend/validation/pre_registration_check.py) 交付了注册前检查的强类型输入/输出对象：
  - `RPCStateSnapshot`
  - `PreRegistrationCheckResult`
  - `PreRegistrationCheckObservations`
  - `AbortReason`
- 交付了显式错误模型：
  - `GasTooHighError`
  - `ExpiredIntentError`
  - `InsufficientBalanceError`
  - `InsufficientAllowanceError`
  - `SlippageExceededError`
  - `UnprofitableRegistrationError`
  - `HealthFactorTooLowError`
  - `MissingPreRegistrationSpecError`
- 交付了两个入口：
  - `run_pre_registration_check`
  - `run_pre_registration_check_or_raise`
- 当前代码快照覆盖了 reserve/slippage/balance/allowance/gas/TTL/profit 可行性判断。

## 修改了哪些文件
- 模块实现文件：
  - `backend/validation/pre_registration_check.py`
- `git diff --name-only HEAD` 还包含大量与本模块无关的文件；本交付说明只认上面这一条模块实现文件。

## 没做什么
- 没有新增专门的 repo 测试文件
- 没有接入真实 RPC provider
- 没有验证 precheck -> compiler 的端到端消费
- 没有实现运行时 require 检查
- 没有实现触发后重新决策

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git branch --show-current
git status --short -- backend/validation/pre_registration_check.py docs/acceptance
Get-ChildItem -Recurse -File backend | Where-Object { $_.Name -match 'pre_registration_check|pre-registration-check' } | Select-Object FullName
python -m py_compile backend/validation/pre_registration_check.py
@'
from backend.validation.pre_registration_check import run_pre_registration_check
print(run_pre_registration_check)
'@ | python -
```

## 验收证据
- `python -m py_compile backend/validation/pre_registration_check.py` -> 成功，无输出
- 运行时 smoke -> 失败：
  - `ImportError: cannot import name 'RegisterPayload' from 'backend.execution.compiler.models'`
  - 当前阻塞发生在 `backend.validation.__init__ -> .models -> backend.execution.compiler.models`
- 专门测试文件搜索 -> 未发现 `pre_registration_check` 专门测试文件

## 对下游线程的影响
- 新增可消费对象：
  - `RPCStateSnapshot`
  - `PreRegistrationCheckResult`
  - `PreRegistrationCheckObservations`
  - `AbortReason`
- 新增显式错误模型：
  - `PreRegistrationCheckDomainError` 及其子类
- 下游需要同步的点：
  - 必须显式提供 `expected_profit_usd`、`max_gas_price_gwei`、`ttl_buffer_seconds` 等快照字段
  - 不要把 precheck 输出当作 runtime require 或重新决策入口
  - 当前工作树里包级导入受上游 `execution_compiler.models` 状态影响，端到端接线前需要先清理这个阻塞
