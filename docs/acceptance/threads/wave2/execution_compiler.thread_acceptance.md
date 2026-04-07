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
- 当前 `HEAD` 下已提交到 git 的模块内容只有 schema / error 层:
  - `backend/execution/compiler/errors.py`
  - `backend/execution/compiler/models.py`
- 当前工作树额外存在:
  - `backend/execution/compiler/__init__.py`
  - `backend/execution/compiler/compiler.py`
  - `backend/execution/compiler/test_execution_compiler.py`
- 但上述额外文件在当前工作树中均为 quarantine 注释说明，不构成可执行的 registration-time compile happy path。
- 因此，当前分支状态下可核实的交付范围是:
  - error model
  - `ExecutionPlan` / `RegisterPayload` / `ChainStateSnapshot` / `CompilerConfig` 的 schema 草图
- 当前分支状态下不可核实的交付范围:
  - `compile_execution_plan(...)` 的活跃实现
  - `freeze_contract_call_inputs(...)` 的活跃实现
  - 运行中的模块级 happy path

## B. Contract 对齐
- 与 `docs/contracts/execution_compiler.contract.md` 的对齐情况:
  - `ExecutionPlan`、`RegisterPayload`、`entryAmountOutMinimum`、`entryValidUntil`、`maxGasPriceGwei`、`stopLossSlippageBps`、`takeProfitSlippageBps`、`exitMinOutFloor` 在 `HEAD` 的 `models.py` 中可见: `是`
  - 注册时链状态 `ChainStateSnapshot` 与编译配置 `CompilerConfig` 在 `HEAD` 可见: `是`
  - 已提交且可执行的 compile entrypoint: `not verified yet`
  - 已提交且可执行的 contract-facing register payload freeze: `not verified yet`
  - Definition of Done 中要求的 registration-time compile happy path: `not verified yet`
- 与 W2 wave 文档的对齐情况:
  - `docs/acceptance/05_prefilled_wave_packets/W2_验收包.md` 将 `execution_compiler` 列为 Wave 2 模块: `是`
  - `HEAD` 的 `W2.wave_gate` / `W2.wave_exit_report` 将 `execution_compiler` 标记为 `execution_compiler -> reactive_runtime` 仅做 schema 对比、未真实 handoff: `是`

## C. Invariants 检查
- 编译只发生在注册时: `仅 contract / knowledge 层要求可见，代码级 not verified yet`
- AI 不生成 calldata: `是`
  - 说明: `HEAD` 模型只停留在结构化 payload / plan 层，未见 calldata 编码逻辑
- 入场是绝对约束；出场是相对 slippage BPS: `是（schema / 字段语义层）`
- 失败快速抛异常，不做局部吞异常: `部分可见`
  - 说明: `HEAD` 中存在显式 error classes，但实际抛出路径 `not verified yet`
- 触发时重新编译不存在: `not verified yet`
  - 说明: 当前工作树的 `compiler.py` 已被 quarantine 注释，`HEAD` 中也没有已提交的活跃编译实现

## D. 验收证据
- `git diff --name-only HEAD`
  - 结果: 当前工作树存在大量跨模块差异；`execution_compiler` 相关文件包含:
    - tracked diff: `backend/execution/compiler/errors.py`, `backend/execution/compiler/models.py`
    - untracked: `backend/execution/compiler/__init__.py`, `backend/execution/compiler/compiler.py`, `backend/execution/compiler/test_execution_compiler.py`
- `git log --oneline -n 10`
  - 结果:
    - `c5afba2 docs: 更新Wave2验收与交接文档`
    - `1211b50 feat: 实现Wave2执行层与验收文档回填`
- `git ls-tree -r --name-only HEAD backend/execution/compiler`
  - 结果:
    - `backend/execution/compiler/errors.py`
    - `backend/execution/compiler/models.py`
- `git show --stat --summary 1211b50 -- backend/execution/compiler`
  - 结果: 仅创建了 `errors.py` 与 `models.py`
- `git show HEAD:backend/execution/compiler/compiler.py`
  - 结果: `fatal: path ... exists on disk, but not in 'HEAD'`
- `git show HEAD:backend/execution/compiler/test_execution_compiler.py`
  - 结果: `fatal: path ... exists on disk, but not in 'HEAD'`
- `python -m compileall backend/execution/compiler`
  - 结果: success；编译了 `__init__.py`、`compiler.py`、`errors.py`、`models.py`、`test_execution_compiler.py`

## E. Known gaps
- 当前 `HEAD` 没有已提交的 `compiler.py` / `__init__.py` / `test_execution_compiler.py`
- 当前工作树中的额外模块文件已被 quarantine 注释，不可作为 active baseline
- `execution_compiler -> reactive_runtime` 在 `HEAD` 的 W2 wave 文档中仍明确为:
  - `only schema-compared`
  - `not actually handed off`
- 模块级 happy path 测试: `not verified yet`
- contract-facing register call input freeze: `not verified yet`

## F. 可交付结论
- 状态: `not verified yet`
- 进入线程间对接: `不可以`
