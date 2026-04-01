# 线程测试证据

## 测试目标
- 验证 shared client 的统一超时 / 重试策略。
- 验证 RPC / The Graph / Etherscan 的 provider 取数路径。
- 验证 Etherscan fallback 路径。

## 覆盖场景
- happy path: HTTP 200 / RPC stub / Graph stub / Etherscan stub
- failure path: HTTP 503 重试、ReadTimeout 重试、Etherscan fallback
- edge case: 目标环境缺少真实 `web3` / `gql` 依赖时，模块导入不应直接崩溃

## 输入
```json
{
  "rpc": {
    "request": {
      "operation": "eth_blockNumber",
      "params": { "params": [] }
    }
  },
  "graph": {
    "request": {
      "operation": "query Pairs($first:Int!){ pairs(first:$first){ id } }",
      "params": { "variables": { "first": 1 }, "operation_name": "Pairs" }
    }
  },
  "etherscan": {
    "request": {
      "operation": "account.txlist",
      "params": { "query": { "address": "0xabc", "startblock": 0 } }
    }
  }
}
```

## 输出
```json
{
  "shared_client": {
    "result": "json payload",
    "retry": "503 and timeout retried"
  },
  "rpc": {
    "result": "ProviderResponse(provider=rpc, operation=eth_blockNumber, ...)"
  },
  "graph": {
    "result": "ProviderResponse(provider=the_graph, operation=Pairs, ...)"
  },
  "etherscan": {
    "result": "ProviderResponse(provider=etherscan, operation=account.txlist, ...)",
    "fallback": "ProviderResponse(provider=rpc, metadata.fallback_from=etherscan, ...)"
  }
}
```

## 命令
```bash
python -m compileall D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/_shared_http_client.py D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/rpc_provider.py D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/graph_provider.py D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/etherscan_provider.py
```

## 实际结果
- 通过: `provider_architecture verification passed`
- 失败: `not verified yet`
- 未覆盖: 真实线上 endpoint 联调

## 备注
- 自定义验证脚本使用了 `httpx.MockTransport`、fake `web3`、fake `gql`，避免依赖外网。
- 仓库内未发现现成 provider pytest 文件，因此没有 repo 原生测试结果。
