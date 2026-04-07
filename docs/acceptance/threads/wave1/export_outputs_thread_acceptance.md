# Thread Acceptance: export_outputs

- Module / prompt: `export_outputs`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`
- Working directory: `backend/export`
- Status: `PASS_WITH_NOTES`

## Why this thread was reworked

- The Wave 1 gate recorded that export evidence stopped at the output envelope and had no demonstrated upstream producer path.

## What is now evidenced

- `export_outputs(...)` is exercised with real upstream typed objects:
  - `ValidationResult` produced by `backend.validation.validate_inputs_or_raise(...)`
  - `ExecutionPlan` produced by `backend.validation.models.ExecutionPlan`
- The exported machine truth keeps those upstream objects as serialized input facts.
- Audit markdown remains a direct excerpt of machine truth leaves.

## Invariants preserved

- `machine_truth_json` remains the only execution truth artifact.
- `audit_markdown` remains derived excerpt output only.
- `investment_memo` remains derived narrative output only.
- No strategy, execution, or approval logic was added to this module.

## Verification

- `python -m unittest backend.export.test_export_outputs`
  - Result: `4 tests OK`

## Remaining notes

- `DecisionArtifact` and `ExecutionRecord` still use generic payload wrappers.
- This thread now has real upstream integration evidence, but field-level envelope hardening remains future work if a stricter export contract is required.
