# AGENTS.md

对该目录的改动，优先遵守：
- `docs/knowledge/06_cli_ops/01_cli_surface.md`
- `docs/knowledge/03_strategy_validation/04_approval_flow.md`
- `docs/contracts/cli_surface.contract.md`
- `docs/contracts/approval_flow.contract.md`

规则：
- 默认显示 battle card，不直接显示 raw JSON
- CLI 只做路由/展示/操作入口

## Phase2 Guardrails - CLI

CLI exposes Phase2 Core Execution Loop only.

Must:
- Support `decision dry-run` / `decision run`.
- Support `execution register` / `execution show` / `execution logs`.
- Support `export json` / `export markdown` / `export memo`.
- Render disabled feature errors clearly.
- Keep approval commands stubbed or disabled in Phase2.

Must not:
- Implement full approval flow.
- Implement monitor daemon commands as completed features.
- Trigger manual force-close unless contract state and Phase2 gate allow it.
- Treat Audit Markdown as execution truth.
