# Validation Engine

## 目标职责
- 校验 `StrategyIntent` / `TradeIntent` 是否在模板范围内
- 输出 `ValidationResult`
- 不执行链上状态确认

## 强制约束


## 设计要求
- 禁止手写散落的 if/else schema 校验
- 必须基于 Pydantic v2
- 失败抛出 `ValidationError` 或领域异常

## 依赖
- Domain Models
- StrategyTemplate
