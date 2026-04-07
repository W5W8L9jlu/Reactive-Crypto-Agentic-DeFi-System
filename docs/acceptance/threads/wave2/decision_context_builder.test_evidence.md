# decision_context_builder 线程测试证据

## 测试目标
- 验证 `DecisionContextBuilder` 能输出完整 `DecisionContext`
- 验证 provider-backed fetchers 的正常路径、显式 fallback 路径和错误路径
- 验证 `execution_state` 不会在 provider 缺失时静默默认

## 覆盖的场景
- context 完整性：
  - provider-backed fetchers 驱动 builder 产出完整 `DecisionContext`
  - `generated_at` 存在并带时区
- provider fallback：
  - `AggregatedMarketFetcher` 在 primary payload 缺字段且显式配置 fallback provider 时回退
- 缺数据 / 延迟异常：
  - `capital_flow` payload 缺字段时报 `ProviderDomainError`
  - `onchain_flow` upstream timeout 时显式报错
  - `execution_state` upstream timeout 时显式报错
  - builder 在 execution fetch 失败时包装为 `ProviderDataUnavailableError`
- 数据质量：
  - `liquidity_depth.depth_usd_2pct <= 0` 时抛 `DataQualityError`
- 模型约束：
  - `StrategyConstraints` 的 `max_position_usd`、`max_slippage_bps` 等边界校验

## 命令
```bash
$env:PYTHONPATH='.'; pytest backend/data/fetchers/test_aggregated_fetchers.py backend/data/context_builder/test_context_builder.py -q
```

## 输入
- `strategy_constraints` fixture：
```json
{
  "pair": "ETH/USDC",
  "dex": "uniswap_v3",
  "max_position_usd": "100000",
  "max_slippage_bps": 50,
  "stop_loss_bps": 200,
  "take_profit_bps": 500,
  "ttl_seconds": 3600,
  "daily_trade_limit": 10
}
```
- provider-backed happy path payloads：
  - `market_trend.direction=up`
  - `market_trend.confidence=0.81`
  - `capital_flow.net_inflow_usd=2500000`
  - `liquidity_depth.depth_2pct=5500000`
  - `onchain_flow.gas_price_gwei=24.5`
  - `risk_state.volatility_annualized=0.62`
  - `position_state.entry_price_usd=3120.5`
  - `execution_state.daily_trades_executed=2`

## 输出
- pytest 输出：
  - `14 passed, 2 warnings in 2.46s`
- warning：
  - `PytestCacheWarning`
  - 原因：当前 sandbox 无法写 `.pytest_cache`

## 实际结果
- 通过：
  - provider-backed context happy path
  - market fallback path
  - missing-field error path
  - onchain timeout error path
  - execution provider required path
  - execution timeout error path
  - builder execution failure wrapping
  - data quality checks
  - `StrategyConstraints` 基础边界校验
- 未覆盖：
  - 真实 provider 集成：`not verified yet`
  - 下游 adapter 消费 `DecisionContext`：`not verified yet`
  - freshness / staleness 判断：`not verified yet`

## 备注
- 当前测试证据来自 repo 当前工作树，不来自已落地 commit。
- 当前工作树下本模块还有 `__pycache__` diff；这不影响上述测试结果。
