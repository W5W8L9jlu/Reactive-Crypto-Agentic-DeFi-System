# cli_surface 线程交付说明

## 基本信息
- 模块名：`cli_surface`
- Prompt 文件：`not verified yet`
- Wave：`wave2`
- 负责人：`not verified yet`
- 分支：`master`
- commit：`not verified yet`

## 本次交付做了什么
- 交付了六组命令面的路由目录：`strategy / decision / approval / execution / export / monitor`。
- 交付了 CLI 展示层对象和文本视图，包含 `ApprovalBattleCard`、`MonitorAlertView`、审批视图渲染、alert 视图渲染。
- 交付了显式 adapter seam、枚举冻结和错误模型，确保 CLI 不回承业务计算。

## 修改了哪些文件
- `git diff --name-only HEAD`：`not verified yet`；仓库当前没有 `HEAD`。
- 当前模块交付快照文件：
  - `backend/cli/app.py`
  - `backend/cli/views.py`
  - `backend/cli/models.py`
  - `backend/cli/alerts.py`
  - `backend/cli/errors.py`
  - `backend/cli/__init__.py`
  - `backend/cli/README.md`
  - `backend/cli/tests/test_cli_surface.py`

## 没做什么
- 没有接入任何真实业务 adapter。
- 没有在 CLI 内实现 provider logic、状态机逻辑、业务核心计算。
- 没有验证真实 `Typer` / `Rich` CLI 运行；当前环境缺少依赖。

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git branch --show-current
git status --short --untracked-files=all -- backend/cli docs/acceptance
$env:PYTHONDONTWRITEBYTECODE='1'; pytest backend/cli/tests/test_cli_surface.py -q -p no:cacheprovider
@'
... python inline render for ApprovalBattleCard and MonitorAlertView ...
'@ | python -
```

## 验收证据
- 测试截图：`not verified yet`
- 日志：
  - `git diff --name-only HEAD` -> 失败：`fatal: ambiguous argument 'HEAD'`
  - `git log --oneline -n 10` -> 失败：当前分支 `master` 尚无提交
  - `pytest ...` -> `7 passed in 0.51s`
- 示例 payload：
  - 审批输入样例来自 `backend/cli/tests/test_cli_surface.py`：`trade_intent_id=ti_001`, `pair=ETH/USDC`, `ttl_remaining_display=2m 30s`
  - alert 输入样例：`alert_id=alert_001`, `severity=critical`, `grace_state=expired`
- 示例输出：
  - `Approval Battle Card / Pair: ETH/USDC / TTL: 2m 30s / Actionable: yes`
  - `Monitor Alerts / [CRITICAL] alert_001 / Manual Action: manual action required`

## 对下游线程的影响
- 新增输入对象：
  - `CliAdapters`
  - `ApprovalBattleCard`
  - `MonitorAlertView`
- 新增输出对象：
  - 审批文本视图
  - alert 文本视图
  - route metadata：`CommandGroup` / `CommandRoute`
- 新增异常：
  - `CliSurfaceDomainError`
  - `MissingCliAdapterError`
  - `MissingCliDependencyError`
  - `UnresolvedCliRouteError`
- 新增命令/入口：
  - `strategy show`
  - `decision run`
  - `approval show|approve|reject`
  - `execution show`
  - `export render --kind <machine_truth_json|audit_markdown|investment_memo>`
  - `monitor alerts|takeover`
- 需要下游同步更新的点：
  - 所有 CLI 命令必须通过显式 adapter 接入，不能要求 CLI 自行补业务行为。
  - `approval --raw` 只用于显示 `machine_truth_ref`；下游不要把 raw payload 暴露责任推回 CLI。
