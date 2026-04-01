# export_outputs

## 模块职责
- 产出 `Machine Truth JSON`
- 产出 `Audit Markdown Excerpt`
- 产出 `Investment Memo`

## 三轨边界
- 执行 = JSON 真相：执行层只能使用 `machine_truth_json`。
- 审计 = 摘抄：`audit_markdown` 仅摘抄 JSON 字段，不做结论改写。
- 报告 = 生成：`investment_memo` 为独立报告文本，不写回 Machine Truth。

## 接口
- `export_outputs(decision_artifact, execution_record, memo_brief=None) -> ExportOutputs`
- 输入模型：
  - `DecisionArtifact` (`Pydantic RootModel[dict]`)
  - `ExecutionRecord` (`Pydantic RootModel[dict]`)
- 输出模型：
  - `ExportOutputs.machine_truth_json`
  - `ExportOutputs.audit_markdown`
  - `ExportOutputs.investment_memo`

## 可追溯规则
- Audit 使用 `machine-truth-excerpt` 代码块输出：
  - 每行格式：`<json_pointer>\t<json_value>`
  - `json_value` 为 JSON 原值序列化结果
- 该结构保证可从 Audit 逐行回溯到 Machine Truth JSON。

## 已知 TODO
- `docs/knowledge/08_delivery/01_export_outputs.md` 未定义：
  - 空 `DecisionArtifact + ExecutionRecord` 的导出语义
  - Investment Memo 的正式模板/字段
- 当前实现对上述缺失采用：
  - 空产物直接抛出 `ExportDomainError`（避免脑补）
  - Memo 输出明确 TODO 占位文本

