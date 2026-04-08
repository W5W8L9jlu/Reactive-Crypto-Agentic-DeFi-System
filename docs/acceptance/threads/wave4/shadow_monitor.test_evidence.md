# 线程测试证据

## 测试目标
- 验证 `shadow_monitor` 最小守护闭环是否覆盖：
  - Grace Period 告警
  - 超时升级为 critical 告警并产出 force-close recommendation
  - 状态已关闭后不重复报警

## 覆盖场景
- 价格击穿阈值且未达 Grace Period：输出 `warning`，不产出 force-close recommendation
- 价格持续击穿并超过 Grace Period：输出 `critical`，产出 force-close recommendation
- 备用 RPC 状态已 `Closed`：不输出告警，不输出建议

## 命令
```bash
python -m py_compile backend/monitor/shadow_monitor.py backend/monitor/reconciliation_daemon.py
python -  # 内联脚本，执行上述 3 个场景断言
```

## 输入（测试夹具）
```json
{
  "active_position_intent": {
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
  },
  "backup_rpc_snapshot": {
    "intent_id": "intent-1",
    "position_state": "ActivePosition | Closed",
    "mark_price": "99 | 98",
    "observed_at": "2026-04-08T00:00:00+00:00"
  },
  "grace_period_seconds": 30
}
```

## 输出（关键断言）
```json
{
  "grace_phase": {
    "alerts_count": 1,
    "severity": "warning",
    "recommendations_count": 0
  },
  "escalated_phase": {
    "alerts_count": 1,
    "severity": "critical",
    "recommendations_count": 1
  },
  "closed_state_phase": {
    "alerts_count": 0,
    "recommendations_count": 0
  }
}
```

## 实际结果
- `python -m py_compile ...`：成功（退出码 0）
- 内联脚本输出：`shadow_monitor_contract_checks: OK`

## 未验证项
- `backend/monitor` 下独立测试文件（`test_*.py`）自动化执行：`not verified yet`
- 与真实 CLI/Reactive/Execution 跨模块集成测试：`not verified yet`
- 历史 CI 记录与本线程绑定：`not verified yet`

