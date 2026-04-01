# 线程测试证据

## 测试目标
- 验证 `Audit Markdown` 对 `Machine Truth JSON` 的字段摘抄是 1:1 可追溯的。
- 验证 `Investment Memo` 不会污染 `Machine Truth JSON`。
- 验证规格缺失时会抛出明确领域异常，而不是猜测默认行为。

## 覆盖的场景
- happy path：`DecisionArtifact` + `ExecutionRecord` 正常导出三轨结果。
- failure path：空 `DecisionArtifact` + 空 `ExecutionRecord` 触发 `ExportDomainError`。
- edge case：`memo_brief` 仅影响 `investment_memo`，不进入 `machine_truth_json`.

## 输入
```json
{
  "decision_artifact": {
    "strategy_intent": {
      "thesis": "accumulate",
      "risk_label": "medium"
    },
    "conclusion": "WAIT_FOR_TRIGGER",
    "agent_trace": [
      {
        "step": "analyze",
        "score": 0.78
      }
    ]
  },
  "execution_record": {
    "status": "registered",
    "plan_id": "plan-001",
    "constraints": {
      "max_slippage_bps": 30,
      "ttl_minutes": 120
    }
  }
}
```

## 输出
```json
{
  "machine_truth_json": "passed",
  "audit_markdown": "passed",
  "investment_memo": "passed"
}
```

## 命令
```bash
python -m unittest backend/export/test_export_outputs.py -v
python -m pytest backend/export/test_export_outputs.py -q
```

## 实际结果
- `python -m unittest backend/export/test_export_outputs.py -v`：通过，3 个测试用例通过。
- `python -m pytest backend/export/test_export_outputs.py -q`：失败，当前环境未安装 `pytest`。
- 未覆盖：更大范围集成测试、跨模块消费验证。

