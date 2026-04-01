# cli_surface 线程间对接单

- 上游线程：`cli_surface`
- 下游线程：所有需要接入 CLI adapter 的后续线程
- Wave：`wave2`
- handoff 日期：`2026-04-01`
- 上游 commit：`not verified yet`

## 1. 上游已经稳定的东西
- 接口：
  - `resolve_route(path: Sequence[str]) -> CommandRoute`
  - `build_app(adapters: CliAdapters | None = None, console: Any | None = None) -> Any`
  - `render_approval_battle_card_text(card, show_raw=False) -> str`
  - `render_monitor_alerts_text(alerts) -> str`
- 对象：
  - `CliAdapters`
  - `CommandGroup`
  - `CommandRoute`
  - `ApprovalBattleCard`
  - `DecisionMeta`
  - `MonitorAlertView`
- 枚举：
  - `ExportArtifactKind = machine_truth_json | audit_markdown | investment_memo`
  - `ApprovalAction = approve | reject`
  - `RiskLevel = low | medium | high`
  - `MonitorAlertSeverity = warning | critical`
- 命令：
  - `strategy show`
  - `decision run`
  - `approval show`
  - `approval approve`
  - `approval reject`
  - `execution show`
  - `export render --kind ...`
  - `monitor alerts`
  - `monitor takeover`
- 文件路径：
  - `backend/cli/app.py`
  - `backend/cli/models.py`
  - `backend/cli/alerts.py`
  - `backend/cli/views.py`
  - `backend/cli/errors.py`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "strategy_show": "() -> str | view object",
  "decision_run": "() -> str | view object",
  "approval_show": "() -> ApprovalBattleCard",
  "approval_approve": "() -> str | view object",
  "approval_reject": "() -> str | view object",
  "execution_show": "() -> str | view object",
  "export_render": "(kind: ExportArtifactKind) -> str | rendered payload",
  "monitor_alerts": "() -> list[MonitorAlertView]",
  "monitor_takeover": "() -> str | view object"
}
```

### 输出对象
```json
{
  "approval_show": "Approval Battle Card text view",
  "monitor_alerts": "Monitor Alerts text view",
  "other_routes": "str(result) fallback",
  "none_result": "TODO: adapter returned no CLI view."
}
```

### 异常模型
```text
CliSurfaceDomainError
MissingCliAdapterError
MissingCliDependencyError
UnresolvedCliRouteError
```

## 3. 约束
- 不允许：
  - 在 CLI 内补业务核心计算
  - 在 CLI 内补 provider logic
  - 在 CLI 内补状态机逻辑
  - 让 CLI 自由生成 machine truth payload
- 仅允许：
  - 路由
  - 展示
  - 人工审批/运维入口
  - 通过显式 schema / interface / adapter 接入下游
- 单位与精度约定：
  - `ApprovalBattleCard` 中展示字段如 `position_usd_display`、`max_slippage_display` 由结构化对象提供或由当前模型内的轻量展示函数生成
  - CLI 不重新定义链上单位和业务精度规则
- 空值 / 默认值约定：
  - 缺失 adapter -> `MissingCliAdapterError`
  - 缺失 `Typer` / `Rich` -> `MissingCliDependencyError`
  - 未知命令路径 -> `UnresolvedCliRouteError`
  - adapter 返回 `None` -> 文本 `TODO: adapter returned no CLI view.`
  - `approval show --raw` 只影响展示，不把 `show_raw` 继续传给上游 adapter

## 4. 示例
- sample request：
  - 用户命令：`approval show`
  - 路由请求：`("approval", "show")`
- sample response：
  - `Approval Battle Card`
  - `Trade Intent: ti_001`
  - `Pair: ETH/USDC`
  - `TTL: 2m 30s`
  - `Actionable: yes`
- sample failure：
  - `resolve_route(("monitor", "unknown"))`
  - 抛出：`UnresolvedCliRouteError: Unsupported CLI route: monitor unknown`

## 5. 未完成项
- TODO：
  - 为九个命令入口接好真实 adapter
  - 安装并验证 `Typer` / `Rich`
  - 做真实 CLI 命令级集成验证
- 临时 workaround：
  - 当前可直接复用 `resolve_route()`、`render_approval_battle_card_text()`、`render_monitor_alerts_text()` 做下游接线前验证
- 风险提示：
  - 由于仓库当前没有提交历史，无法通过 commit/HEAD 提供稳定版本锚点
  - 当前 handoff 基于代码快照，不代表端到端 CLI 已验证
