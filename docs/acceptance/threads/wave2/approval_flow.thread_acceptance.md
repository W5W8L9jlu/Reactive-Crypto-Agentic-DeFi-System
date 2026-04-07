# approval_flow 线程内验收清单

- 模块 / prompt：`approval_flow` / `docs/prompts/approval_flow.prompt.md`
- Wave：`wave2`
- 线程负责人：`not verified yet`
- 分支：`w1-gate-fail-fix`
- commit：`not verified yet`；当前模块文件仍为未提交工作树状态
- 改动目录：
  - `backend/cli/views/approval_battle_card.py`
  - `backend/cli/approval/`
  - `backend/execution/compiler/`
- 是否只改允许路径：否（本次为已确认的跨模块修复；根因在 `execution_compiler`）

## A. 职责边界
- 本模块目标职责是否完成：是。`show_approval` 默认人话战报、`raw=True` 返回 machine truth、`approve/reject` 分流和 TTL 过期阻断均有实现与测试。
- 是否引入了不属于本模块的逻辑：未发现。未新增 machine truth 生成、未新增链上执行逻辑。
- 是否修改了共享 schema / 契约：是。恢复了 `execution_compiler` 冻结模型与导出，以修复 `approval_flow` 导入阻塞。
- 若修改，是否同步通知依赖线程：是，已在 handoff 文档写明恢复后的接口面。

## B. Contract 对齐
- 是否逐条对齐 implementation contract：是。
- 已对齐项：
  - 默认不展示 raw JSON
  - `--raw` 路径显示 machine truth
  - 输入对象：`TradeIntent`、`ExecutionPlan`、`ValidationResult`、`DecisionMeta`
  - 输出对象：`ApprovalBattleCard` 与 `approve/reject action`
  - TTL 过期禁止审批
  - 战报由结构化对象映射，不由 LLM 自由生成
- 未满足项：
  - CLI route / adapter 端到端接线：not verified yet
- 明确拒绝实现项：
  - machine truth 生成
  - 执行编译逻辑迁入审批模块
  - 链上执行

## C. Invariants 检查
- JSON 仍是唯一执行真相：是；`show_approval(raw=True)` 仅透传 `machine_truth_json`
- Audit 是否只做摘抄：不适用；本模块不生成 audit
- Investment Memo 是否未污染执行真相：不适用；本模块不生成 memo
- 是否仍然只信 RPC 作为执行真相：不适用；本模块不做 provider / RPC 拉取
- Execution Compiler 是否只在注册时工作：是；恢复后的 compiler 仍是注册期编译与冻结
- Reactive 是否未承载自由决策：是；审批模块仅做显示与人工分流
- Shadow Monitor 是否保持独立：不适用；本模块未接 monitor 执行

## D. 验证证据
- 运行的命令：
  - `python -m unittest backend.execution.compiler.test_execution_compiler -v` -> `2 tests OK`
  - `python -m unittest backend.validation.test_validation_engine -v` -> `6 tests OK`
  - `python -m unittest backend.export.test_export_outputs -v` -> `4 tests OK`
  - `python -m unittest backend.cli.approval.test_approval_flow -v` -> `5 tests OK`
  - Python 内联命令调用 `show_approval(...)` -> 成功输出 battle card 文本
- 测试结果：
  - compiler：通过
  - validation：通过
  - export：通过
  - approval_flow：通过
- 样例输入（来自 `backend/cli/approval/test_approval_flow.py`）：
  - `TradeIntent(trade_intent_id="trade-001", pair="ETH/USDC", dex="uniswap-v3", ttl_seconds=300, ...)`
  - `RegisterPayload(intentId="intent-001", entryAmountOutMinimum=1450000000, ...)`
  - `DecisionMeta(trade_intent_id="trade-001", created_at="2026-04-03T10:00:00Z", ttl_seconds=300)`
- 样例输出（实测）：
  - `Approval Battle Card`
  - `TTL Remaining: 5m 0s`
  - `Approve: allowed`
- 截图/日志/回执路径：`not verified yet`

## E. Known gaps
- TODO：
  - CLI route / adapter 级端到端接线验证
  - 清理 `backend/cli/models.py` 与 `backend/cli/approval/flow.py` 的 battle card 映射双实现风险
- Blockers：无
- 假设：
  - 当前未提交代码为本线程交付快照
- 风险：
  - 由于尚未提交，`commit` 级锚点暂不可用

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 进入线程间对接：可以
