# Strategy Boundary Service

## 目标职责
- 创建 / 修改 / 查看策略模板
- 模板版本管理
- 约束边界校验
- 决定自动注册、人工审批或拒绝

## 输入
- `StrategyTemplate`
- `StrategyIntent`
- `TradeIntent`

## 输出
- boundary decision:
  - auto register
  - manual approval
  - reject

## 并行边界
本模块不做：
- 链上状态确认
- calldata 编译
- 真实执行
