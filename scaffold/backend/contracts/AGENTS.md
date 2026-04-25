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

## Phase2 Guardrails - Contracts

Phase2 contracts implement a single-chain, long-only, Uniswap V2-compatible investment state machine.

Must:
- Use register-time `tokenIn` custody.
- Implement `PendingEntry -> ActivePosition -> Closed`.
- Emit stable events for EventSyncer.
- Use an authorized executor for `executeReactiveTrigger`.
- Use price oracle adapter semantics from `docs/contracts/phase2_price_oracle_adapter.contract.md`.
- Keep `emergencyForceClose` interface reserved.

Must not:
- Implement Uniswap V3.
- Implement cross-chain messaging.
- Implement Aave protection.
- Allow `Closed` intent to execute again.
- Let `PendingEntry` TTL or `maxEntryGasPriceWei` block `ActivePosition` exits.
