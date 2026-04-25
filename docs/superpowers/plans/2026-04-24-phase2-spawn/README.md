# 2026-04-24-phase2-spawn

This directory is a Codex-ready project decomposition spawn bundle.

## Read Order

- `README.md`
- `manifest.json`
- `01-product-manager.json`
- `02-workflow-architect.json`
- `03-software-architect.json`
- `04-senior-project-manager.json`
- `05-technical-writer.json`

## How To Use

- Read `manifest.json` to inspect the approved split, spawn groups, and source proposal.
- Read the role files in order.
- For each role file, copy `spawn_agent.message` and `spawn_agent.items` into the Codex session that will launch the agent.
- The `Technical Writer` file is the final synthesis step and depends on the review pack.
- If module bundles are present under `modules/`, run each module through draft, review, approved, and spawn in order.