# cli_surface 线程测试证据

## 测试目标
- 验证 `cli_surface` 是否冻结了六组最小命令面与九个基础入口。
- 验证审批显示和 alert 视图是否满足最小可追溯展示要求。

## 覆盖的场景
- happy path：
  - 六组命令面注册成功
  - 九个入口可通过 `resolve_route()` 定位
  - 审批视图能渲染 `ApprovalBattleCard`
  - alert 视图能渲染 `MonitorAlertView`
- failure path：
  - 未知命令路径抛 `UnresolvedCliRouteError`
- edge case：
  - `approval show` 默认不显示 `machine_truth_ref`
  - `approval show --raw` 才显示 `machine_truth_ref`
  - export 仅允许三种 artifact kind

## 输入
```json
{
  "command_groups": [
    "strategy",
    "decision",
    "approval",
    "execution",
    "export",
    "monitor"
  ],
  "approval_card_sample": {
    "trade_intent_id": "ti_001",
    "pair": "ETH/USDC",
    "dex": "uniswap-v3",
    "ttl_remaining_display": "2m 30s",
    "machine_truth_ref": "mt:ti_001"
  },
  "alert_sample": {
    "alert_id": "alert_001",
    "severity": "critical",
    "source": "shadow_monitor",
    "grace_state": "expired",
    "requires_manual_action": true
  }
}
```

## 输出
```json
{
  "resolved_routes": 9,
  "unknown_route_error": "UnresolvedCliRouteError",
  "export_artifact_kinds": [
    "machine_truth_json",
    "audit_markdown",
    "investment_memo"
  ],
  "approval_show_default_hides_machine_truth_ref": true,
  "approval_show_raw_exposes_machine_truth_ref": true,
  "alert_view_marks_manual_action_required": true
}
```

## 命令
```bash
$env:PYTHONDONTWRITEBYTECODE='1'; pytest backend/cli/tests/test_cli_surface.py -q -p no:cacheprovider
@'
... python inline render for ApprovalBattleCard and MonitorAlertView ...
'@ | python -
```

## 实际结果
- 通过：
  - `pytest backend/cli/tests/test_cli_surface.py -q -p no:cacheprovider` -> `7 passed in 0.51s`
  - Python 内联渲染成功输出：
    - `Approval Battle Card`
    - `Pair: ETH/USDC`
    - `TTL: 2m 30s`
    - `Monitor Alerts`
    - `[CRITICAL] alert_001`
    - `Manual Action: manual action required`
- 失败：
  - 本次记录的功能测试命令无失败
  - `git diff --name-only HEAD` 与 `git log --oneline -n 10` 失败；原因是仓库当前无 `HEAD` / 无提交历史
- 未覆盖：
  - 真实 `Typer` / `Rich` CLI app 构建与命令调用
  - 缺失 adapter 时 `typer.Exit(code=2)` 的进程级行为
  - 真实导出内容、真实 monitor takeover、真实 approval approve/reject 的下游连线

## 备注
- 当前环境缺少 `Typer` / `Rich`，因此本次证据聚焦于路由目录、对象形状和文本视图 contract。
