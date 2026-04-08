# shadow_monitor 线程间对接单

- 上游线程：`shadow_monitor`
- 建议下游线程：`cli_surface`、运维编排/告警处理线程
- Wave：`wave4`
- handoff 日期：`2026-04-08`
- 当前分支：`codex/wave4`
- 当前 HEAD：`4297287`
- 上游 commit：`not verified yet`

## 1. 上游已稳定产出（工作树）
- 核心入口：
  - `ShadowMonitor.reconcile_positions(...) -> ShadowMonitorResult`
  - `ReconciliationDaemon.run_cycle() -> ReconciliationDaemonCycle`
  - `ReconciliationDaemon.run_forever(...) -> list[ReconciliationDaemonCycle]`
- 核心数据对象：
  - `ActivePositionIntent`
  - `BackupRPCSnapshot`
  - `MonitorAlert`
  - `ForceCloseRecommendation`
  - `ShadowMonitorResult`

## 2. 下游消费契约
### 输入对象
```json
{
  "active_positions": [
    {
      "intent_id": "str",
      "trade_intent_id": "str | null",
      "position_state": "ActivePosition",
      "quantity": "decimal",
      "breach_rules": [
        {
          "rule_id": "str",
          "threshold_price": "decimal",
          "operator": "lte | gte",
          "reason_code": "str"
        }
      ]
    }
  ],
  "snapshots": [
    {
      "intent_id": "str",
      "position_state": "ActivePosition | Closed",
      "mark_price": "decimal",
      "observed_at": "timezone-aware datetime"
    }
  ]
}
```

### 输出对象
```json
{
  "checked_at": "timezone-aware datetime",
  "alerts": [
    {
      "code": "SHADOW_MONITOR_GRACE | SHADOW_MONITOR_CRITICAL_STALE_POSITION",
      "severity": "warning | critical",
      "source": "shadow_monitor",
      "escalation_required": "bool",
      "intent_id": "str",
      "trade_intent_id": "str | null",
      "estimated_additional_loss_usd": "decimal"
    }
  ],
  "force_close_recommendations": [
    {
      "action": "emergency_force_close",
      "reason_code": "str",
      "intent_id": "str",
      "trade_intent_id": "str | null",
      "estimated_additional_loss_usd": "decimal"
    }
  ]
}
```

## 3. 异常模型
```text
ShadowMonitorError
MissingShadowMonitorSpecError
ValueError (pydantic model validation /参数约束)
```

## 4. 约束
- 不允许：
  - 执行正常交易链路
  - 执行日常决策
  - 在 monitor 内直接触发链上动作
- 仅允许：
  - 读取 ActivePosition 与备用 RPC 状态
  - 进行 Grace Period 判定与升级告警
  - 产出 force-close 建议动作供人工/下游处理

## 5. 示例
- sample request：
```json
{
  "active_positions": [
    {
      "intent_id": "intent-1",
      "trade_intent_id": "ti-1",
      "position_state": "ActivePosition",
      "quantity": "1",
      "breach_rules": [
        {
          "rule_id": "stop-loss",
          "threshold_price": "100",
          "operator": "lte",
          "reason_code": "STOP_LOSS_BREACH"
        }
      ]
    }
  ],
  "snapshots": [
    {
      "intent_id": "intent-1",
      "position_state": "ActivePosition",
      "mark_price": "99",
      "observed_at": "2026-04-08T00:00:00+00:00"
    }
  ]
}
```
- sample response（超出 Grace Period 后）：
```json
{
  "alerts": [
    {
      "code": "SHADOW_MONITOR_CRITICAL_STALE_POSITION",
      "severity": "critical",
      "escalation_required": true,
      "intent_id": "intent-1"
    }
  ],
  "force_close_recommendations": [
    {
      "action": "emergency_force_close",
      "reason_code": "STOP_LOSS_BREACH",
      "intent_id": "intent-1"
    }
  ]
}
```

## 6. 剩余问题
- 上游 commit 锚点：`not verified yet`
- `shadow_monitor -> cli_surface AlertView` 真实映射联调：`not verified yet`
- 额外损失估算公式的跨模块冻结：`not verified yet`
- 作为提交基线的冻结标签/版本：`not verified yet`

