# AGENTS.md

对该目录的改动，优先遵守：
- `docs/knowledge/07_data/01_provider_architecture.md`
- `docs/knowledge/07_data/02_source_of_truth_rules.md`
- `docs/contracts/provider_architecture.contract.md`
- `docs/contracts/decision_context_builder.contract.md`

规则：
- RPC 用 web3.py，The Graph 用 gql
- 统一 shared http client
- 不在 provider 重复实现重试逻辑
