# 线程验收清单
- 模块 / prompt: `provider_architecture`
- Wave: `wave_1`
- 线程负责人: `not verified yet`
- commit: `not verified yet`
- 改动目录: `backend/data/providers`
- 是否只改允许路径: `是`

## A. 职责边界
- 本模块目标已完成：Phase 1 最小可用数据接入骨架可用，且 provider 接口已统一为 `fetch(ProviderRequest) -> ProviderResponse`。
- 未引入业务层特征工程。
- 未执行真相裁决。
- RPC 只通过 `web3.py` 接入。
- The Graph 只通过 `gql` 接入。
- Etherscan 通过共享 `httpx` client 接入，并提供显式 fallback 入口。

## B. Contract 对齐
- 已对齐 `docs/contracts/provider_architecture.contract.md` 的工作目录与 Canonical Files To Touch。
- 已对齐硬约束：
  - RPC 用 `web3.py`
  - The Graph 用 `gql`
  - 优先官方 SDK，否则统一 `httpx` client
  - 禁止在各 provider 重复实现重试逻辑
- 未满足项: `not verified yet` 的只有外部依赖是否在目标运行环境完整安装；当前工作区只做了导入保护和本地验证。

## C. Invariants 检查
- JSON 仍是唯一执行真相: `不适用`
- Audit 只做摘抄: `不适用`
- Investment Memo 未污染执行真相: `不适用`
- 仍然只信 RPC 作为执行真相: `是`
- Execution Compiler 只在注册时工作: `不适用`
- Reactive 未承担自由决策: `不适用`
- Shadow Monitor 保持独立: `不适用`
- provider 层没有实现 truth judgment。
- provider 层没有重复重试循环；重试收敛到 `_shared_http_client.py`。

## D. 验收依据
- `git -C D:/reactive-crypto-agentic-DeFi-system branch --show-current` -> `master`
- `git -C D:/reactive-crypto-agentic-DeFi-system log --oneline -n 10` -> 仓库当前分支没有 commits，无法输出提交历史
- `git -C D:/reactive-crypto-agentic-DeFi-system diff --name-only HEAD` -> `HEAD` 不存在，无法比较
- `python -m compileall ...` -> 4 个 provider 文件均可编译
- 自定义验证脚本 -> `provider_architecture verification passed`

## E. Known gaps
- `git` 历史不可用: 当前仓库是无提交状态，commit 证据只能记为 `not verified yet`。
- 目标环境的真实 `web3` / `gql` 依赖未在本地安装，已通过导入保护避免模块级崩溃，但端到端真实 SDK 联调仍是 `not verified yet`。
- 仓库内未发现现成的 provider pytest 文件，故没有 repo 原生测试证据。

## F. 交付结果
- 状态: `PASS_WITH_NOTES`
- 进入线程间对接: `可以`
