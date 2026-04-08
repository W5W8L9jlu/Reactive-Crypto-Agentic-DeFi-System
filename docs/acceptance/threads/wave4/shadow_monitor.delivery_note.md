# 线程交付说明

## 基本信息
- 模块名: `shadow_monitor`
- Prompt 文件: `docs/prompts/shadow_monitor.prompt.md`
- Wave: `wave4`
- 负责人: `not verified yet`
- 分支: `codex/wave4`
- HEAD commit: `4297287`

## 本次交付做了什么
- 交付了 `backend/monitor` 的最小守护闭环：
  - `ShadowMonitor`：对账、Grace Period、critical 升级、force-close recommendation 产出
  - `ReconciliationDaemon`：独立周期轮询（active position source + backup rpc）
  - 强类型模型与边界约束（Pydantic v2，timezone-aware 时间）

## 模块实现文件（当前工作树）
- `backend/monitor/shadow_monitor.py`
- `backend/monitor/reconciliation_daemon.py`

## 未交付项
- 已提交 commit 锚点：`not verified yet`
- 模块独立单测文件：`not verified yet`
- 真实下游（CLI/执行层）联调证据：`not verified yet`
- 额外损失估算公式的正式契约冻结：`not verified yet`

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status --short --branch
git diff --name-status HEAD
git ls-files --others --exclude-standard -- backend/monitor docs/acceptance
python -m py_compile backend/monitor/shadow_monitor.py backend/monitor/reconciliation_daemon.py
python -  # shadow_monitor_contract_checks 内联脚本
```

## 命令结果摘要
- `git diff --name-only HEAD`：仅显示 `backend/contracts/core/ReactiveInvestmentCompiler.sol`
- `git log --oneline -n 10`：最近提交未出现 `shadow_monitor` 提交锚点
- `git status --short --branch`：`## codex/wave4`，且 `?? backend/monitor/`
- `git ls-files --others --exclude-standard -- backend/monitor docs/acceptance`：
  - `backend/monitor/shadow_monitor.py`
  - `backend/monitor/reconciliation_daemon.py`
- `python -m py_compile ...`：成功（退出码 0）
- 内联验证脚本：输出 `shadow_monitor_contract_checks: OK`

## 对下游影响
- 下游可按以下接口接入：
  - `ShadowMonitor.reconcile_positions(...) -> ShadowMonitorResult`
  - `ReconciliationDaemon.run_cycle() -> ReconciliationDaemonCycle`
- 下游不可假设当前模块已形成 commit-level 冻结基线（当前是工作树证据）。

