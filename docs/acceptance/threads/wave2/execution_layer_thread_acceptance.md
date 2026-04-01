# 线程内验收清单
- 模块 / prompt：`execution_layer` / `docs/prompts/execution_layer.prompt.md`
- Wave：`wave2`
- 线程负责人：`not verified yet`
- 分支：`master`
- commit：`not verified yet`
- 改动目录：`backend/execution/runtime`
- 是否只改允许路径：`yes`（模块实现位于 `backend/execution/runtime/`；本次仅回填 `docs/acceptance/`）

## A. 职责边界
- 模块目标职责是否完成：`yes, with notes`；当前实现可消费 `runtime trigger`，在运行时门禁通过后调用执行端口，并返回带链上回执的 `ExecutionRecord`
- 是否引入了不属于本模块的逻辑：`no`；未加入自由决策、重新编译或状态机替代逻辑
- 是否修改了共享 schema / 契约：`yes`；新增了模块内的 `RuntimeTrigger`、`ChainReceipt`、`ExecutionRecord` 和执行端口协议
- 若有修改，是否同步通知依赖线程：`not verified yet`

## B. Contract 对齐
- 是否逐条对齐 implementation contract：`yes, with notes`
- 已对齐项：
  - 输入为 `compiled execution plan`、`runtime trigger`、`on-chain checks passed`
  - 输出为 `ExecutionRecord`
  - 仅通过显式 adapter / interface 执行链上调用
- 未满足项：
  - 仓库内未发现真实链上 executor 适配器或端到端链上验证证据
  - `docs/knowledge/01_core/02_domain_models.md` 未给出正式 `ExecutionRecord` schema，当前实现保留最小字段并留有 `TODO`
  - `docs/knowledge/04_execution/02_execution_layer.md` 未定义细粒度 `runtime trigger` schema，当前实现只保留闭环所需字段
- 明确拒绝实现的项：自由决策、重新编译、替代状态机

## C. Invariants 检查
- JSON 仍是唯一执行真相：`不适用`；本模块不直接产出 `machine_truth_json`，但已验证 `ExecutionRecord` 可被 `export_outputs` 消费
- Audit 是否只做摘抄：`不适用`
- Investment Memo 是否未污染执行真相：`不适用`
- 是否仍然只信 RPC 作为执行真相：`yes`；从代码看仅消费 runtime trigger 与链上回执，不依赖第三方索引 API
- Execution Compiler 是否只在注册时工作：`yes`；`runtime/` 未实现任何 compile 逻辑
- Reactive 是否未承载自由决策：`yes`
- Shadow Monitor 是否保持独立：`not verified yet`
- 是否在校验通过后立即 swap：`no`；必须先收到 `Reactive trigger` 且 `onchain_checks_passed=True`

## D. 验证证据
- 运行的命令：
  - `git diff --name-only HEAD`，结果：失败，当前仓库没有可用 `HEAD`
  - `git log --oneline -n 10`，结果：失败，当前分支 `master` 尚无提交历史
  - `git branch --show-current`，结果：`master`
  - `git status --short`，结果：整个仓库当前均为未跟踪状态，无法仅通过 git 历史隔离模块改动
  - `python -m unittest -v backend/execution/runtime/test_execution_layer.py`，结果：通过，4 个测试全部 `ok`
- 测试结果：`passed`
- 样例输入：`StubExecutionPlan(trade_intent_id, register_payload.intent_id)` + `RuntimeTrigger(trigger_id, trade_intent_id, trigger_source, triggered_at, onchain_checks_passed, metadata)` + `ChainReceipt(...)`
- 样例输出：`ExecutionRecord(trade_intent_id, intent_id, trigger_id, trigger_source, triggered_at, executed_at, execution_status, receipt)`
- 截图 / 日志 / 链上真实回执路径：`not verified yet`

## E. Known gaps
- TODO：细粒度 `runtime trigger` schema 仍未在 knowledge files 中定义
- TODO：正式 `ExecutionRecord` domain schema 仍未在 knowledge files 中定义
- TODO：真实链上 executor / RPC 集成未在当前线程中提供
- 风险：当前仓库没有提交历史，无法从 git 证明“最近提交”与“diff against HEAD”
- 风险：当前仅有模块级单元测试，没有真实链上或跨模块集成测试证据

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 进入线程间对接：`可以`
