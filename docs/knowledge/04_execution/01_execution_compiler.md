# Execution Compiler

## 目标职责


## 输入
- `StrategyIntent`
- `TradeIntent`
- 注册时链上状态

## 输出
- `ExecutionPlan`
- `InvestmentIntent` register payload

## 关键设计
- calldata 不由 AI 生成
- 编译发生在注册时，不在触发时
- 入场参数采用绝对约束
- 出场参数采用相对滑点 BPS
- 异常快速抛出，由上层统一处理

## 依赖
- Domain Models
- RPC quote / reserve snapshot
- PreRegistrationCheck
- Contract interface
