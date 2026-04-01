# CryptoAgents Adapter

## 目标职责
- 调用 CryptoAgents 多角色流程
- 保留 analyst / research / risk / portfolio 的多智能体推理骨架
- 输出结构化 `DecisionArtifact`
- 输出长期投资 thesis 和 Investment Memo
- 不直接输出最终可执行 calldata

## 不负责
- 即时交易
- 直接下单
- 直接编码合约参数

## 可直接复用能力


## 推荐改造路径


## Prompt 重构重点


## 依赖模块
- Domain Models
- DecisionContextBuilder
- Export layer

## 并行开发接口
输入：
- `DecisionContext`

输出：
- `PortfolioManagerOutput`
- `DecisionMeta`
- `AgentTrace`
