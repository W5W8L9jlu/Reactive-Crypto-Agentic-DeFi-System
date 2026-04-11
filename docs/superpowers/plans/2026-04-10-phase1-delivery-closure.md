# Phase1 Delivery Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove CLI placeholder routes and close P0 blockers so Phase1 can be evaluated as user-deliverable.

**Architecture:** Keep business logic in existing domain modules (`decision`, `execution`, `export`, `monitor`) and upgrade `backend/cli` to become a real routing/persistence surface. Persist user-facing state in local SQLite, assemble requests for main-chain flow from stored strategies, and expose operator diagnostics via CLI doctor checks.

**Tech Stack:** Python 3.10+, Typer, Rich, sqlite3, Pydantic v2, pytest

---

### Task 1: Runtime Persistence Layer

**Files:**
- Create: `backend/cli/runtime_store.py`
- Modify: `backend/cli/wiring.py`
- Test: `backend/cli/test_runtime_store.py`

- [x] Define SQLite-backed repositories for strategy records and intent artifacts.
- [x] Add read/write methods required by strategy/approval/execution/export/monitor commands.
- [x] Keep schemas JSON-centric to preserve machine-truth payloads without lossy transforms.
- [x] Add unit tests for CRUD and retrieval error cases.

### Task 2: Wire Real CLI Handlers

**Files:**
- Modify: `backend/cli/wiring.py`
- Modify: `backend/cli/app.py`
- Test: `backend/cli/test_wiring.py`
- Test: `backend/cli/test_app.py`

- [x] Replace placeholder handlers for strategy, approval, execution show/logs, export, monitor.
- [x] Implement user-mode decision request assembly from stored strategy records (no mandatory request-file).
- [x] Keep advanced override via request-file env for deterministic replay.
- [x] Persist decision run outputs and make downstream commands consume persisted artifacts.

### Task 3: Doctor + Smoke Command Surface

**Files:**
- Modify: `backend/cli/app.py`
- Modify: `backend/cli/wiring.py`
- Create: `backend/cli/test_doctor.py`

- [x] Add `agent-cli doctor` command.
- [x] Report missing runtime env, contract artifact path, and RPC connectivity checks.
- [x] Return actionable diagnostics while avoiding secret disclosure.

### Task 4: Phase1 Gate Tests

**Files:**
- Create: `backend/cli/test_phase1_gate.py`
- Modify: `backend/cli/test_force_close_integration.py`
- Modify: `scripts/run_phase1_regression.py`

- [x] Add CLI-focused gate tests that fail on placeholder behavior.
- [x] Validate approval/raw consistency, export consistency, and monitor/force-close critical path.
- [x] Ensure regression runner can execute gate checks in non-chain and with-chain modes.

### Task 5: Verification

**Files:**
- Modify: `docs/acceptance/threads/wave5/00_generic.test_evidence.md`

- [x] Run targeted CLI tests.
- [x] Run `backend/cli + backend/decision + backend/execution` regression.
- [x] Run command-line smoke checks for strategy/decision/approval/execution/export/monitor paths.

> Note: current machine still lacks `SEPOLIA_PRIVATE_KEY` and `REACTIVE_INVESTMENT_COMPILER_ADDRESS`; live Sepolia operator smoke remains environment-blocked until secrets are provided.
