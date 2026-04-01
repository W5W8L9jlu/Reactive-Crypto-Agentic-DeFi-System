# Prompt Template: Provider Architecture

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement ONLY the `provider_architecture` module.

Goal:
<一句话说明本轮目标，例如：实现 compile() happy path>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/07_data/01_provider_architecture.md
4. docs/contracts/provider_architecture.contract.md

Optional supporting files:
- docs/knowledge/07_data/02_source_of_truth_rules.md

Only edit these paths:
- backend/data/providers/rpc_provider.py
- backend/data/providers/graph_provider.py
- backend/data/providers/etherscan_provider.py
- backend/data/providers/_shared_http_client.py

Do not:
- 业务层特征工程
- 执行真相裁决

Hard invariants to preserve:
- RPC 用 web3.py，The Graph 用 gql
- 优先官方 SDK；否则统一 httpx client
- 禁止在各 provider 重复实现重试逻辑

Deliverables:
- <代码/测试/接口/文档>

Definition of done:
- Phase 1 最小数据源集合可用
- provider 接口清晰统一

Verification:
- provider 正常取数测试
- fallback 测试
- shared client 重试/超时测试

When spec is missing:
- do not invent behavior
- leave a clear TODO or raise a domain error
- summarize assumptions explicitly
```
