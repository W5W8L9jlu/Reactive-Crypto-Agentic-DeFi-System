# Phase2 Minimal Documentation Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the minimum Phase2 documentation package that lets multiple agents develop the Core Execution Loop without inventing interfaces in parallel.

**Architecture:** Reuse the Phase1 documentation skeleton and add Phase2 deltas only where they are needed. Wave 0 freezes interfaces first; Waves 1-4 then provide vertical smoke-test gates from offline fixtures to Reactive hardening.

**Tech Stack:** Markdown documentation, existing `docs/knowledge`, `docs/contracts`, `docs/prompts`, `docs/acceptance`, and `scaffold/backend/*/AGENTS.md` conventions.

---

### Task 1: Phase2 Materials Map

**Files:**
- Create: `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
- Create: `docs/knowledge/08_delivery/05_phase2_wave_plan.md`
- Create: `docs/knowledge/09_testing/04_phase2_wave_smoke_tests.md`
- Modify: `docs/knowledge/08_delivery/04_phase2_prd_alignment.md`

- [ ] **Step 1: Record source hierarchy**

Document that PRD v11 is the boundary source, PRD-Lite is the daily development source, the Wave plan is the delivery cadence, and the vibe coding paradigm is the documentation production rule.

- [ ] **Step 2: Record Wave/Lane map**

Document W0-W4 and Lane A-F, including which contracts each lane consumes.

- [ ] **Step 3: Update PRD alignment**

Replace the old Phase2 cross-chain wording with Core Execution Loop scope: single-chain, long-only, Uniswap V2-compatible, register-time custody.

### Task 2: W0 Interface Freeze Contracts

**Files:**
- Create: `docs/contracts/phase2_interface_freeze.contract.md`
- Create: `docs/contracts/phase2_core_execution_loop.contract.md`
- Create: `docs/contracts/phase2_disabled_features.contract.md`

- [ ] **Step 1: Define frozen interfaces**

Freeze Pydantic schemas, Solidity ABI/events, DB schema, CLI skeleton, fixtures, error taxonomy, and disabled feature behavior.

- [ ] **Step 2: Define the Core Execution Loop**

Define the only Phase2 success path: `TradeIntent -> Validation -> PreRegistrationCheck -> ExecutionCompiler -> registerInvestmentIntent -> PendingEntry -> ActivePosition -> Closed -> ExecutionRecord -> Export`.

- [ ] **Step 3: Define disabled features**

Require approval flow, shadow monitor daemon, Aave, Uniswap V3, cross-chain, webhooks, and Postgres/Redis to fail fast or remain as disabled interfaces.

### Task 3: Phase2 Gates

**Files:**
- Modify: `docs/acceptance/00_overview/08_phase2_go_no_go.md`
- Create: `docs/acceptance/waves/P2_W0.wave_gate.md`
- Create: `docs/acceptance/waves/P2_W1.wave_gate.md`
- Create: `docs/acceptance/waves/P2_W2.wave_gate.md`
- Create: `docs/acceptance/waves/P2_W3.wave_gate.md`
- Create: `docs/acceptance/waves/P2_W4.wave_gate.md`

- [ ] **Step 1: Update Go/No-Go**

Make Phase2 GO depend on the Core Execution Loop closing, all Wave Gates passing, disabled features failing fast, and export evidence matching Machine Truth.

- [ ] **Step 2: Add Wave Gates**

Each Wave Gate must include goal, scope, allowed paths, forbidden paths, smoke tests, exit criteria, delivery evidence, and rollback/no-go conditions.

### Task 4: Delivery Playbook

**Files:**
- Modify: `docs/guides/06_phase2_delivery_playbook.md`

- [ ] **Step 1: Replace module-sequential guidance**

Move from module order to Wave Gate order: W0 freeze, W1 offline, W2 local chain, W3 fork/testnet, W4 Reactive/hardening/export closure.

- [ ] **Step 2: Preserve module context workflow**

Keep the rule that agents read core invariants, domain models, relevant knowledge, contract, prompt, current Wave Gate, and scaffold AGENTS.md.

### Task 5: Verify Documentation Package

**Files:**
- Verify all created/modified files above.

- [ ] **Step 1: List expected files**

Run: `Get-ChildItem docs/knowledge,docs/contracts,docs/acceptance/waves,docs/guides -Recurse -File | Select-Object FullName`

- [ ] **Step 2: Check Phase2 scope language**

Run: `Select-String -Path docs/acceptance/00_overview/08_phase2_go_no_go.md,docs/guides/06_phase2_delivery_playbook.md -Pattern "single-chain|long-only|Uniswap V2|Core Execution Loop|cross-chain"`

- [ ] **Step 3: Optional workflow audit**

Run: `python scripts/workflow.py audit-manifest --strict`

Expected: existing manifest audit passes or reports only pre-existing manifest coverage gaps.
