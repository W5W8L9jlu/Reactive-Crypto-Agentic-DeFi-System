# Phase2 Disabled Features Contract

## Module Purpose

Prevent Phase3, Phase3.5, and Phase4 capabilities from leaking into the Phase2 main path. Disabled features may have interfaces or skeletons, but they must fail fast when invoked.

## Phase2 Scope

The following features are disabled in Phase2:

- complete Approval Flow queue
- ApprovalBattleCard interaction
- Shadow Monitor daemon
- Aave Protection
- Uniswap V3 execution
- Hyperlane / cross-chain execution
- webhook alerts
- Postgres / Redis deployment path

## Required Defaults

```yaml
features:
  approval_flow: false
  shadow_monitor: false
  aave_protection: false
  uniswap_v3: false
  crosschain: false
  webhook_alerts: false
```

## Required Behavior

- `crosschain == true` is rejected before registration.
- `dex == uniswap_v3` is rejected before registration.
- `requires_manual_approval == true` raises `ApprovalRequiredError` and aborts registration.
- Aave-specific checks do not run in the Phase2 main path.
- Shadow Monitor daemon is not required for Phase2 GO.
- `emergencyForceClose` may exist as a contract escape hatch.
- webhook paths may expose an interface only if disabled by default.

## Forbidden Behavior

- Do not silently ignore disabled feature requests.
- Do not partially execute disabled feature paths.
- Do not map disabled features to fallback behavior that changes execution semantics.
- Do not require disabled feature infrastructure for Phase2 tests.

## Tests

Tests must prove disabled requests fail fast:

- approval-required intent
- cross-chain intent
- Uniswap V3 intent
- Aave protection path
- webhook alert path
- Shadow Monitor daemon path

## Acceptance Criteria

- disabled features cannot enter the Core Execution Loop.
- each disabled feature returns a clear domain error.
- disabled feature tests are part of W4 hardening evidence.
