# Draft Summary

- `模块：` PreRegistrationCheck (`pre_registration_check`)
- `阶段：` Decision Boundary
- `目标：` Implement module scope: 复核 reserve/slippage/balance/allowance/gas/TTL; 给出明确 abort reason

## 重点验收

- 复核 reserve/slippage/balance/allowance/gas/TTL
- 给出明确 abort reason
- gas 太高拒绝

## 重点非目标

- 运行时 require 检查
- 触发后重新决策

## 重点风险

- 注册前检查只信 RPC
- 必须校验 Gas / Expected Profit
- 只负责注册时可行性，不做运行时最终防守

# Full Draft

# Draft Task Card

## Header

- `模块：` PreRegistrationCheck (`pre_registration_check`)
- `负责人 agent：` Backend Architect
- `状态：` Draft
- `来源：` 用户目标 / contract / prompt / knowledge

## 1. 目标

- Implement module scope: 复核 reserve/slippage/balance/allowance/gas/TTL; 给出明确 abort reason

## 2. 验收标准

- [ ] 复核 reserve/slippage/balance/allowance/gas/TTL
- [ ] 给出明确 abort reason
- [ ] gas 太高拒绝
- [ ] TTL 过期拒绝
- [ ] allowance/balance 不足拒绝

## 3. 非目标

- 运行时 require 检查
- 触发后重新决策

## 4. 风险

- 注册前检查只信 RPC
- 必须校验 Gas / Expected Profit
- 只负责注册时可行性，不做运行时最终防守
- 失败快速抛异常
- 不得向其他模块偷偷引入新行为。
- 需要跨模块接口时，只能通过显式 schema / interface / adapter 接入。
- 无法从 knowledge files 证明的行为，必须保留 `TODO:` 或抛出明确异常。

## 5. 依据

- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`
- `docs/knowledge/03_strategy_validation/03_pre_registration_check.md`
- `docs/contracts/pre_registration_check.contract.md`
- `docs/prompts/pre_registration_check.prompt.md`