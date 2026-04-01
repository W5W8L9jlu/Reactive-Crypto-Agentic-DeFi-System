# CLI Surface

This module owns only the CLI surface for:

- routing
- presentation
- manual entrypoints

It does not own:

- business calculations
- state-machine logic
- provider logic

## Command Groups

- `strategy show`
- `decision run`
- `approval show`
- `approval approve`
- `approval reject`
- `execution show`
- `export render --kind <machine_truth_json|audit_markdown|investment_memo>`
- `monitor alerts`
- `monitor takeover`

## Adapter Boundary

Every command resolves to an explicit adapter seam through `CliAdapters`.
If an adapter is not wired, the CLI raises `MissingCliAdapterError` with a
clear TODO instead of inventing cross-module behavior.

## Runtime Assumptions

- `build_app()` requires `typer`
- Rich console output requires `rich`

If those dependencies are absent, the module raises `MissingCliDependencyError`
instead of silently falling back to hidden behavior.
