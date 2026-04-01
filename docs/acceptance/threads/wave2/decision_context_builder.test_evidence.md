# 线程测试证据

## 测试目标
- 证明模块能输出完整 `DecisionContext`
- 证明 provider fallback、缺数据异常、延迟异常会走显式错误路径
- 证明 builder 不依赖 tick 级输入，而依赖聚合后的趋势/资金流/风险/仓位/执行状态对象

## 覆盖的场景
- happy path:
  - `DecisionContextBuilder` 基于 mock fetchers 返回完整 context
  - `DecisionContextBuilder` 基于 provider-backed aggregated fetchers 返回完整 context
- failure path:
  - `FailingMarketFetcher` 触发 `ProviderDataUnavailableError`
  - `AggregatedMarketFetcher` 缺字段触发 `ProviderDomainError`
  - `AggregatedOnchainFetcher` timeout 触发 `ProviderDomainError`
- edge case:
  - `InvalidLiquidityFetcher` 触发 `DataQualityError`
  - primary provider payload 非法时 fallback 到 secondary provider
  - `StrategyConstraints` 非法参数校验

## 输入
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
  "provider_payload_example": {
    "market_trend": {
      "direction": "up",
      "confidence": "0.81",
      "timeframe_minutes": 240
    },
    "capital_flow": {
      "net_inflow_usd": "2500000",
      "volume_24h_usd": "70000000",
      "whale_inflow_usd": "1800000",
      "retail_inflow_usd": "700000"
    }
  }
}
```

## 输出
```json
{
  "context_id": "ctx-provider-backed-001",
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
  }
}
```

## 命令
```bash
$env:PYTHONPATH='D:\reactive-crypto-agentic-DeFi-system'; pytest backend/data/context_builder/test_context_builder.py backend/data/fetchers/test_aggregated_fetchers.py -q
```

## 实际结果
- 通过: `11 passed, 2 warnings in 1.12s`
- 失败: `0`
- 未覆盖:
  - live provider 联调
  - 非 market fetcher 的 fallback 路径逐一验证
  - 跨模块端到端消费 `DecisionContext`

## 备注
- 本工作区中，最终通过证据来自带 `PYTHONPATH` 的 pytest 命令。
- warnings 为 `.pytest_cache` 权限告警，不是断言失败。
- `git diff --name-only HEAD` 与 `git log --oneline -n 10` 因仓库无提交而 `not verified yet`，不作为通过性证据。
