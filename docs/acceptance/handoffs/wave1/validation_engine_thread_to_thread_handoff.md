# 线程间对接单

- 上游线程：validation_engine
- 下游线程：not verified yet
- Wave：wave_1
- handoff 日期：2026-03-31
- 上游 commit：not verified yet

## 1. 上游已经稳定的东西
- 接口：`validate_inputs(...)`、`validate_inputs_or_raise(...)`
- 对象：`ExecutionPlan`、`ExecutionHardConstraints`、`ValidationIssue`、`ValidationResult`
- 枚举：none added
- 命令：`python -m unittest backend.validation.test_validation_engine`
- 文件路径：`backend/validation/`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "strategy_template": "StrategyTemplate | dict",
  "strategy_intent": "StrategyIntent | dict",
  "trade_intent": "TradeIntent | dict",
  "execution_plan": "ExecutionPlan | dict | null"
}
```

### 输出对象
```json
{
  "is_valid": true,
  "validated_objects": ["StrategyTemplate", "StrategyIntent", "TradeIntent"],
  "issues": []
}
```

### 异常模型
```text
pydantic.ValidationError
ValidationEngineDomainError
MissingValidationSpecError
```

## 3. 约束
- 不允许：把 Validation Engine 改写成 RPC 真相查询器
- 不允许：在这里做 calldata 编译或审批展示
- 仅允许：Pydantic v2 强类型解析、字段范围校验、跨字段模型校验、统一结果输出
- 单位与精度约定：`position_usd` 使用 Decimal；`ttl_seconds` 使用正整数；`bps` 字段使用非负整数
- 空值 / 默认值约定：`execution_plan` 可选；模板空 allowed list 目前按 TODO 异常处理

## 4. 示例
- sample request：`StrategyTemplate` + `StrategyIntent` + `TradeIntent` 的结构化字典，且 `pair/dex/template_id/template_version` 一致
- sample response：`ValidationResult(is_valid=True, validated_objects=(...), issues=())`
- sample failure：`trade_intent.pair` 不在模板允许范围内时返回/抛出 `value_error` 级别拒绝

## 5. 未完成项
- TODO：模板 `allowed_pairs` / `allowed_dexes` 为空时的正式业务规则仍未在 knowledge 中定义
- 临时 workaround：当前实现显式抛 `MissingValidationSpecError`
- 风险提示：下游若需要更细的 result schema，需先补充 contract，再扩展模型字段
