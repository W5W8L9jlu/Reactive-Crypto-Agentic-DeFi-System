# 线程交付说明

- 模块: `reactive_runtime`
- Wave: `wave2`
- 分支: `master`
- commit: `not verified yet`
- 交付日期: `2026-04-01`

## 1. 本次交付内容
- 新增最小 Reactive runtime adapter 闭环
- 新增模块内 schema:
  - `ReactiveExecutionPlan`
  - `ReactiveRegisterPayload`
  - `ReactiveExecutionHardConstraints`
  - `ReactiveTrigger`
  - `ReactivePositionState`
  - `InvestmentStateMachineIntent`
- 新增状态机 port:
  - `register_investment_intent(intent_id, intent)`
  - `execute_reactive_trigger(intent_id, observed_out, runtime_exit_min_out)`
  - `get_position_state(intent_id)`
- 新增 runtime 行为:
  - 注册 plan 并适配为状态机可消费的 intent
  - 校验 callback 与当前状态兼容
  - 将 `entry` / `stop_loss` / `take_profit` 触发转发到状态机
- 新增模块级单元测试 3 个场景

## 2. 已核实的模块文件
- `backend/reactive/adapters/__init__.py`
- `backend/reactive/adapters/errors.py`
- `backend/reactive/adapters/models.py`
- `backend/reactive/adapters/runtime.py`
- `backend/reactive/adapters/README.md`
- `backend/reactive/adapters/test_reactive_runtime.py`

## 3. 未交付内容
- 真实链上状态机 adapter: `not delivered`
- callback 来源认证机制: `not delivered`
- 真实 RPC / 合约联调证据: `not delivered`
- 跨模块集成测试: `not delivered`

## 4. 实际执行过的命令
- `git diff --name-only HEAD`
  - 结果: 失败, 当前仓库无 `HEAD`
- `git log --oneline -n 10`
  - 结果: 失败, 当前分支尚无提交
- `git branch --show-current`
  - 结果: `master`
- `git status --short`
  - 结果: 仓库整体为未跟踪初始化状态
- `python -m unittest backend.reactive.adapters.test_reactive_runtime -v`
  - 结果: `Ran 3 tests ... OK`
- `python -m unittest discover -s backend/reactive/adapters -p 'test_*.py' -v`
  - 结果: `Ran 3 tests ... OK`

## 5. 下游影响
- 下游只能依赖显式 adapter contract，不应假设 runtime 会做:
  - 自由决策
  - 策略评估
  - `runtime_exit_min_out` 链下补算
  - callback 来源认证以外的额外安全判断
- 下游状态机 adapter 需要实现 `InvestmentPositionStateMachinePort`
- 若后续要补真实链上集成，应保持:
  - `PendingEntry -> ActivePosition -> Closed`
  - `entry` 只能发生在 `PendingEntry`
  - `stop_loss/take_profit` 只能发生在 `ActivePosition`

## 6. 备注
- 由于仓库没有首个 commit，本交付说明无法引用稳定 commit hash
- 变更文件的 git 归属和“最近提交”信息均为 `not verified yet`
