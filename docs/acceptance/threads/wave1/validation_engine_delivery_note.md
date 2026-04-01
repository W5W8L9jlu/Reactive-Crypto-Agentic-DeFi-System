# 线程交付说明

## 基本信息
- 模块名：validation_engine
- Prompt 文件：`docs/prompts/validation_engine.prompt.md`
- Wave：wave_1
- 负责人：not verified yet
- 分支：master
- commit：not verified yet

## 本次交付做了什么
- 新增基于 Pydantic v2 的强类型校验入口，先解析 `StrategyTemplate` / `StrategyIntent` / `TradeIntent` / `ExecutionPlan`，再做跨对象边界校验。
- 新增统一 `ValidationResult` 与 `ValidationIssue`，让失败路径可被下游统一消费。
- 新增领域异常，用于文档未定义行为的显式拒绝，而不是猜测实现。

## 修改了哪些文件
- `backend/validation/errors.py`
- `backend/validation/models.py`
- `backend/validation/validation_engine.py`
- `backend/validation/__init__.py`
- `backend/validation/README.md`
- `backend/validation/test_validation_engine.py`

## 没做什么
- 没有做 RPC 查询。
- 没有编译 calldata。
- 没有做审批展示。
- 没有做链上状态确认。

## 运行了哪些命令
```bash
git branch --show-current
git status --short
git diff --name-only HEAD
git log --oneline -n 10
python -m unittest backend.validation.test_validation_engine
python -m unittest backend.export.test_export_outputs backend.validation.test_validation_engine
```

## 验收证据
- 测试截图：not verified yet
- 日志：`python -m unittest backend.validation.test_validation_engine` -> `OK`
- 示例 payload：见 `backend/validation/test_validation_engine.py` 的 `_valid_payloads()`
- 示例输出：`is_valid=True` 的 `ValidationResult`

## 对下游线程的影响
- 新增输入对象：`ExecutionPlan`、`ExecutionHardConstraints`
- 新增输出对象：`ValidationResult`、`ValidationIssue`
- 新增异常：`ValidationEngineDomainError`、`MissingValidationSpecError`
- 新增命令/入口：`validate_inputs(...)`、`validate_inputs_or_raise(...)`
- 需要下游同步更新的点：如果下游要消费统一失败结果，需按 `ValidationResult.issues` 和 `field_path` 解析；如果下游依赖空模板边界规则，需要先补 knowledge/contract
