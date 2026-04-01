# 线程测试证据

## 测试目标
- 验证模板内意图可以进入 `auto_register`。
- 验证超出自动边界但仍在模板允许范围内的意图会进入 `manual_approval`。
- 验证越过硬边界的意图会直接 `reject`。
- 验证判定结果包含可追溯的 rule trace。

## 覆盖的场景
- happy path：`ETH/USDC` + `uniswap-v3` + 正常仓位/滑点/止盈止损，返回 `auto_register`
- manual path：`ARB/USDC` 落在 manual pair boundary，返回 `manual_approval`
- reject path：`position_usd=25000` 超过 `hard_max_position_usd=20000`，返回 `reject`
- version path：使用非最新但存在的模板版本，返回 `manual_approval`

## 输入
```python
StrategyTemplate(
    template_id="swing_eth",
    version=1 or 2,
    auto_allowed_pairs=frozenset({"ETH/USDC"}),
    manual_allowed_pairs=frozenset({"ARB/USDC"}),
    auto_allowed_dexes=frozenset({"uniswap-v3"}),
    manual_allowed_dexes=frozenset({"sushiswap"}),
    auto_max_position_usd=Decimal("10000"),
    hard_max_position_usd=Decimal("20000"),
    auto_max_slippage_bps=100,
    hard_max_slippage_bps=300,
    auto_stop_loss_bps_range=BpsRange(min_bps=100, max_bps=300),
    manual_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=500),
    auto_take_profit_bps_range=BpsRange(min_bps=200, max_bps=800),
    manual_take_profit_bps_range=BpsRange(min_bps=100, max_bps=1200),
    auto_daily_trade_limit=3,
    hard_daily_trade_limit=6,
    execution_mode="conditional",
)
```

```python
StrategyIntent(
    strategy_intent_id="si_001",
    template_id="swing_eth",
    template_version=1 or 2,
    execution_mode="conditional",
    projected_daily_trade_count=2,
)
```

```python
TradeIntent(
    trade_intent_id="ti_001",
    strategy_intent_id="si_001",
    pair="ETH/USDC" or "ARB/USDC",
    dex="uniswap-v3",
    position_usd=Decimal("5000") or Decimal("25000"),
    max_slippage_bps=80,
    stop_loss_bps=200,
    take_profit_bps=500,
    entry_conditions=["price <= 1800"],
    ttl_seconds=3600,
)
```

## 输出
```python
BoundaryDecisionResult(
    boundary_decision=BoundaryDecision.AUTO_REGISTER
    # or MANUAL_APPROVAL / REJECT
)
```

## 命令
```bash
pytest backend/strategy/tests/test_strategy_boundary_service.py -q
```

## 实际结果
- 通过：`4 passed in 0.63s`
- 失败：无
- 未覆盖：模板持久化、外部模板来源、不同 version policy 的替代策略

## 备注
- 测试文件中通过本地 `sys.path` 调整导入 `strategy` 包。
