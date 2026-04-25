# Phase2 Batch 2 Consistency Review

> Lightweight checklist before writing P0 module prompts. This is not a new documentation layer.

## Scope

Review Batch 2 outputs:

- `scaffold/backend/*/AGENTS.md` Phase2 guardrails
- Phase2 interface contracts added after W0
- W1-W4 thread evidence templates

## Checklist

- [ ] P0 prompts use `docs/contracts/phase2_interface_freeze.contract.md` as the interface truth source.
- [ ] `scaffold/backend/validation/AGENTS.md` does not imply RPC access for Validation Engine.
- [ ] `scaffold/backend/execution/AGENTS.md` does not allow trigger-time compilation.
- [ ] `scaffold/backend/contracts/AGENTS.md` does not introduce Uniswap V3, Aave, or cross-chain execution.
- [ ] `scaffold/backend/export/AGENTS.md` preserves JSON / Audit Markdown / Investment Memo separation.
- [ ] `docs/contracts/phase2_price_oracle_adapter.contract.md` defines `priceE18` direction.
- [ ] `docs/contracts/phase2_event_syncer.contract.md` defines event-to-`ExecutionRecord` mapping.
- [ ] W1-W4 evidence templates can record commands, test evidence, acceptance mapping, deviations, risks, and gate recommendation.

## Review Result

- Result: `PASS / HOLD`
- Reviewer:
- Date:
- Notes:
