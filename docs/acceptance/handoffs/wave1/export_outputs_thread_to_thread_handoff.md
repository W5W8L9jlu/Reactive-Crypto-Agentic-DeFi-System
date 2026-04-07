# Thread Handoff: export_outputs

- Upstream thread: `export_outputs`
- Downstream consumer status: `three-output envelope stable; stricter field contract still optional future work`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`

## Stable interfaces

- Entry point:
  - `export_outputs(...)`
- Stable wrappers:
  - `DecisionArtifact`
  - `ExecutionRecord`
  - `ExportOutputs`
  - `MachineTruth`

## Upstream producer path now evidenced

- `ValidationResult` from `backend.validation.validate_inputs_or_raise(...)` can be serialized into `DecisionArtifact`.
- `ExecutionPlan` from `backend.validation.models.ExecutionPlan` can be serialized into `ExecutionRecord`.
- The output bundle remains:
  - `machine_truth_json`
  - `audit_markdown`
  - `investment_memo`

## Constraints for downstream work

- Do not treat `audit_markdown` or `investment_memo` as replacement execution truth.
- Do not silently fill missing export inputs.
- If stricter field-level schema is needed, document it before replacing the current generic wrappers.

## Verification source

- `python -m unittest backend.export.test_export_outputs`
  - Result: `4 tests OK`

## Remaining TODOs

- Formal memo template remains unspecified in knowledge docs.
- Empty artifact/export semantics remain an explicit error path until the knowledge base defines them.
