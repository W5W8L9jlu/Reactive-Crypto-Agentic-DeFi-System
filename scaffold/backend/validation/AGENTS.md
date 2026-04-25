# AGENTS.md

对该目录的改动，优先遵守：
- `docs/knowledge/03_strategy_validation/02_validation_engine.md`
- `docs/knowledge/03_strategy_validation/03_pre_registration_check.md`
- `docs/contracts/validation_engine.contract.md`
- `docs/contracts/pre_registration_check.contract.md`

规则：
- Validation 必须基于 Pydantic v2
- PreRegistrationCheck 只信 RPC
- 不吞异常

## Phase2 Guardrails - Validation

This module is offline-only for Validation Engine work.

Must:
- Validate `StrategyTemplate`, `StrategyIntent`, `TradeIntent`, and `ValidationResult` through Pydantic v2 models.
- Enforce Phase2 scope: single-chain, long-only, Uniswap V2-compatible.
- Return `ApprovalRequiredError` when `requires_manual_approval=true`.
- Reject `crosschain=true`.
- Reject `dex != uniswap_v2`.
- Reject `side != buy`.

Must not:
- Access RPC from Validation Engine.
- Read pool reserves.
- Estimate gas.
- Build calldata.
- Register on-chain intents.
- Implement approval queues.
- Implement Shadow Monitor behavior.
