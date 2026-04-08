# 线程验收清单
- 模块 / prompt: `reactive_runtime` / `docs/prompts/reactive_runtime.prompt.md`
- Wave: `wave3`
- 线程负责人: `not verified yet`
- 分支: `w3-reactive-runtime`
- HEAD commit: `b920945`
- 模块相关历史 commit: `not verified yet`
- 改动目录: `backend/reactive/adapters`
- 是否只改允许路径: `是（当前实现文件均在 backend/reactive/adapters）`

## A. Scope
- 已实现最小闭环：
  - `entry` 触发
  - `stop_loss` / `take_profit` 触发
  - callback 执行结果校验
- 运行时入口：
  - `run_reactive_runtime_or_raise(...)`
  - `run_reactive_runtime(...)`
- 状态机对接方式：
  - 通过 `InvestmentStateMachinePort`（`get_position_state` / `execute_entry_callback` / `execute_exit_callback`）

## B. Contract 对齐
- 与 `docs/contracts/reactive_runtime.contract.md` 对齐情况：
  - 仅在 `backend/reactive/adapters/` 交付：`是`
  - 输入消费 `registered investment intent` + `reactive trigger`：`是`
  - 输出 `entry/exit callback execution`：`是`
  - 非目标（投资建议/策略评估/链下兜底决策）：`未实现`

## C. Invariants 检查
- Reactive 只做事件驱动与 callback，不做自由决策：`是`
- 入场/出场经由状态机：`是`
- 保留 callback 验证：`是（回调类型与状态迁移双校验）`
- 触发时不做重新编译：`是（模块内无编译逻辑）`

## D. 验收证据（当前分支）
- `git diff --name-only HEAD`：空输出（无 tracked diff）
- `git status --short --branch`：`?? backend/reactive/`
- `git ls-files --others --exclude-standard -- backend/reactive/adapters`：
  - `backend/reactive/adapters/__init__.py`
  - `backend/reactive/adapters/errors.py`
  - `backend/reactive/adapters/models.py`
  - `backend/reactive/adapters/runtime.py`
  - `backend/reactive/adapters/test_reactive_runtime.py`
- 测试：
  - 命令：`$env:PYTHONPATH='.'; python -m unittest backend.reactive.adapters.test_reactive_runtime -v`
  - 结果：`Ran 5 tests ... OK`

## E. Known Gaps
- 模块代码尚未提交到 git 历史：`not verified yet`
- 与真实 Investment State Machine 合约适配（非 fake state machine）: `not verified yet`
- 与 execution_layer 的端到端联调：`not verified yet`
- callback 对链上回执/日志结构约束：`not verified yet`

## F. 结论
- 线程状态：`IMPLEMENTED_IN_WORKTREE`
- 是否可进入线程间对接：`可以（以当前工作树接口为准）`
- 是否可作为“已提交基线”交付：`not verified yet`
