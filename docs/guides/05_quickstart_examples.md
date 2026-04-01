# Quickstart Examples

## Example 1：实现 Execution Compiler happy path

```text
Implement ONLY the `execution_compiler` module.

Goal:
实现 registration-time compile() happy path，输出 ExecutionPlan 和 register payload。

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/04_execution/01_execution_compiler.md
4. docs/contracts/execution_compiler.contract.md
5. docs/prompts/execution_compiler.prompt.md

Only edit these paths:
- backend/execution/compiler/

Do not:
- 在触发时重新编译
- 生成链上最终签名
- 替代合约 runtime checks

Return:
- changed files
- compile pipeline 说明
- tests run
- assumptions/TODOs
```

## Example 2：补 Validation Engine

```text
Implement ONLY the `validation_engine` module.

Goal:
用 Pydantic v2 重构 TradeIntent / StrategyIntent 校验，并输出 ValidationResult。

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/knowledge/03_strategy_validation/02_validation_engine.md
4. docs/contracts/validation_engine.contract.md
5. docs/prompts/validation_engine.prompt.md

Only edit these paths:
- backend/validation/

Do not:
- 做 RPC 查询
- 编译执行计划
- 改 CLI 显示逻辑
```
