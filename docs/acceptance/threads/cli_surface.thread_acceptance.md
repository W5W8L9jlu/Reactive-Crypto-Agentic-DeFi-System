# cli_surface 线程内验收清单

- 模块 / prompt：`cli_surface` / `not verified yet`
- Wave：`wave2`
- 线程负责人：`not verified yet`
- 分支：`master`
- commit：`not verified yet`；`git log --oneline -n 10` 返回当前分支尚无提交
- 改动目录：`backend/cli/`
- 是否只改允许路径：是；当前模块实现快照仅见于 `backend/cli/`

## A. 职责边界
- 本模块的目标职责是否完成：基本完成。当前快照提供了 `strategy / decision / approval / execution / export / monitor` 六组命令面、审批/告警文本视图、显式 adapter seam 和 CLI 错误模型。
- 是否引入了不属于本模块的逻辑：未发现。`backend/cli/app.py` 只做路由、依赖加载、adapter 调用和结果渲染；缺失行为统一报错或 `TODO`。
- 是否修改了共享 schema / 契约：否；当前检查范围内未发现跨模块 schema 改写。
- 若修改，是否同步通知依赖线程：不适用。

## B. Contract 对齐
- 是否逐条对齐 implementation contract：是，带说明。
- 未满足项：
  - `Typer` / `Rich` 真实 CLI 运行未验证；当前环境缺少这两个依赖。
  - prompt 文件未核对，记为 `not verified yet`。
  - git commit / git diff against `HEAD` 无法提供，因为仓库当前没有 `HEAD`。
- 明确拒绝实现的项（若有）：
  - 未为缺失 adapter 的命令补业务逻辑，统一抛 `MissingCliAdapterError`。
  - 未在 CLI 内实现 provider logic、状态机逻辑、业务核心计算。

## C. Invariants 检查
- JSON 仍是唯一执行真相：是；CLI 当前只展示 `ApprovalBattleCard` 和 alert 视图，`--raw` 仅暴露 `machine_truth_ref`，不构造新的执行真相。
- Audit 是否只做摘抄：不适用；当前模块只冻结 `ExportArtifactKind` 三轨枚举，不生成 audit 内容。
- Investment Memo 是否未污染执行真相：是；仅作为 `export render --kind investment_memo` 的枚举入口存在。
- 是否仍然只信 RPC 作为执行真相：不适用；当前模块未接入 provider / RPC 读取。
- Execution Compiler 是否只在注册时工作：不适用；当前模块未实现 compiler 逻辑。
- Reactive 是否未承载自由决策：是；当前模块没有任何自动决策逻辑。
- Shadow Monitor 是否保持独立：是；CLI 仅定义 `monitor alerts` / `monitor takeover` 展示与入口，不承载 monitor 运行逻辑。

## D. 验证证据
- 运行的命令：
  - `git diff --name-only HEAD` -> 失败：`fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.`
  - `git log --oneline -n 10` -> 失败：`fatal: your current branch 'master' does not have any commits yet`
  - `git branch --show-current` -> 输出：`master`
  - `git status --short --untracked-files=all -- backend/cli docs/acceptance` -> 无输出
  - `$env:PYTHONDONTWRITEBYTECODE='1'; pytest backend/cli/tests/test_cli_surface.py -q -p no:cacheprovider` -> `7 passed in 0.51s`
  - Python 内联渲染命令 -> 成功输出审批视图和 alert 视图片段
- 测试结果：
  - 命令路由测试：通过
  - 审批显示测试：通过
  - alert 视图测试：通过
- 样例输入：
  - 路由：`("approval", "show")`
  - Battle card：`trade_intent_id=ti_001`, `pair=ETH/USDC`, `ttl_remaining_display=2m 30s`
  - Alert：`alert_id=alert_001`, `severity=critical`, `grace_state=expired`
- 样例输出：
  - 审批视图：
    - `Approval Battle Card`
    - `Pair: ETH/USDC`
    - `TTL: 2m 30s`
    - `Actionable: yes`
  - alert 视图：
    - `Monitor Alerts`
    - `[CRITICAL] alert_001`
    - `Manual Action: manual action required`
- 截图/日志/回执路径：`not verified yet`

## E. Known gaps
- TODO：
  - 为九个命令入口接入显式 `CliAdapters`。
  - 安装并验证 `Typer` / `Rich` 运行时。
  - 若后续需要真实导出内容，必须通过显式 adapter 接入，不能在 CLI 内计算。
- Blockers：
  - 当前环境缺少 `Typer` / `Rich`，无法直接验证 `build_app()` 和真实命令调用。
  - 仓库当前无提交历史，无法从 `git diff HEAD` / `git log` 回溯精确变更集。
- 假设：
  - 当前 `backend/cli/` 快照即本线程交付物。
  - 下游会通过显式 adapter 提供 `ApprovalBattleCard`、`MonitorAlertView` 或其他已定义对象。
- 风险：
  - 运行时依赖未安装时，CLI 构建将抛 `MissingCliDependencyError`。
  - 未接 adapter 的命令默认失败并退出，当前仍属“可接线骨架”而非端到端 CLI。

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 进入线程间对接：可以；但需携带上述依赖与 adapter 未接线说明
