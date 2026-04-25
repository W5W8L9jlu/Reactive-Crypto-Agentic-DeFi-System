# AGENTS.md

## 目标
在本仓库中，优先使用模块化知识库与 implementation contract；禁止默认读取完整 PRD。

## 启动规则
开始任何任务前，先识别目标模块，并按顺序读取：
1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. 对应 `docs/contracts/<module>.contract.md`
4. 对应 `docs/knowledge/...` 模块文件
5. 对应 `docs/prompts/<module>.prompt.md`

## 工作边界
- 一个任务只做一个模块，除非用户明确要求跨模块修改。
- 只改 prompt 指定的路径。
- 未在 knowledge/contract 中定义的行为，不得脑补实现。
- 需要跨模块改动时，先输出变更提案与影响面，再等待确认。

## 输出要求
每次完成任务时都给出：
- 修改了哪些文件
- 保持了哪些 invariants
- 跑了哪些验证
- 仍有哪些 TODO / 风险

## 默认工作方式
- 当用户在本仓库提出代码实现、重构、修复、验证或模块推进类任务时，默认先按本仓库的 workflow 走 `draft -> review -> approve -> spawn`；项目级拆分则走 `split -> review-split -> approve-split -> spawn-decomposition`。
- 只有在用户明确要求“直接实现”“跳过 workflow”或任务明显只是问答/调研时，才不启用该流程。
- 如果任务跨模块或需要更高风险决策，先用 workflow 收束到单模块，再继续执行。
- 如果任务无法唯一映射到单一 module_id，先进入 `Project Decomposition`，不要直接进入模块级 `draft`。

## 任务类型定义
- `代码实现 / 重构 / 修复 / 验证 / 模块推进`：需要改文件、跑测试、产出 diff 的任务。
- `问答 / 调研`：只需要解释、比较、分析或给建议，不要求改仓库的任务。
- 以“最终是否要改代码”为判断标准；要改代码就按 workflow 走，不改代码就按问答处理。
- 如果代码任务无法先落到单一模块，就先按拆分阶段处理。

## 禁止
- 读取完整 PRD 代替模块文档
- 在运行时重新编译 execution plan
- 让 AI 直接生成最终 calldata
- 吞掉核心业务异常
- 使用静默 fallback 掩盖缺失数据、错误配置或业务异常
- 用疯狂嵌套的 if/else 混淆核心业务逻辑
- 滥用 try/except，把测试适配、错误吞噬和业务流程混在一起

## Phase2 补充规则

当任务属于 Phase2 / Core Execution Loop 时，优先遵守：

1. `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
2. `docs/knowledge/08_delivery/04_phase2_prd_alignment.md`
3. `docs/knowledge/08_delivery/05_phase2_wave_plan.md`
4. `docs/contracts/phase2_interface_freeze.contract.md`
5. `docs/contracts/phase2_core_execution_loop.contract.md`
6. `docs/contracts/phase2_disabled_features.contract.md`
7. 当前 Wave Gate：`docs/acceptance/waves/P2_W*.wave_gate.md`
8. 对应 Phase2 prompt：`docs/prompts/phase2_*.prompt.md`
9. 对应目录级规则：`scaffold/backend/*/AGENTS.md`

Phase2 固定边界：
- single-chain only
- long-only only
- Uniswap V2-compatible only
- register-time `tokenIn` custody
- LocalExecutor first, ReactiveExecutorAdapter v1 later
- JSON and chain events are execution truth

Phase2 不做：
- complete Approval Flow queue
- Shadow Monitor daemon
- Aave Protection
- Uniswap V3 execution
- Hyperlane / cross-chain execution
- webhook alerts
- Postgres / Redis default path

Phase2 执行顺序：
- W0: Interface Freeze
- W1: Offline Core Loop
- W2: Local Chain Mock Loop
- W3: Fork/Testnet E2E Loop
- W4: Reactive + Hardening + Export Closure

Phase2 任务不得绕过当前 Wave Gate。

## 补充
- Phase2 任务若 knowledge/contract 未定义，按以下根目录文档顺序补充查阅：
  1. `prd_final_v11_phase2_core_execution_loop.md`（Phase2 总边界）
  2. `prd_phase2_lite_agile_v1.md`（Phase2 敏捷开发输入）
  3. `phase2_wave_development_plan_v1.md`（W0-W4 Wave 执行计划）
  4. `phase2_vibe_coding_development_paradigm_v1.md`（Phase2 文档生产范式）
- `prd_final_v10.md` 仅作为历史/Phase1 参考；当它与 Phase2 v11 文档冲突时，以 `prd_final_v11_phase2_core_execution_loop.md` 为准。
