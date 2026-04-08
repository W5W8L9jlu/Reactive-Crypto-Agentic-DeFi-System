# 线程验收清单
- 模块 / prompt: `shadow_monitor` / `docs/prompts/shadow_monitor.prompt.md`
- Wave: `wave4`
- 线程负责人: `not verified yet`
- 分支: `codex/wave4`
- HEAD commit: `4297287`
- 模块相关历史 commit: `not verified yet`
- 改动目录: `backend/monitor`
- 是否只改允许路径: `是（模块实现仅在 backend/monitor）`

## A. Scope
- 已实现最小守护闭环：
  - 独立轮询守护（`ReconciliationDaemon`）
  - ActivePosition + 备用 RPC 周期对账（`ShadowMonitor.reconcile_positions`）
  - 阈值击穿后 Grace Period（warning）与超时升级（critical）
  - 输出 `force_close_recommendations`（建议动作，不执行链上）
- 非目标能力未实现：
  - 正常执行链路
  - 日常决策

## B. Contract 对齐
- 与 `docs/contracts/shadow_monitor.contract.md` 对齐情况：
  - 仅在 `backend/monitor` 交付：`是`
  - 输入消费 `ActivePosition intents` + `backup RPC quotes/state`：`是`
  - 输出 `alerts` + `force-close recommendation`：`是`
  - Hard invariants（独立运行/只看不摸/备用 RPC/Grace Period）：`是`

## C. Invariants 检查
- 独立于 Reactive 运行：`是（通过 source/rpc port 注入）`
- 只看不摸，除非报警：`是（仅产出告警与建议对象）`
- 使用备用 RPC 对账：`是（BackupRPCPort.get_position_snapshot）`
- 有 Grace Period 且避免与正常回调竞争：`是（先 warning，超时才 critical）`

## D. 验收证据（当前分支）
- `git diff --name-only HEAD`：
  - `backend/contracts/core/ReactiveInvestmentCompiler.sol`
- `git status --short --branch`：
  - `## codex/wave4`
  - `?? backend/monitor/`
- `git ls-files --others --exclude-standard -- backend/monitor docs/acceptance`：
  - `backend/monitor/shadow_monitor.py`
  - `backend/monitor/reconciliation_daemon.py`
- 运行验证：
  - `python -m py_compile backend/monitor/shadow_monitor.py backend/monitor/reconciliation_daemon.py`（成功，退出码 0）
  - 内联验证脚本（`python -`）输出：`shadow_monitor_contract_checks: OK`

## E. Known Gaps
- 模块代码尚未提交到 git 历史：`not verified yet`
- 独立测试文件（如 `backend/monitor/test_*.py`）: `not verified yet`
- 与 CLI `AlertView` 字段映射的跨线程联调：`not verified yet`
- 额外损失估算公式的跨模块冻结契约：`not verified yet`

## F. 结论
- 线程状态：`IMPLEMENTED_IN_WORKTREE`
- 是否可进入线程间对接：`可以（以当前工作树接口为准）`
- 是否可作为“已提交基线”交付：`not verified yet`

