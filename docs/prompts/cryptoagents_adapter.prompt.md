# Prompt Template: CryptoAgents Adapter

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `cryptoagents_adapter` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/02_decision/01_cryptoagents_adapter.md
4. docs/contracts/cryptoagents_adapter.contract.md

Optional supporting files:
- docs/knowledge/01_core/01_system_invariants.md
- docs/knowledge/01_core/02_domain_models.md
- docs/knowledge/02_decision/02_context_builder.md
- docs/knowledge/08_delivery/01_export_outputs.md

Only edit these paths:
- backend/decision/adapters/cryptoagents_adapter.py
- backend/decision/prompts/
- backend/decision/schemas/

Do not:
- 链上执行
- 最终签名
- 交易即时决策

Hard invariants to preserve:
- 保留多 Agent orchestration，不重写底盘
- AI 不生成最终 calldata
- 输出必须结构化，执行字段与 thesis/report 文本分离
- 只生成 Conditional Intent，不生成即时市价建议

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- 能够接收标准化 DecisionContext
- 能够稳定输出 Pydantic 兼容结构化对象
- 保留 agent trace
- 失败时返回明确的解析/约束错误

Verification:
- 结构化输出 schema 测试
- 缺字段 / 越界字段失败测试
- thesis 与 trade_intent 分离测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
