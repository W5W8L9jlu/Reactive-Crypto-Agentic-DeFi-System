# Validation Engine

该模块只负责：
- 将 `StrategyTemplate`、`StrategyIntent`、`TradeIntent`、`ExecutionPlan` 先解析为强类型对象
- 执行字段级和模型级边界校验
- 输出统一 `ValidationResult`

不负责：
- RPC 查询
- calldata 编译
- 审批展示
- 链上状态确认

## Public Interface
- `validate_inputs_or_raise(...) -> ValidationResult`
  - 校验失败时抛出 `pydantic.ValidationError` 或 `MissingValidationSpecError`
- `validate_inputs(...) -> ValidationResult`
  - 不抛出异常，返回 `is_valid=False` 的统一结果

## TODO / Spec Gaps
- 当前 knowledge/contract 未定义模板 `allowed_pairs` 或 `allowed_dexes` 为空时应如何处理。
  当前实现会抛出 `MissingValidationSpecError`，避免猜测行为。
