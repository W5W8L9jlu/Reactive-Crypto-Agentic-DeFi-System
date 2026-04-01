# Approval Flow

## 目标
当意图超出模板边界但未越界拒绝时，进入 CLI 审批流。

## 审批视图对象


## CLI 审批要求


## 终端 UI Mockup


## 规则
- 默认展示 `ApprovalBattleCard`
- `--raw` 才允许看 Machine Truth
- 必须显示 TTL 倒计时
- 过期意图禁止审批

## 依赖
- ValidationResult
- TradeIntent
- ExecutionPlan
- DecisionMeta
- CLI surface
