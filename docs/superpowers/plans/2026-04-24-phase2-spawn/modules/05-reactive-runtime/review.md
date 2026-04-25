# Draft Summary

- `模块：` Reactive Runtime (`reactive_runtime`)
- `阶段：` Reactive and Safety
- `目标：` Implement module scope: 支持入场/止损/止盈触发; 与状态机契约对接

## 重点验收

- 支持入场/止损/止盈触发
- 与状态机契约对接
- entry trigger 测试

## 重点非目标

- 投资建议
- 策略评估
- 链下兜底决策

## 重点风险

- Reactive 负责事件驱动与 callback，不做自由决策
- 入场与出场都经由状态机
- 保留事件驱动逻辑与 callback 验证

# Full Draft

# Draft Task Card

## Header

- `模块：` Reactive Runtime (`reactive_runtime`)
- `负责人 agent：` Backend Architect
- `状态：` Draft
- `来源：` 用户目标 / contract / prompt / knowledge

## 1. 目标

- Implement module scope: 支持入场/止损/止盈触发; 与状态机契约对接

## 2. 验收标准

- [ ] 支持入场/止损/止盈触发
- [ ] 与状态机契约对接
- [ ] entry trigger 测试
- [ ] stop/take trigger 测试
- [ ] callback 验证测试

## 3. 非目标

- 投资建议
- 策略评估
- 链下兜底决策

## 4. 风险

- Reactive 负责事件驱动与 callback，不做自由决策
- 入场与出场都经由状态机
- 保留事件驱动逻辑与 callback 验证
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。

## 5. 依据

- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/05_reactive_contracts/01_reactive_runtime.md`
- `docs/contracts/reactive_runtime.contract.md`
- `docs/prompts/reactive_runtime.prompt.md`