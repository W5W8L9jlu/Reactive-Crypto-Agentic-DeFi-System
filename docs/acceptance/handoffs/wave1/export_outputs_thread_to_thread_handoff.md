# 线程间对接单

- 上游线程：`export_outputs`
- 下游线程：`not verified yet`
- Wave：`wave_1`
- handoff 日期：2026-03-31
- 上游 commit：`not verified yet`

## 1. 上游已经稳定的东西
- 输出 1：`machine_truth_json`
- 输出 2：`audit_markdown`
- 输出 3：`investment_memo`
- 领域异常：`ExportDomainError`
- 文件路径：`backend/export/export_outputs.py`、`backend/export/errors.py`、`backend/export/__init__.py`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "decision_artifact": {
    "any": "json payload"
  },
  "execution_record": {
    "any": "json payload"
  }
}
```

### 输出对象
```json
{
  "machine_truth_json": "{\"decision_artifact\":{...},\"execution_record\":{...}}",
  "audit_markdown": "# Audit Markdown Excerpt\n...",
  "investment_memo": "# Investment Memo\n..."
}
```

### 异常模型
```text
ExportDomainError
```

## 3. 约束
- 不允许把 `audit_markdown` 当成新的执行真相。
- 不允许把 `investment_memo` 回写到 machine truth。
- 不允许在本模块加入执行、策略判断、审批逻辑。
- 不允许对空产物静默补默认值；当前实现对未定义场景显式抛错。

## 4. 示例
- sample request：`export_outputs(decision_artifact, execution_record, memo_brief="...")`
- sample response：`ExportOutputs(machine_truth_json=..., audit_markdown=..., investment_memo=...)`
- sample failure：空 `decision_artifact` 与空 `execution_record` 时抛出 `ExportDomainError`

## 5. 未完成项
- TODO：`docs/knowledge/08_delivery/01_export_outputs.md` 未定义 Investment Memo 正式模板。
- TODO：空产物导出语义仍需知识库补齐。
- 风险提示：当前工作区没有 git 历史，且未运行更大范围集成测试。

