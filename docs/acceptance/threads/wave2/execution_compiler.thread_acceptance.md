# 线程验收清单
- 模块 / prompt: `execution_compiler`
- Wave: `wave2`
- 线程负责人: `not verified yet`
- 分支: `w1-gate-fail-fix`
- HEAD commit: `c5afba2`
- 模块相关历史 commit:
  - `1211b50 feat: 实现Wave2执行层与验收文档回填`
  - `c5afba2 docs: 更新Wave2验收与交接文档`
- 改动目录: `backend/execution/compiler`
- 是否只改允许路径: `not verified yet`
  - 说明: 当前工作树包含大量与本模块无关的改动；仅从模块目录看，`git diff --name-only HEAD -- backend/execution/compiler` 命中了 `errors.py`、`models.py`，另有 `__init__.py`、`compiler.py`、`test_execution_compiler.py` 为未跟踪文件。

## A. 职责边界
- 已提交并可执行的编译入口与冻结映射：
  - `backend/execution/compiler/compiler.py` 提供 `compile_execution_plan(...)` 与 `freeze_contract_call_inputs(...)`
- 已提交并可验证的模型：
  - `backend/execution/compiler/models.py` 中的 `ExecutionPlan`、`RegisterPayload`、`ContractRegisterCallInputs`、`ContractInvestmentIntent`、`ChainStateSnapshot`、`CompilerConfig`、`CompilationContext`、`RegistrationContext`
- 模块职责：
  - 在注册时编译 `TradeIntent` + `ChainStateSnapshot` + `RegistrationContext` + `CompilerConfig` 为 `ExecutionPlan.register_payload`
  - 通过 `freeze_contract_call_inputs(...)` 产出合约面向的 `registerInvestmentIntent` 输入

## B. Contract 对齐
- 与 `docs/contracts/execution_compiler.contract.md` 的对齐情况:
  - `ExecutionPlan`、`RegisterPayload`、`entryAmountOutMinimum`、`entryValidUntil`、`maxGasPriceGwei`、`stopLossSlippageBps`、`takeProfitSlippageBps`、`exitMinOutFloor`：`是`
  - `ChainStateSnapshot`、`CompilerConfig`、`CompilationContext`、`RegistrationContext`：`是`
  - 编译入口已提交且可执行：`是`
  - contract-facing register payload freeze 已提交且可执行：`是`
  - registration-time compile happy path：`通过`

## C. Invariants 检查
- 编译只发生在注册时：`是`
- AI 不生成 calldata：`是`
- 入场是绝对约束；出场是相对 slippage BPS：`是`
- 失败快速抛异常，不做局部吞异常：`是（`ConstraintViolationError` 等）`
- 触发时重新编译不存在：`是`

## D. 验收证据
- 当前工作区复跑：
  - `python -m unittest backend.execution.compiler.test_execution_compiler -v` -> `2 tests OK`
  - `python -m unittest backend.validation.test_validation_engine -v` -> `6 tests OK`
  - `python -m unittest backend.export.test_export_outputs -v` -> `4 tests OK`
  - 内联顺序调用 -> `plan_ok: intent-001 1710000540 100000000000000000000`

## E. Known gaps
- 与 `reactive_runtime` 的实际 handoff：`not verified yet`
- 跨模块单命令端到端链路：`not verified yet`

## F. 可交付结论
- 状态: `ACCEPTED`
- 进入线程间对接: `可以`
