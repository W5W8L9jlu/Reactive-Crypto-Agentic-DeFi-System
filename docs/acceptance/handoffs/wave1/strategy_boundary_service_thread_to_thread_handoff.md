# 线程间对接单

- 上游线程：strategy_boundary_service
- 下游线程：not verified yet
- Wave：wave_1
- handoff 日期：2026-03-31
- 上游 commit：not verified yet

## 1. 上游已经稳定的东西
- 接口：`StrategyBoundaryService.register_template(...)`、`get_template(...)`、`get_latest_version(...)`、`evaluate(...)`
- 对象：`StrategyTemplate`、`StrategyIntent`、`TradeIntent`、`BoundaryDecisionResult`
- 枚举：`BoundaryDecision`、`RuleDecision`
- 异常：`TemplateNotFoundError`、`IntentLinkError`、`MissingBoundaryRuleError`
- 命令：`pytest backend/strategy/tests/test_strategy_boundary_service.py -q`
- 文件路径：`backend/strategy/`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "strategy_intent": "StrategyIntent",
  "trade_intent": "TradeIntent",
  "template_registry": "StrategyTemplate[]"
}
```

### 输出对象
```json
{
  "strategy_intent_id": "si_001",
  "trade_intent_id": "ti_001",
  "template_id": "swing_eth",
  "template_version": 2,
  "boundary_decision": "auto_register | manual_approval | reject",
  "trace": [
    {
      "rule_name": "pair",
      "decision": "auto | manual | reject",
      "observed": "ETH/USDC",
      "note": "..."
    }
  ]
}
```

### 异常模型
```text
pydantic.ValidationError
TemplateNotFoundError
IntentLinkError
MissingBoundaryRuleError
```

## 3. 约束
- 不允许：把 Boundary Service 改写成 RPC 真相确认器
- 不允许：在这里做执行编译或 calldata 生成
- 仅允许：模板注册/读取、版本边界判断、规则分流、可追溯 trace 输出
- 单位与精度约定：`position_usd` 使用 Decimal；`bps` 字段使用非负整数；`ttl_seconds` 使用正整数
- 模板接入约定：模板先通过 `register_template(...)` 注入服务，再调用 `evaluate(...)`
- 版本策略约定：当前实现对“非最新但存在的模板版本”返回 `manual_approval`

## 4. 示例
- sample request：`StrategyIntent(template_version=2)` + `TradeIntent(pair="ETH/USDC", dex="uniswap-v3", position_usd=Decimal("5000"))`
- sample response：`BoundaryDecisionResult(boundary_decision=BoundaryDecision.AUTO_REGISTER, trace=[...])`
- sample failure：`TradeIntent(position_usd=Decimal("25000"))` 时返回 `reject`

## 5. 未完成项
- TODO：模板存储目前是内存注册，不是持久化来源
- TODO：外部模板仓库/DB 适配器未接入
- 风险提示：如果下游想改变版本边界策略，需要先更新 contract，再改实现
