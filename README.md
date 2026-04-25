# Reactive Crypto Agentic DeFi System

本仓库是一个面向 Codex / 多 agent 协作开发的 DeFi 自动执行系统文档与代码工程包。

根目录 `README.md` 是给人看的入口导览；真正约束 agent 行为的是 `AGENTS.md`、`docs/contracts/`、`docs/prompts/`、`scaffold/backend/*/AGENTS.md` 和 `docs/acceptance/`。

## 当前阶段

当前主线是 Phase2：Core Execution Loop。

Phase2 的目标是打通一个最小可用的单链条件执行闭环：

```text
TradeIntent
-> Validation
-> PreRegistrationCheck
-> ExecutionCompiler
-> registerInvestmentIntent
-> PendingEntry
-> ActivePosition
-> Closed
-> ExecutionRecord
-> JSON / Audit Markdown / Investment Memo export
```

Phase2 固定边界：

- single-chain only
- long-only only
- Uniswap V2-compatible only
- register-time `tokenIn` custody
- LocalExecutor first, ReactiveExecutorAdapter v1 later
- JSON and chain events are execution truth

Phase2 不做完整 Approval Flow、Shadow Monitor daemon、Aave Protection、Uniswap V3、Hyperlane / cross-chain、webhook alerts、Postgres / Redis 默认路径。

## 文档体系

```text
AGENTS.md
 └─ 仓库级 agent 执行规则

docs/knowledge/
 └─ 模块化知识库：系统不变量、领域模型、模块背景、Phase/Wave 计划

docs/contracts/
 └─ implementation contract：每个模块必须实现什么、禁止什么、如何验收

docs/prompts/
 └─ agent-ready task prompt：给 Codex/agent 的具体任务包

scaffold/backend/*/AGENTS.md
 └─ 目录级 guardrails：约束 agent 在具体代码目录内的行为

docs/acceptance/
 └─ 验收体系：Wave Gate、thread evidence、handoff、Go/No-Go
```

## 人类阅读顺序

如果你是新接手 Phase2 的开发者，建议按这个顺序读：

1. `AGENTS.md`
2. `docs/knowledge/01_core/01_system_invariants.md`
3. `docs/knowledge/01_core/02_domain_models.md`
4. `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
5. `docs/knowledge/08_delivery/04_phase2_prd_alignment.md`
6. `docs/knowledge/08_delivery/05_phase2_wave_plan.md`
7. `docs/contracts/phase2_interface_freeze.contract.md`
8. `docs/contracts/phase2_core_execution_loop.contract.md`
9. `docs/contracts/phase2_disabled_features.contract.md`
10. 当前 Wave Gate，例如 `docs/acceptance/waves/P2_W1.wave_gate.md`
11. 对应模块 contract / prompt / scaffold AGENTS

如果只想了解 Phase2 为什么这样拆，可以先读根目录下：

- `prd_final_v11_phase2_core_execution_loop.md`
- `prd_phase2_lite_agile_v1.md`
- `phase2_wave_development_plan_v1.md`
- `phase2_vibe_coding_development_paradigm_v1.md`

`prd_final_v10.md` 仅作为历史 / Phase1 参考；当它与 Phase2 v11 文档冲突时，以 `prd_final_v11_phase2_core_execution_loop.md` 为准。

## Agent 工作入口

普通模块任务不要直接喂完整 PRD。推荐让 agent 按以下顺序读取：

```text
core invariants
-> domain models
-> Phase2 wave map / PRD alignment
-> module knowledge
-> module contract
-> Phase2 core contracts
-> current Wave Gate
-> module prompt
-> scaffold/backend/*/AGENTS.md
```

一个 prompt 如果没有明确这些字段，不应视为 agent-ready：

- Read First
- Goal
- Allowed Paths
- Forbidden Paths
- Must Not Implement
- Inputs / Outputs
- Required Errors
- Required Tests
- Smoke Command
- Delivery Evidence
- Acceptance Criteria

## Phase2 Wave

Phase2 按 Wave 收口，而不是按孤立模块完成收口：

```text
W0: Interface Freeze
W1: Offline Core Loop
W2: Local Chain Mock Loop
W3: Fork/Testnet E2E Loop
W4: Reactive + Hardening + Export Closure
```

每个 Wave 必须留下证据：

```text
docs/acceptance/threads/phase2_wave*/
```

每个 thread 至少应包含：

- delivery note
- test evidence
- thread acceptance

## 关键原则

- 不读完整 PRD 代替模块文档。
- 不跨模块发散。
- 不脑补未在 knowledge / contract / prompt 中定义的行为。
- 不让 AI 生成最终 calldata、签名或控制资金。
- 不在触发时重新编译 execution plan。
- 不使用静默 fallback 掩盖错误。
- 不用复杂 if/else 和滥用 try/except 混淆业务逻辑。
- 不以“文档完成”代替 Wave Gate 通过。

## 常用验证

```powershell
python scripts/workflow.py audit-manifest --strict
python scripts/workflow.py check --all --execute --strict
```

模块级验证以对应 `docs/prompts/*.prompt.md` 和当前 Wave Gate 中的命令为准。
