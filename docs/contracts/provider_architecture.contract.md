# Implementation Contract: Provider Architecture

## Module ID
`provider_architecture`

## Working Directory
`backend/data/providers`

## Primary Knowledge File
- `docs/knowledge/07_data/01_provider_architecture.md`

## Scope
本模块只负责以下职责：
- Phase 1 最小数据源集合可用
- provider 接口清晰统一

## Inputs
- `chain/API requests`

## Outputs
- `normalized provider responses`

## Canonical Files To Touch
- `backend/data/providers/rpc_provider.py`
- `backend/data/providers/graph_provider.py`
- `backend/data/providers/etherscan_provider.py`
- `backend/data/providers/_shared_http_client.py`

## Must Read Before Coding
- `docs/knowledge/07_data/02_source_of_truth_rules.md`

## Hard Invariants
- RPC 用 web3.py，The Graph 用 gql
- 优先官方 SDK；否则统一 httpx client
- 禁止在各 provider 重复实现重试逻辑

## Non-goals
- 业务层特征工程
- 执行真相裁决

## Definition of Done
- Phase 1 最小数据源集合可用
- provider 接口清晰统一

## Minimum Verification
- provider 正常取数测试
- fallback 测试
- shared client 重试/超时测试

## Handoff Contract
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。
