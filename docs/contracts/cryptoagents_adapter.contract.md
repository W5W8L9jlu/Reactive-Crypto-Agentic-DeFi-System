# Implementation Contract: CryptoAgents Adapter

## Module ID
`cryptoagents_adapter`

## Working Directory
`backend/decision`

## Primary Knowledge File
- `docs/knowledge/02_decision/01_cryptoagents_adapter.md`

## Scope
本模块只负责以下职责：
- 能够接收标准化 DecisionContext
- 能够稳定输出 Pydantic 兼容结构化对象
- 保留 agent trace
- 失败时返回明确的解析/约束错误

## Inputs
- `DecisionContext`

## Outputs
- `PortfolioManagerOutput`
- `DecisionMeta`
- `AgentTrace`
- `DecisionArtifact(partial)`

## Canonical Files To Touch
- `backend/decision/adapters/cryptoagents_adapter.py`
- `backend/decision/prompts/`
- `backend/decision/schemas/`

## Must Read Before Coding
- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/02_decision/02_context_builder.md`
- `docs/knowledge/08_delivery/01_export_outputs.md`

## Hard Invariants
- 保留多 Agent orchestration，不重写底盘
- AI 不生成最终 calldata
- 输出必须结构化，执行字段与 thesis/report 文本分离
- 只生成 Conditional Intent，不生成即时市价建议

## Non-goals
- 链上执行
- 最终签名
- 交易即时决策

## Definition of Done
- 能够接收标准化 DecisionContext
- 能够稳定输出 Pydantic 兼容结构化对象
- 保留 agent trace
- 失败时返回明确的解析/约束错误

## Minimum Verification
- 结构化输出 schema 测试
- 缺字段 / 越界字段失败测试
- thesis 与 trade_intent 分离测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
