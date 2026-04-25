# Draft Summary

- `模块：` Execution Layer (`execution_layer`)
- `阶段：` Registration and Execution
- `目标：` Implement module scope: 能消费 runtime trigger 并记录执行回执; ExecutionRecord 与链上回执一致

## 重点验收

- 能消费 runtime trigger 并记录执行回执
- ExecutionRecord 与链上回执一致
- 执行成功回执测试

## 重点非目标

- 自由决策
- 重新编译
- 替代状态机

## 重点风险

- 不在校验通过后立即 swap
- 只在 Reactive 触发后执行
- 只负责链上调用和回执记录

# Full Draft

# Draft Task Card

## Header

- `模块：` Execution Layer (`execution_layer`)
- `负责人 agent：` Solidity Smart Contract Engineer
- `状态：` Draft
- `来源：` 用户目标 / contract / prompt / knowledge

## 1. 目标

- Implement module scope: 能消费 runtime trigger 并记录执行回执; ExecutionRecord 与链上回执一致

## 2. 验收标准

- [ ] 能消费 runtime trigger 并记录执行回执
- [ ] ExecutionRecord 与链上回执一致
- [ ] 执行成功回执测试
- [ ] 链上失败回执测试
- [ ] record/export 一致性测试

## 3. 非目标

- 自由决策
- 重新编译
- 替代状态机

## 4. 风险

- 不在校验通过后立即 swap
- 只在 Reactive 触发后执行
- 只负责链上调用和回执记录
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。

## 5. 依据

- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/04_execution/02_execution_layer.md`
- `docs/contracts/execution_layer.contract.md`
- `docs/prompts/execution_layer.prompt.md`