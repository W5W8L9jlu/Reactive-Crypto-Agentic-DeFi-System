# AGENTS.md

对该目录的改动，优先遵守：
- `docs/knowledge/08_delivery/01_export_outputs.md`
- `docs/contracts/export_outputs.contract.md`

规则：
- 执行 = JSON 真相
- 审计 = 摘抄
- 报告 = 生成

## Phase2 Guardrails - Export

Export has three separated outputs.

Must:
- Treat JSON as Machine Truth.
- Keep Audit Markdown as excerpt-only.
- Keep Investment Memo as narrative-only.
- Ensure exports are derived from `ExecutionRecord` and `DecisionArtifact`.
- Never let Memo or Audit mutate execution JSON.

Must not:
- Generate new execution facts in Markdown.
- Summarize Audit Markdown beyond structured excerpts.
- Back-propagate Memo text into `TradeIntent`, `ExecutionPlan`, or `ExecutionRecord`.
