# 线程间对接单

- 上游线程: `provider_architecture`
- 下游线程: `not verified yet`
- Wave: `wave_1`
- handoff 日期: `2026-03-31`
- 上游 commit: `not verified yet`

## 1. 上游已经稳定的东西
- 接口: `ProviderRequest`、`ProviderResponse`、`Provider` protocol
- 对象: `TimeoutPolicy`、`RetryPolicy`
- 错误: `ProviderConfigurationError`、`ProviderRequestError`、`ProviderUpstreamError`
- 枚举 / 常量: `not verified yet`
- 命令 / 入口: `RPCProvider.fetch()`、`GraphProvider.fetch()`、`EtherscanProvider.fetch()`、`EtherscanProvider.fetch_or_fallback()`
- 文件路径: `backend/data/providers/_shared_http_client.py`、`backend/data/providers/rpc_provider.py`、`backend/data/providers/graph_provider.py`、`backend/data/providers/etherscan_provider.py`

## 2. 下游必须按此消费

### 输入对象
```json
{
  "operation": "string",
  "params": {
    "params": "list<any> | optional for RPC",
    "variables": "object | optional for Graph",
    "operation_name": "string | optional for Graph",
    "module": "string | optional for Etherscan",
    "action": "string | optional for Etherscan",
    "query": "object | optional for Etherscan"
  }
}
```

### 输出对象
```json
{
  "provider": "string",
  "operation": "string",
  "payload": "any",
  "metadata": "object"
}
```

### 异常模型
```text
ProviderConfigurationError
ProviderRequestError
ProviderUpstreamError
```

## 3. 约束
- 不允许: 在每个 provider 内再写一套重试循环
- 仅允许: 通过 `_shared_http_client.SharedHTTPClient` 统一超时 / 重试
- 单位与精度约定: `not verified yet`
- 空值 / 默认值约定:
  - `ProviderRequest.params` 默认空 mapping
  - Etherscan `query` 必须显式给出或在调用方补齐
  - Graph `variables` 缺省为空 dict

## 4. 样例
- sample request: `ProviderRequest(operation="account.txlist", params={"query": {"address": "0xabc", "startblock": 0}})`
- sample response: `ProviderResponse(provider="etherscan", operation="account.txlist", payload=<json>, metadata={"fallback_capable": true})`
- sample failure: `ProviderUpstreamError("upstream request failed after retries")`

## 5. 未完成项
- TODO: 真实 `web3` / `gql` 运行时依赖联调仍然 `not verified yet`
- 临时 workaround: fake 依赖只用于本地验证脚本
- 风险提示: 当前仓库无 commits，后续如需引用 commit / branch 历史，需要先补上 git 初始提交
