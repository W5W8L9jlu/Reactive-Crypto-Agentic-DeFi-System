# 线程间对接单

- 上游线程: `decision_context_builder`
- 下游线程: `not verified yet`
- Wave: `wave2`
- handoff 日期: `2026-04-01`
- 上游 commit: `not verified yet`

## 1. 上游已经稳定的东西
- 接口:
  - `DecisionContextBuilder.build(strategy_constraints, context_id) -> DecisionContext`
  - `AggregatedMarketFetcher.fetch_market_trend(pair)`
  - `AggregatedMarketFetcher.fetch_capital_flow(pair)`
  - `AggregatedLiquidityFetcher.fetch_liquidity_depth(pair, dex)`
  - `AggregatedOnchainFetcher.fetch_onchain_flow()`
  - `AggregatedRiskFetcher.fetch_risk_state(pair)`
  - `AggregatedPositionFetcher.fetch_position_state(pair)`
  - `AggregatedExecutionFetcher.fetch_execution_state()`
- 对象:
  - `StrategyConstraints`
  - `DecisionContext`
  - `MarketTrend`
  - `CapitalFlow`
  - `LiquidityDepth`
  - `OnchainFlow`
  - `RiskState`
  - `PositionState`
  - `ExecutionState`
- 错误:
  - `ProviderDataUnavailableError`
  - `DataQualityError`
  - `ProviderDomainError`
- 文件路径:
  - `backend/data/context_builder/builder.py`
  - `backend/data/context_builder/models.py`
  - `backend/data/fetchers/aggregated_fetchers.py`

## 2. 下游必须按此消费

### 输入对象
```json
{
  "strategy_constraints": {
    "pair": "ETH/USDC",
    "dex": "uniswap_v3",
    "max_position_usd": "100000",
    "max_slippage_bps": 50,
    "stop_loss_bps": 200,
    "take_profit_bps": 500,
    "ttl_seconds": 3600,
    "daily_trade_limit": 10
  },
  "context_id": "ctx-provider-backed-001"
}
```

### 输出对象
```json
{
  "context_id": "ctx-provider-backed-001",
  "market_trend": {
    "direction": "up",
    "confidence_score": "0.81",
    "timeframe_minutes": 240
  },
  "capital_flow": {
    "net_inflow_usd": "2500000",
    "volume_24h_usd": "70000000",
    "whale_inflow_usd": "1800000",
    "retail_inflow_usd": "700000"
  },
  "liquidity_depth": {
    "pair": "ETH/USDC",
    "dex": "uniswap_v3",
    "depth_usd_2pct": "5500000",
    "total_tvl_usd": "120000000"
  },
  "onchain_flow": {
    "active_address_delta_24h": 150,
    "transaction_count_24h": 42000,
    "gas_price_gwei": "24.5"
  },
  "risk_state": {
    "volatility_annualized": "0.62",
    "var_95_usd": "35000",
    "correlation_to_market": "0.74"
  },
  "position_state": {
    "current_position_usd": "40000",
    "unrealized_pnl_usd": "1800",
    "entry_price_usd": "3120.5"
  },
  "execution_state": {
    "daily_trades_executed": 2,
    "daily_volume_usd": "90000"
  },
  "strategy_constraints": {
    "pair": "ETH/USDC",
    "dex": "uniswap_v3"
  },
  "sources": {
    "market_trend": "market_fetcher",
    "capital_flow": "market_fetcher",
    "liquidity_depth": "liquidity_fetcher",
    "onchain_flow": "onchain_fetcher",
    "risk_state": "risk_fetcher",
    "position_state": "position_fetcher",
    "execution_state": "execution_fetcher"
  }
}
```

### 异常模型
```text
ProviderDataUnavailableError
DataQualityError
ProviderDomainError
```

## 3. 约束
- 不允许:
  - 让下游直接依赖 provider 原始 payload
  - 在本模块基础上追加 tick 级噪声输入
  - 在本模块内做链上执行、最终风控裁决、schema 外推
  - 吞掉 provider 缺数据或坏 payload
- 仅允许:
  - 通过显式 fetcher / adapter 接口替换数据源
  - 通过 `DecisionContext` 消费聚合结果
- 单位与精度约定:
  - 金额、比例、gas price 在代码中使用 `Decimal`
  - `timeframe_minutes`、`ttl_seconds`、trade limit、bps 使用整数
  - 本文 JSON 示例中的 decimal 以字符串表示，仅用于 handoff 说明
- 空值 / 默认值约定:
  - provider payload 中 `aggregated_at` 可省略，省略时使用模型默认 UTC 时间
  - `entry_price_usd`、`position_opened_at`、`last_execution_at` 可为空
  - builder 需要 7 个上下文字段全部可得；缺任一 required fetch 结果即报错，不做 silent fallback

## 4. 示例
- sample request:
  - `DecisionContextBuilder.build(strategy_constraints=<ETH/USDC constraints>, context_id="ctx-provider-backed-001")`
- sample response:
  - 见上文输出对象；已在 `backend/data/fetchers/test_aggregated_fetchers.py` 中验证关键字段
- sample failure:
  - `ProviderDataUnavailableError("Failed to fetch market trend for ETH/USDC")`
  - `ProviderDomainError("Missing required field volume_24h_usd in capital_flow payload")`
  - `DataQualityError("Invalid liquidity depth")`

## 5. 未完成项
- TODO:
  - live provider / upstream payload 一致性验证
  - 其他 fetcher fallback 路径逐一验证
- 临时 workaround:
  - 当前验证基于 repo 内 mock fetchers 与 `RecordingProvider`
- 风险提示:
  - 当前仓库无首个提交，commit / diff / recent history 均为 `not verified yet`
  - 下游若需要引用 commit 或 branch diff 作为冻结证据，需先建立 git 历史
