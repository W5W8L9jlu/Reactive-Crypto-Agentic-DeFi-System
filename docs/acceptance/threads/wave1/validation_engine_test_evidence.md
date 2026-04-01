# 线程测试证据

## 测试目标
- 验证字段范围校验是否由 Pydantic v2 承担。
- 验证跨字段 `model_validator` 是否会拒绝越界对象。

## 覆盖的场景
- happy path：模板、意图、交易意图、执行计划均符合边界，返回有效 `ValidationResult`
- failure path：`ttl_seconds=0` 被拒绝
- failure path：`template_version` 不匹配被拒绝
- failure path：`pair` 不在模板允许范围内被拒绝
- edge case：模板 `allowed_pairs` / `allowed_dexes` 为空时抛领域异常

## 输入
```json
{
  "strategy_template": {
    "template_id": "tpl-eth-swing",
    "version": 1,
    "auto_allowed_pairs": ["ETH/USDC"],
    "manual_allowed_pairs": ["WBTC/USDC"],
    "auto_allowed_dexes": ["uniswap_v3"],
    "manual_allowed_dexes": ["curve"],
    "auto_max_position_usd": "5000",
    "hard_max_position_usd": "10000",
    "auto_max_slippage_bps": 30,
    "hard_max_slippage_bps": 80,
    "auto_stop_loss_bps_range": {"min_bps": 50, "max_bps": 200},
    "manual_stop_loss_bps_range": {"min_bps": 10, "max_bps": 400},
    "auto_take_profit_bps_range": {"min_bps": 100, "max_bps": 500},
    "manual_take_profit_bps_range": {"min_bps": 50, "max_bps": 1000},
    "auto_daily_trade_limit": 2,
    "hard_daily_trade_limit": 8,
    "execution_mode": "conditional"
  },
  "strategy_intent": {
    "strategy_intent_id": "si-001",
    "template_id": "tpl-eth-swing",
    "template_version": 1,
    "execution_mode": "conditional",
    "projected_daily_trade_count": 1
  },
  "trade_intent": {
    "trade_intent_id": "ti-001",
    "strategy_intent_id": "si-001",
    "pair": "ETH/USDC",
    "dex": "uniswap_v3",
    "position_usd": "1200",
    "max_slippage_bps": 20,
    "stop_loss_bps": 90,
    "take_profit_bps": 250,
    "entry_conditions": ["price_below:3000"],
    "ttl_seconds": 3600
  }
}
```

## 输出
```json
{
  "is_valid": true,
  "validated_objects": [
    "StrategyTemplate",
    "StrategyIntent",
    "TradeIntent",
    "ExecutionPlan"
  ],
  "issues": []
}
```

## 命令
```bash
python -m unittest backend.validation.test_validation_engine
python -m unittest backend.export.test_export_outputs backend.validation.test_validation_engine
```

## 实际结果
- 通过：5 个 validation tests 通过；8 个 combined tests 通过
- 失败：无
- 未覆盖：未对更完整的 ExecutionPlan 语义做额外约束测试

## 备注
- `git diff --name-only HEAD` 在当前仓库状态下不可用，因为仓库没有提交历史。
