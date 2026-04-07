# decision_context_builder 线程内验收清单

- 模块 / contract：`decision_context_builder` / `docs/contracts/decision_context_builder.contract.md`
- Wave：`wave2`
- 分支：`w1-gate-fail-fix`
- 最近提交：
  - `c5afba2 docs: 更新Wave2验收与交接文档`
  - `1211b50 feat: 实现Wave2执行层与验收文档回填`
- 模块工作目录：`backend/data/context_builder/`、`backend/data/fetchers/`

## A. 职责边界
- 当前代码快照在 [builder.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/context_builder/builder.py)、[models.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/context_builder/models.py)、[aggregated_fetchers.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/fetchers/aggregated_fetchers.py) 中实现了：
  - `DecisionContextBuilder.build(strategy_constraints, context_id) -> DecisionContext`
  - `DecisionContext` 及其子对象：
    - `MarketTrend`
    - `CapitalFlow`
    - `LiquidityDepth`
    - `OnchainFlow`
    - `RiskState`
    - `PositionState`
    - `ExecutionState`
    - `StrategyConstraints`
  - provider-backed fetchers：
    - `AggregatedMarketFetcher`
    - `AggregatedLiquidityFetcher`
    - `AggregatedOnchainFetcher`
    - `AggregatedRiskFetcher`
    - `AggregatedPositionFetcher`
    - `AggregatedExecutionFetcher`
- 当前 diff 中与本模块直接相关的源码文件：
  - `backend/data/context_builder/__init__.py`
  - `backend/data/context_builder/test_context_builder.py`
  - `backend/data/fetchers/__init__.py`
  - `backend/data/fetchers/aggregated_fetchers.py`
  - `backend/data/fetchers/test_aggregated_fetchers.py`
- 当前 diff 还包含 `__pycache__` 产物；这些不计入模块交付事实。

## B. Contract 对齐
- 输入对齐：是。builder 当前消费 `StrategyConstraints` 与 provider-backed fetchers 提供的 snapshots。
- 输出对齐：是。builder 输出单一 `DecisionContext`，包含 contract 要求的：
  - `market_trend`
  - `capital_flow`
  - `liquidity_depth`
  - `onchain_flow`
  - `risk_state`
  - `position_state`
  - `execution_state`
  - `strategy_constraints`
- Provider 失败语义对齐：是。
  - builder 层通过 `ProviderDataUnavailableError` 明确抛错
  - fetcher 层通过 `ProviderDomainError` 暴露缺字段或上游失败
- 可替换/扩展数据源对齐：是。builder 依赖 Protocol，fetcher 封装 provider 差异。
- 未完全验证项：
  - 真实 provider 接线：`not verified yet`
  - 下游 adapter 消费 `DecisionContext`：`not verified yet`

## C. Invariants 检查
- 是否以趋势 / 资金流 / 风险环境 / 仓位态为主，而不是 tick 级噪声：是
- 是否仍然不产生执行真相 / calldata：是
- 是否统一屏蔽 provider 差异：是
- 是否存在静默吞错：未发现
- fallback 是否被限制在显式 provider 配置内：是
  - 当前只在 `AggregatedMarketFetcher` / `AggregatedLiquidityFetcher` 中看到显式 fallback 分支
  - `AggregatedExecutionFetcher` 当前要求 provider 必填，不存在默认空 `ExecutionState()` 兜底

## D. 验证证据
- 已运行命令：
  - `git diff --name-only HEAD`
    - 结果：输出包含本模块工作目录下的源码和 `__pycache__`，同时也包含大量无关模块改动
  - `git diff --name-only HEAD -- backend/data/context_builder backend/data/fetchers`
    - 结果：本模块源码 diff 为：
      - `backend/data/context_builder/__init__.py`
      - `backend/data/context_builder/test_context_builder.py`
      - `backend/data/fetchers/__init__.py`
      - `backend/data/fetchers/aggregated_fetchers.py`
      - `backend/data/fetchers/test_aggregated_fetchers.py`
  - `git log --oneline -n 10`
    - 结果：当前只看到 2 条最近提交，均不能直接证明是本模块提交
  - `git branch --show-current`
    - 结果：`w1-gate-fail-fix`
  - `$env:PYTHONPATH='.'; pytest backend/data/fetchers/test_aggregated_fetchers.py backend/data/context_builder/test_context_builder.py -q`
    - 结果：`14 passed, 2 warnings in 2.46s`
- 当前已验证的关键行为：
  - provider-backed fetchers 可以驱动 builder 产出完整 `DecisionContext`
  - market fetcher 在显式 fallback provider 存在时可回退
  - 缺字段 / 上游 timeout 会抛显式错误
  - execution state provider 缺失时不会静默默认

## E. Known gaps
- 真实 provider snapshots 到 builder 的集成：`not verified yet`
- `DecisionContext` 被 `cryptoagents_adapter` 或其他下游直接消费：`not verified yet`
- 数据 freshness / staleness 规则：`not verified yet`
- 模块专属提交 commit：`not verified yet`

## F. 可交付结论
- 状态：`PASS on current workspace evidence`
- 说明：
  - contract 最小验证项已被当前测试覆盖：
    - context 完整性
    - provider fallback
    - 缺数据 / 延迟异常
  - 当前尚未验证真实 provider 接线与下游 adapter 消费，因此这些点继续保留为已知缺口
