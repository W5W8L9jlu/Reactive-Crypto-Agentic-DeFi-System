# decision_context_builder 线程间对接单

- 上游线程：`decision_context_builder`
- 建议下游线程：`cryptoagents_adapter`、`pre_registration_check`、以及所有需要消费结构化决策上下文的线程
- Wave：`wave2`
- handoff 日期：`2026-04-07`
- 上游 commit：`not verified yet`
- 分支：`w1-gate-fail-fix`

## 1. 当前代码快照中已经稳定的东西
- builder 入口：
  - `DecisionContextBuilder.build(strategy_constraints, context_id) -> DecisionContext`
- 上下文对象：
  - `DecisionContext`
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

## 2. 下游必须按此消费
### builder request shape
```json
{
  "strategy_constraints": {
    "pair": "str",
    "dex": "str",
    "max_position_usd": "Decimal > 0",
    "max_slippage_bps": "int >= 0",
    "stop_loss_bps": "int >= 0",
    "take_profit_bps": "int >= 0",
    "ttl_seconds": "int >= 1",
    "daily_trade_limit": "int >= 0"
  },
  "context_id": "str"
}
```

### builder response shape
```json
{
  "market_trend": {
    "direction": "up|down|sideways|unknown",
    "confidence_score": "Decimal[0,1]",
    "timeframe_minutes": "int >= 1"
  },
  "capital_flow": {
    "net_inflow_usd": "Decimal",
    "volume_24h_usd": "Decimal",
    "whale_inflow_usd": "Decimal",
    "retail_inflow_usd": "Decimal"
  },
  "liquidity_depth": {
    "pair": "str",
    "dex": "str",
    "depth_usd_2pct": "Decimal",
    "total_tvl_usd": "Decimal"
  },
  "onchain_flow": {
    "active_address_delta_24h": "int",
    "transaction_count_24h": "int",
    "gas_price_gwei": "Decimal >= 0"
  },
  "risk_state": {
    "volatility_annualized": "Decimal >= 0",
    "var_95_usd": "Decimal",
    "correlation_to_market": "Decimal[-1,1]"
  },
  "position_state": {
    "current_position_usd": "Decimal >= 0",
    "unrealized_pnl_usd": "Decimal",
    "entry_price_usd": "Decimal | null"
  },
  "execution_state": {
    "daily_trades_executed": "int >= 0",
    "daily_volume_usd": "Decimal >= 0"
  },
  "strategy_constraints": "StrategyConstraints",
  "context_id": "str",
  "generated_at": "datetime",
  "sources": "Mapping[str,str]"
}
```

## 3. 错误模型
- builder 层：
  - `ProviderDataUnavailableError`
    - 任一 required fetch 失败时抛出
  - `DataQualityError`
    - 当前用于：
      - invalid market trend timeframe
      - invalid liquidity depth
      - invalid volatility
- fetcher 层：
  - `ProviderDomainError`
    - payload 缺字段
    - upstream timeout / provider failure 包装
  - `ValueError`
    - `AggregatedExecutionFetcher` 在 provider 缺失时直接抛错

## 4. 约束
- 不允许：
  - 输出 tick 级原始噪声
  - 在本模块内生成 execution truth / calldata
  - 在本模块内做最终风控裁决
  - 对 `execution_state` 做静默默认值兜底
- 仅允许：
  - 聚合 provider snapshots
  - 产出结构化 `DecisionContext`
  - 在显式配置 fallback provider 时进行有限 fallback
- 当前 fallback 约束：
  - `AggregatedMarketFetcher`：允许显式 fallback
  - `AggregatedLiquidityFetcher`：允许显式 fallback
  - `AggregatedExecutionFetcher`：不允许 fallback；provider 必填

## 5. 示例
- sample request（来自当前测试夹具）：
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
- sample response（当前测试断言到的字段）：
```json
{
  "market_trend": {
    "direction": "up",
    "timeframe_minutes": 240
  },
  "capital_flow": {
    "net_inflow_usd": "2500000"
  },
  "liquidity_depth": {
    "depth_usd_2pct": "5500000"
  },
  "onchain_flow": {
    "gas_price_gwei": "24.5"
  },
  "risk_state": {
    "volatility_annualized": "0.62"
  },
  "position_state": {
    "entry_price_usd": "3120.5"
  },
  "execution_state": {
    "daily_trades_executed": 2
  },
  "context_id": "ctx-provider-backed-001"
}
```
- sample failure：
```text
ProviderDataUnavailableError: Failed to fetch execution state
ProviderDomainError: execution_state payload is missing required fields: ...
ValueError: Execution state provider is required
DataQualityError: Invalid liquidity depth
```

## 6. 剩余问题
- 真实 provider 集成：`not verified yet`
- 下游 adapter / precheck 是否已稳定消费 `DecisionContext`：`not verified yet`
- freshness / staleness 规则：`not verified yet`
- 模块专属提交 commit：`not verified yet`
