# Domain Models

## 一级核心对象
- `DecisionContext`
- `StrategyTemplate`
- `StrategyIntent`
- `TradeIntent`
- `ExecutionPlan`
- `DecisionMeta`
- `AgentTrace`
- `ValidationResult`
- `ExecutionRecord`
- `DecisionArtifact`
- `ApprovalBattleCard`

## 强约束
- 所有核心对象必须映射为 Pydantic v2 models
- 禁止在业务层重复发明 schema 校验逻辑
- Validation Engine 只接收强类型对象

## 模型职责摘要

### DecisionContext
统一决策输入，聚合 market / liquidity / onchain_flow / risk_state / position_state / strategy_constraints / execution_state。

### StrategyTemplate
策略模板真相对象，定义 pairs、dex、仓位上限、滑点、止损止盈区间、日内限制、执行模式等。

### StrategyIntent
长期投资目标层抽象，可拆解为多个 `TradeIntent`。

### TradeIntent
执行真相主对象，必须是条件意图，含 entry_conditions、TTL、max_slippage_bps、stop_loss_bps、take_profit_bps。

### ExecutionPlan
注册时编译产物，包含 register payload 与链上硬约束参数。

### DecisionArtifact
统一中间产物：
- strategy_intent
- trade_intent
- execution_plan
- decision_meta
- agent_trace
- validation_result
- execution_record

### ApprovalBattleCard
CLI 审批显示对象，不是执行真相。

## 原始 schema 参考
请回看 PRD 中的 6.1 ~ 6.13 定义。
