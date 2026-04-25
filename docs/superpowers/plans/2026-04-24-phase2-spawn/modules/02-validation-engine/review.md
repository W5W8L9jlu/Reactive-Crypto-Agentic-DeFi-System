# Draft Summary

- `模块：` Validation Engine (`validation_engine`)
- `阶段：` Decision Boundary
- `目标：` Implement module scope: 所有核心对象先解析为强类型对象; 抛出清晰 ValidationError 或领域异常; 输出 ValidationResult

## 重点验收

- 所有核心对象先解析为强类型对象
- 抛出清晰 ValidationError 或领域异常
- 输出 ValidationResult

## 重点非目标

- RPC 查询
- calldata 编译
- 审批展示

## 重点风险

- 必须基于 Pydantic v2
- 禁止散落 if/else schema 校验
- 不做链上状态确认

# Full Draft

# Draft Task Card

## Header

- `模块：` Validation Engine (`validation_engine`)
- `负责人 agent：` Backend Architect
- `状态：` Draft
- `来源：` 用户目标 / contract / prompt / knowledge

## 1. 目标

- Implement module scope: 所有核心对象先解析为强类型对象; 抛出清晰 ValidationError 或领域异常; 输出 ValidationResult

## 2. 验收标准

- [ ] 所有核心对象先解析为强类型对象
- [ ] 抛出清晰 ValidationError 或领域异常
- [ ] 输出 ValidationResult
- [ ] 字段范围校验
- [ ] 跨字段 model_validator 校验
- [ ] 非法对象拒绝测试

## 3. 非目标

- RPC 查询
- calldata 编译
- 审批展示

## 4. 风险

- 必须基于 Pydantic v2
- 禁止散落 if/else schema 校验
- 不做链上状态确认
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。

## 5. 依据

- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/03_strategy_validation/02_validation_engine.md`
- `docs/contracts/validation_engine.contract.md`
- `docs/prompts/validation_engine.prompt.md`