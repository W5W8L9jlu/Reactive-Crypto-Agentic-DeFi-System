# Thread Acceptance: validation_engine

- Module / prompt: `validation_engine`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`
- Working directory: `backend/validation`
- Status: `PASS_WITH_NOTES`

## Why this thread was reworked

- The Wave 1 gate required an explicit contract-facing seam instead of generic object/schema gating only.
- The current test suite already expected `contract_bindings`, but the implementation did not provide them.

## What is now evidenced

- `ValidationResult` now carries `contract_bindings`.
- Successful validation explicitly binds:
  - template identity into strategy intent identity/version/mode
  - trade intent identity into execution plan identity
  - `max_slippage_bps`, `ttl_seconds`, `stop_loss_bps`, and `take_profit_bps` into `ExecutionPlan.hard_constraints`
- Invalid validation results keep `contract_bindings` empty.

## Invariants preserved

- Validation remains Pydantic v2 based.
- Validation still raises or reports explicit validation/domain errors.
- No RPC checks were added.
- No calldata compilation was added.

## Verification

- `python -m unittest backend.validation.test_validation_engine`
  - Result: `6 tests OK`

## Remaining notes

- These bindings freeze the validated seam into `ExecutionPlan`, not final on-chain register payload compilation.
- Empty `allowed_pairs` / `allowed_dexes` behavior remains an explicit `MissingValidationSpecError` TODO path.
