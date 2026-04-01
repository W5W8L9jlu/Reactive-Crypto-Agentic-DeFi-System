# AGENTS.md

对该目录的改动，优先遵守：
- `docs/knowledge/05_reactive_contracts/02_investment_state_machine.md`
- `docs/knowledge/05_reactive_contracts/03_emergency_force_close.md`
- `docs/contracts/investment_state_machine_contract.contract.md`
- `docs/contracts/emergency_force_close.contract.md`

规则：
- 状态机只能 PendingEntry -> ActivePosition -> Closed
- Closed 不能再次触发
- force-close 先写 Closed 再卖出
