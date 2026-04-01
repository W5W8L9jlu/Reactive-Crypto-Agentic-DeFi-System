# 线程交付说明

## 基本信息
- 模块名: `provider_architecture`
- Prompt 文件: `docs/prompts/provider_architecture.prompt.md` `not verified yet`
- Wave: `wave_1`
- 负责人: `not verified yet`
- 分支: `master`
- commit: `not verified yet`

## 本次交付做了什么
- 落地了 `backend/data/providers` 的 Phase 1 最小可用 provider 骨架。
- 统一了 provider 输入输出接口，新增 `ProviderRequest` / `ProviderResponse` / `Provider` protocol。
- 把统一超时与重试策略集中到 `_shared_http_client.py`。
- 为 Etherscan 增加了显式 `fetch_or_fallback()` 入口，fallback 由调用方注入。

## 修改了哪些文件
- `backend/data/providers/_shared_http_client.py`
- `backend/data/providers/rpc_provider.py`
- `backend/data/providers/graph_provider.py`
- `backend/data/providers/etherscan_provider.py`

## 没做什么
- 没有做业务层特征工程。
- 没有做执行真相裁决。
- 没有新增 repo 内 pytest 文件。
- 没有修改 `docs/acceptance/` 之外的文件。

## 运行了哪些命令
```bash
git -C D:/reactive-crypto-agentic-DeFi-system diff --name-only HEAD
git -C D:/reactive-crypto-agentic-DeFi-system log --oneline -n 10
git -C D:/reactive-crypto-agentic-DeFi-system status --short
git -C D:/reactive-crypto-agentic-DeFi-system branch --show-current
python -m compileall D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/_shared_http_client.py D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/rpc_provider.py D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/graph_provider.py D:/reactive-crypto-agentic-DeFi-system/backend/data/providers/etherscan_provider.py
```

## 验收依据
- 自定义本地验证脚本输出: `provider_architecture verification passed`
- `compileall` 成功通过
- `git` 历史证据不可用，因为当前分支没有 commits

## 对下游的影响
- 新增稳定输入对象: `ProviderRequest`
- 新增稳定输出对象: `ProviderResponse`
- 新增稳定错误类型: `ProviderConfigurationError`、`ProviderRequestError`、`ProviderUpstreamError`
- 下游 context builder / pre-registration check 需要按这个统一接口接入
- 下游若需要 source-of-truth 决策，仍需在别的模块实现
