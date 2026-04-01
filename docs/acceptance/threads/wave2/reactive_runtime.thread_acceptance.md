# 线程内验收清单

- 模块 / prompt: `reactive_runtime` / `docs/contracts/reactive_runtime.contract.md`
- Wave: `wave2`
- 线程负责人: `not verified yet`
- 分支: `master`
- commit: `not verified yet`
- 改动目录: `backend/reactive/adapters/`
- 是否只改允许路径: `yes` for module implementation; 本次文档回填仅改 `docs/acceptance/`

## A. 职责边界
- 模块目标职责是否完成: `yes, with notes`
  - 已实现 `register_execution_plan(...)` 和 `handle_trigger(...)`
  - 已支持 `entry` / `stop_loss` / `take_profit` 三类触发
  - 已通过状态机端口完成注册与触发执行
- 是否引入不属于本模块的逻辑: `no`
  - 未实现自由决策
  - 未实现策略评估
  - 未实现链下兜底决策
  - 未实现重新编译执行计划
- 是否修改共享 schema / 合约: `no`
  - 新增的是模块内 adapter schema 和状态机 port
- 若有共享接口变更是否已通知下游: `not verified yet`

## B. Contract 对齐
- 是否逐条对齐 implementation contract: `yes, with notes`
- 已对齐项:
  - 输入对象覆盖 `registered investment intent` 和 `reactive trigger`
  - 输出行为为状态机注册调用与 entry/exit callback 执行
  - 保持 Reactive 只负责事件驱动与 callback
  - 入场与出场均经由状态机端口
  - 保留 callback 验证
- 未满足球项:
  - knowledge/contract 未定义 callback 来源认证机制，当前只校验注册绑定与状态兼容
  - 未提供真实链上状态机 adapter，实现停留在 port/interface 层
- 明确拒绝实现的项:
  - 投资建议
  - 策略评估
  - 链下兜底决策

## C. Invariants 检查
- JSON 仍是唯一执行真相: `not verified yet`
  - 本模块不直接产出 `machine_truth_json`
- Audit 是否只做摘抄: `not applicable`
- Investment Memo 是否未污染执行真相: `not applicable`
- 是否仍然只信 RPC 作为执行真相: `not verified yet`
  - 当前模块未接入真实 RPC 或链上客户端
- Execution Compiler 是否只在注册时工作: `yes`
  - `runtime.py` 未实现任何 compile 逻辑，只消费已注册 plan
- Reactive 是否未承载自由决策: `yes`
- Shadow Monitor 是否保持独立: `not verified yet`
- 入场与出场是否都经由状态机: `yes`
- 是否保留 callback 验证: `yes`

## D. 验证证据
- 运行的命令:
  - `git diff --name-only HEAD`
    - 结果: 失败
    - 输出: `fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.`
  - `git log --oneline -n 10`
    - 结果: 失败
    - 输出: `fatal: your current branch 'master' does not have any commits yet`
  - `git branch --show-current`
    - 结果: 成功
    - 输出: `master`
  - `git status --short`
    - 结果: 成功
    - 输出显示整个仓库当前为未跟踪初始化状态，例如 `?? backend/`、`?? docs/`
  - `python -m unittest backend.reactive.adapters.test_reactive_runtime -v`
    - 结果: 通过
    - 输出: `Ran 3 tests ... OK`
  - `python -m unittest discover -s backend/reactive/adapters -p 'test_*.py' -v`
    - 结果: 通过
    - 输出: `Ran 3 tests ... OK`
- 测试结果: `passed`
- 样例输入:
  - `ReactiveExecutionPlan(register_payload.intent_id, entry_amount_out_minimum, exit_min_out_floor, hard_constraints)`
  - `ReactiveTrigger(intent_id, kind, observed_out, runtime_exit_min_out)`
- 样例输出:
  - `register_investment_intent(intent_id, InvestmentStateMachineIntent(...))`
  - `execute_reactive_trigger(intent_id, observed_out, runtime_exit_min_out)`
- 截图 / 日志 / 链上真实回执路径: `not verified yet`

## E. Known gaps
- TODO: callback 来源认证机制未在 knowledge/contract 中定义，`runtime.py` 保留 `TODO(domain)`
- TODO: 未接入真实链上状态机 adapter 或 RPC 客户端
- 假设: `entry` 触发转发时使用 `runtime_exit_min_out=0`
- 风险: 当前只有模块级单元测试，没有真实链上或跨模块联调证据
- 风险: 仓库没有 commit 历史，无法从 git 证明“最近提交”或“相对 HEAD 的 diff”

## F. 可交付结论
- 状态: `PASS_WITH_NOTES`
- 进入线程间对接: `可以`
