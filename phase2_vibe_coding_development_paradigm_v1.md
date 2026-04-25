# Phase2 Vibe Coding 开发范式

版本：v1  
适用阶段：Phase2 / Core Execution Loop  
用途：指导 Phase2 如何沿用 Phase1 的 `knowledge -> contracts -> prompts -> acceptance -> scaffold/AGENTS` 范式，并加入 Wave-based 并行开发。  
定位：这是开发范式文档，不是 PRD，不是完整技术规格书。

---

## 0. 核心结论

Phase2 不另起一套全新的 `agent_work / issue_cards` 体系。

Phase2 继续沿用 Phase1 已经形成的 vibe coding 文档结构：

```text
PRD / 总设计
 └─ docs/knowledge：拆成模块知识
    └─ docs/contracts：收敛成实现合同
       └─ docs/prompts：变成 agent 可执行任务
          └─ scaffold/*/AGENTS.md：落到代码目录规则
             └─ docs/acceptance：开发后留下验收证据
```

Phase2 要做的不是推翻这套结构，而是在同一套骨架上补充：

```text
Phase2 scope / goal
Phase2 module delta
Phase2 implementation contract
Phase2 agent prompt
Phase2 wave gate
Phase2 acceptance evidence
```

最终原则：

> Phase1 留下的是基础骨架；Phase2 做的是在同一套骨架上补 Phase2 增量合同、任务包、Wave Gate 和验收证据。

---

## 1. 为什么不能直接把 PRD 或 Wave Plan 丢给 code agent

PRD 和 Wave Plan 面向人类规划，不适合直接驱动 code agent。

Code agent 需要的是：

```text
1. 做什么
2. 不做什么
3. 改哪里
4. 不许改哪里
5. 输入输出是什么
6. 怎么验证
7. 怎么判定完成
8. 交付证据写到哪里
```

如果某个模块的 `knowledge + contract + prompt + scaffold + acceptance` 不能明确回答这八个问题，那么该模块还不是 agent-ready。

---

## 2. Phase2 文档层级

Phase2 文档继续使用 Phase1 五层流水线。

### 2.1 knowledge：模块知识层

位置：

```text
docs/knowledge/**
```

职责：

```text
解释模块是什么
解释业务边界
解释 Phase2 相比 Phase1 的 delta
解释模块和其他模块的依赖
```

不负责：

```text
不写具体允许改哪些文件
不写完整任务 prompt
不写交付证据
不替代 implementation contract
```

### 2.2 contracts：实现合同层

位置：

```text
docs/contracts/*.contract.md
```

职责：

```text
定义该模块必须实现什么
定义输入输出
定义禁止事项
定义验收边界
定义测试命令
定义 Phase2 特有硬约束
```

这是 code agent 的主要实现依据之一。

### 2.3 prompts：执行任务层

位置：

```text
docs/prompts/*.prompt.md
```

职责：

```text
告诉 code agent 当前任务要读哪些上下文
告诉 code agent 只允许修改哪些路径
告诉 code agent 禁止修改哪些路径
告诉 code agent 必须运行什么验证
告诉 code agent 交付证据写在哪里
```

Prompt 是真正可投喂给 code agent 的文件。

### 2.4 scaffold / AGENTS：目录级护栏层

位置：

```text
scaffold/backend/*/AGENTS.md
```

职责：

```text
为每个代码目录提供局部规则
约束 agent 在该目录中的实现风格
禁止越界实现
保持 Phase1 与 Phase2 的目录习惯一致
```

如果 Phase2 没有新增目录，优先复用已有 AGENTS.md。  
如果 Phase2 新增目录，才补新的局部 AGENTS.md。

### 2.5 acceptance：验收证据层

位置：

```text
docs/acceptance/**
```

职责：

```text
记录单 thread 是否完成
记录测试证据
记录 Wave Gate 是否通过
记录风险和 handoff
记录 Phase2 Go / No-Go
```

Phase2 并行开发必须依赖 acceptance 层收口，否则多个 agent 会各自完成局部任务但无法集成。

---

## 3. Phase2 不做平行文档体系

不要新增这些结构：

```text
agent_work/
phase2_knowledge/
phase2_contracts/
phase2_prompts/
issues/
```

除非整个项目决定废弃 Phase1 文档范式。当前不建议这么做。

正确做法是：

```text
已有模块：在现有 knowledge / contract / prompt 中补 Phase2 delta
新增模块：在现有目录下新增对应文件
Wave 并行：新增 wave map 和 wave gate
验收证据：继续进入 docs/acceptance
```

---

## 4. 复用、更新、新建的判断标准

### 4.1 可以直接复用的内容

这些属于全阶段不变量，通常不需要为 Phase2 重写：

```text
AI 不直接生成 calldata
AI 不直接签名
RPC 是执行真相
JSON 是 Machine Truth
Audit Markdown 只摘抄，不生成新结论
Investment Memo 不影响执行
Reactive 不做自由决策
Pydantic / schema 是核心模型边界
CLI-only
执行层不信第三方索引 API
```

推荐继续放在：

```text
docs/knowledge/01_core/01_system_invariants.md
```

### 4.2 应该更新现有文件的情况

如果 Phase2 是增强已有模块，应更新原文件，而不是另建重复文件。

例如：

```text
execution_compiler
validation_engine
pre_registration_check
export_outputs
cli_surface
reactive_runtime
```

推荐做法：

```text
docs/knowledge/<module>.md
  增加 “Phase2 Delta” 小节

docs/contracts/<module>.contract.md
  增加 “Phase2 Contract” 小节

docs/prompts/<module>.prompt.md
  增加 “Phase2 Wave Task” 小节
```

### 4.3 应该新增文件的情况

如果 Phase2 引入新增概念、显著新增职责，或需要独立验收，则新增文件。

Phase2 建议新增的文件类型：

```text
Wave parallelization map
Interface freeze record
InvestmentIntentPayload contract
LocalExecutor contract
EventSyncer contract
UniswapV2PriceOracleAdapter contract
Disabled feature handling
Phase2 Wave Gate
Phase2 Go / No-Go
```

---

## 5. Phase2 推荐目录增量

### 5.1 knowledge 增量

```text
docs/knowledge
 ├─ 00_meta
 │  ├─ 02_phase2_split_manifest.json
 │  ├─ 03_phase2_wave_parallelization_map.md
 │  ├─ 04_phase2_materials_audit.md
 │  └─ 05_phase2_doc_delta_plan.md
 │
 ├─ 01_core
 │  ├─ 04_phase2_system_invariants_delta.md
 │  └─ 05_phase2_interface_freeze.md
 │
 ├─ 03_strategy_validation
 │  ├─ 05_phase2_validation_engine_delta.md
 │  └─ 06_phase2_pre_registration_check_delta.md
 │
 ├─ 04_execution
 │  ├─ 03_phase2_execution_compiler_delta.md
 │  ├─ 04_phase2_execution_runtime.md
 │  └─ 05_phase2_event_syncer.md
 │
 ├─ 05_reactive_contracts
 │  ├─ 04_phase2_investment_state_machine.md
 │  ├─ 05_phase2_price_oracle_adapter.md
 │  └─ 06_phase2_local_executor.md
 │
 ├─ 08_delivery
 │  ├─ 05_phase2_wave_plan.md
 │  ├─ 06_phase2_disabled_features.md
 │  └─ 07_phase2_delivery_playbook.md
 │
 └─ 09_testing
    ├─ 03_phase2_test_plan.md
    └─ 04_phase2_wave_smoke_tests.md
```

说明：

- 如果已有同名或等价文件，优先更新，不重复创建。
- `phase2_materials_audit.md` 必须先做，用于判断哪些文件已经存在、哪些需要补。
- `phase2_doc_delta_plan.md` 用于记录每个模块是 `reuse / update / split / create / deprecate`。

---

### 5.2 contracts 增量

```text
docs/contracts
 ├─ phase2_interface_freeze.contract.md
 ├─ phase2_core_execution_loop.contract.md
 ├─ phase2_validation_engine.contract.md
 ├─ phase2_pre_registration_check.contract.md
 ├─ phase2_execution_compiler.contract.md
 ├─ phase2_investment_state_machine.contract.md
 ├─ phase2_price_oracle_adapter.contract.md
 ├─ phase2_local_executor.contract.md
 ├─ phase2_event_syncer.contract.md
 ├─ phase2_cli_execution.contract.md
 ├─ phase2_export_outputs.contract.md
 └─ phase2_disabled_features.contract.md
```

是否独立新建取决于现有文件情况：

```text
如果已有 execution_compiler.contract.md 且职责清晰：
  更新原文件，增加 Phase2 Contract

如果现有合同太混杂或包含 Phase1/Phase3 大量内容：
  新建 phase2_execution_compiler.contract.md
```

---

### 5.3 prompts 增量

```text
docs/prompts
 ├─ phase2_wave0_interface_freeze.prompt.md
 ├─ phase2_validation_engine.prompt.md
 ├─ phase2_pre_registration_check.prompt.md
 ├─ phase2_execution_compiler.prompt.md
 ├─ phase2_investment_state_machine.prompt.md
 ├─ phase2_price_oracle_adapter.prompt.md
 ├─ phase2_local_executor.prompt.md
 ├─ phase2_event_syncer.prompt.md
 ├─ phase2_cli_execution.prompt.md
 ├─ phase2_export_outputs.prompt.md
 └─ phase2_disabled_features.prompt.md
```

每个 prompt 必须是 agent-ready。

---

### 5.4 acceptance 增量

```text
docs/acceptance
 ├─ 00_overview
 │  └─ 08_phase2_go_no_go.md
 │
 ├─ 05_prefilled_wave_packets
 │  ├─ P2_W0_验收包.md
 │  ├─ P2_W1_验收包.md
 │  ├─ P2_W2_验收包.md
 │  ├─ P2_W3_验收包.md
 │  └─ P2_W4_验收包.md
 │
 ├─ waves
 │  ├─ P2_W0.wave_gate.md
 │  ├─ P2_W1.wave_gate.md
 │  ├─ P2_W2.wave_gate.md
 │  ├─ P2_W3.wave_gate.md
 │  └─ P2_W4.wave_gate.md
 │
 └─ threads
    ├─ phase2_wave0
    ├─ phase2_wave1
    ├─ phase2_wave2
    ├─ phase2_wave3
    └─ phase2_wave4
```

每个 thread 至少要有：

```text
<thread>.delivery_note.md
<thread>.test_evidence.md
<thread>.thread_acceptance.md
```

---

## 6. Phase2 Wave 和 Thread 映射

Phase2 采用 Wave-based 并行开发，但文档仍然沿用 Phase1 的 thread / wave 验收模型。

### Wave 0：Interface Freeze

目标：冻结跨模块契约，使后续并行开发不互相打架。

Threads：

```text
P2_W0_core_schemas
P2_W0_solidity_interfaces
P2_W0_fixtures
P2_W0_feature_flags
P2_W0_wave_smoke_commands
```

退出条件：

```text
Pydantic schema fixture 可解析
Solidity interface 可编译
Feature flags 默认禁用 Phase3 / Phase4 功能
Happy path fixtures 存在
Wave1 agent 可基于这些契约开工
```

---

### Wave 1：Offline Core

目标：不接链、不接 Reactive，先跑通离线链路。

链路：

```text
fixture TradeIntent
 -> Validation
 -> PreRegistrationCheck mock
 -> ExecutionCompiler
 -> ExecutionPlan
 -> Audit JSON / Markdown fixture export
```

Threads：

```text
P2_W1_validation_engine
P2_W1_execution_compiler
P2_W1_audit_export_fixture
P2_W1_cli_dry_run
```

退出条件：

```text
agent-cli decision dry-run --fixture 可跑通
ValidationResult = PASSED
ExecutionPlan 可生成
Audit Markdown 可从 fixture 摘抄
不发送任何链上交易
```

---

### Wave 2：Local Chain Core

目标：本地链 + Mock DEX 跑通状态机。

链路：

```text
registerInvestmentIntent
 -> custody tokenIn
 -> LocalExecutor entry
 -> ActivePosition
 -> LocalExecutor exit
 -> Closed
 -> EventSyncer 更新 ExecutionRecord
```

Threads：

```text
P2_W2_contract_register_custody
P2_W2_contract_entry_swap
P2_W2_contract_exit_swap
P2_W2_local_executor
P2_W2_event_syncer_local
```

退出条件：

```text
Foundry 状态机测试通过
本地 register / entry / exit / closed 闭环通过
ExecutionRecord 从事件同步更新
Closed 状态重复触发失败
```

---

### Wave 3：Fork / Testnet E2E

目标：将 mock 替换为真实 fork / testnet 组件，但仍优先使用 LocalExecutor。

Threads：

```text
P2_W3_uniswap_v2_adapter
P2_W3_price_oracle_adapter
P2_W3_rpc_pre_registration_check
P2_W3_register_tx_sender
P2_W3_fork_integration_test
```

退出条件：

```text
RPC PreRegistrationCheck 通过
register tx 可发送并解析 receipt
Uniswap V2-compatible swap 可在 fork/testnet 跑通
EntryExecuted / ExitExecuted 可同步
ExecutionRecord = Closed
```

---

### Wave 4：Reactive + Hardening

目标：接入 Reactive adapter，完成幂等、禁用功能保护与导出收口。

Threads：

```text
P2_W4_reactive_adapter
P2_W4_idempotency_hardening
P2_W4_final_export
P2_W4_disabled_feature_tests
P2_W4_phase2_go_no_go
```

退出条件：

```text
LocalExecutor happy path 仍然通过
ReactiveAdapter happy path 通过
重复 callback 不会重复执行
disabled features 不可误触发
export json / markdown / memo 可从同一 ExecutionRecord 生成
Phase2 Go / No-Go 通过
```

---

## 7. Phase2 Materials Audit 模板

文件位置：

```text
docs/knowledge/00_meta/04_phase2_materials_audit.md
```

模板：

```markdown
# Phase2 Materials Audit

## 1. 目的

检查现有 Phase2 文档是否足够支持 code agent 开工。

## 2. 判断标准

每个模块必须回答：

1. 做什么？
2. 不做什么？
3. 改哪里？
4. 怎么验证？
5. 怎么判定完成？
6. 交付证据写到哪里？

## 3. 审计表

| 文件 | 是否存在 | 覆盖范围 | Agent-ready | 缺口 | 动作 |
|---|---:|---|---:|---|---|
| docs/contracts/phase2_execution_bundle.contract.md | TBD | Phase2 bundle | TBD | 是否含 allowed paths / test command | update / split |
| docs/prompts/phase2_bundle.prompt.md | TBD | Phase2 bundle prompt | TBD | 是否可拆 wave/thread | update / split |
| docs/guides/06_phase2_delivery_playbook.md | TBD | delivery guide | TBD | 是否含 wave gate | update |
| docs/knowledge/08_delivery/04_phase2_prd_alignment.md | TBD | PRD alignment | TBD | 是否反映最新 Phase2 scope | update |
| docs/acceptance/00_overview/08_phase2_go_no_go.md | TBD | Phase2 go/no-go | TBD | 是否含 Core Execution Loop gate | update |
```

---

## 8. Phase2 Doc Delta Plan 模板

文件位置：

```text
docs/knowledge/00_meta/05_phase2_doc_delta_plan.md
```

模板：

```markdown
# Phase2 Documentation Delta Plan

## 1. 动作枚举

- reuse：复用现有文件，不修改
- update：更新现有文件，加入 Phase2 delta
- split：现有文件太大，拆成模块级文件
- create：新增 Phase2 专用文件
- deprecate：标记旧文件不再作为 Phase2 输入

## 2. 模块计划

| 模块 | 当前文件 | 动作 | 新增/更新文件 | 原因 |
|---|---|---:|---|---|
| core invariants | docs/knowledge/01_core/01_system_invariants.md | reuse | - | 全阶段通用 |
| domain models | docs/knowledge/01_core/02_domain_models.md | update | 增加 Phase2 InvestmentIntentPayload | Phase2 有新字段 |
| execution compiler | docs/contracts/execution_compiler.contract.md | update | 增加 Phase2 Contract | 注册时编译语义增强 |
| investment state machine | docs/contracts/investment_state_machine_contract.contract.md | update/create | TBD | Phase2 核心合约 |
| local executor | - | create | docs/contracts/phase2_local_executor.contract.md | Phase2 新增 |
| event syncer | - | create | docs/contracts/phase2_event_syncer.contract.md | Phase2 新增 |
| disabled features | - | create | docs/contracts/phase2_disabled_features.contract.md | 防止 Phase3/4 泄漏 |
```

---

## 9. Agent-ready Prompt 标准

每个 `docs/prompts/*.prompt.md` 必须包含以下字段。

```markdown
# <module>.prompt.md

## Read First

- scaffold/backend/<module>/AGENTS.md
- docs/knowledge/01_core/01_system_invariants.md
- docs/knowledge/01_core/02_domain_models.md
- docs/knowledge/<module>/<module>.md
- docs/contracts/<module>.contract.md

## Task

明确说明本次任务。

## Allowed Paths

- backend/<module>/**
- tests/<module>/**
- fixtures/phase2/<module>/**

## Forbidden Paths

- contracts/**          # unless this is a contract task
- backend/reactive/**   # unless this is a reactive task
- backend/cli/**        # unless this is a CLI task
- backend/export/**     # unless this is an export task

## Must Not Implement

- Uniswap V3
- Cross-chain
- Hyperlane
- Aave Protection
- Full Approval Flow
- Shadow Monitor daemon
- Web UI
- PostgreSQL / Redis
- Telegram / Discord / webhook alerts

## Inputs

- 输入模型或文件

## Outputs

- 输出模型或文件

## Acceptance Criteria

- [ ] ...
- [ ] ...
- [ ] ...

## Test Command

```bash
pytest ...
```

## Delivery Evidence

Update:

- docs/acceptance/threads/phase2_waveX/<module>.delivery_note.md
- docs/acceptance/threads/phase2_waveX/<module>.test_evidence.md
- docs/acceptance/threads/phase2_waveX/<module>.thread_acceptance.md
```

没有 `Allowed Paths / Forbidden Paths / Test Command / Delivery Evidence` 的 prompt，不算 agent-ready。

---

## 10. Implementation Contract 标准

每个 `docs/contracts/*.contract.md` 必须包含：

```markdown
# <module>.contract.md

## Module Purpose

该模块负责什么。

## Phase2 Scope

Phase2 中该模块必须交付什么。

## Out of Scope

明确不做什么。

## Inputs

输入对象、文件或依赖。

## Outputs

输出对象、文件或副作用。

## Public Interfaces

需要保持稳定的函数、模型、CLI 命令、事件、ABI。

## Required Behavior

必须实现的行为。

## Failure Modes

失败时应该抛出的异常、返回的状态或链上 revert。

## Forbidden Behavior

禁止事项。

## Tests

必须覆盖的测试。

## Acceptance Criteria

完成标准。

## Handoff Notes

交给下游模块需要说明什么。
```

---

## 11. Wave Gate 标准

每个 `docs/acceptance/waves/P2_W*.wave_gate.md` 必须包含：

```markdown
# P2_WX Wave Gate

## Wave Goal

本 Wave 的唯一目标。

## Included Threads

- thread A
- thread B
- thread C

## Required Contracts

- docs/contracts/...
- docs/contracts/...

## Frozen Interfaces

本 Wave 结束后冻结的接口。

## Smoke Test

```bash
make smoke-p2-wx
```

## Exit Criteria

- [ ] ...
- [ ] ...

## Merge Policy

- 所有 thread 测试通过
- 所有 delivery note 已填写
- 所有 test evidence 已填写
- 没有未批准的 interface change
- 没有 disabled feature 泄漏

## Risks

| Risk | Impact | Mitigation |
|---|---|---|

## Handoff to Next Wave

说明下一个 Wave 可以依赖什么。
```

Wave Gate 是并行开发能否收口的关键。

---

## 12. Thread Acceptance 标准

每个 thread 的验收文件建议包括三份。

### 12.1 delivery note

```markdown
# <thread>.delivery_note.md

## Summary

实现了什么。

## Files Changed

- ...

## Behavior Added

- ...

## Behavior Explicitly Not Added

- ...

## Interfaces Changed

- None / list

## Downstream Notes

给下游模块的说明。
```

### 12.2 test evidence

```markdown
# <thread>.test_evidence.md

## Test Command

```bash
...
```

## Result

PASS / FAIL

## Output Summary

粘贴关键输出。

## Skipped Checks

如果有跳过，说明原因。
```

### 12.3 thread acceptance

```markdown
# <thread>.thread_acceptance.md

## Acceptance Checklist

- [ ] Contract requirements satisfied
- [ ] Prompt requirements satisfied
- [ ] Tests passed
- [ ] No forbidden paths modified
- [ ] No Phase3 / Phase4 features implemented
- [ ] Delivery note completed
- [ ] Test evidence completed

## Reviewer Notes

...
```

---

## 13. Phase2 Disabled Feature 规则

Phase2 明确不实现：

```text
Uniswap V3
Cross-chain
Hyperlane
Aave Protection
Full Approval Flow
Shadow Monitor daemon
Webhook alerts
PostgreSQL / Redis
Web UI
```

这些功能必须：

```text
默认 feature flag disabled
可以保留接口或 stub
不能进入主链路
不能被 happy path 调用
必须有 disabled-feature 测试
```

推荐 feature flags：

```yaml
features:
  approval_flow: false
  shadow_monitor: false
  aave_protection: false
  uniswap_v3: false
  crosschain: false
  webhook_alerts: false
```

推荐测试：

```text
test_manual_approval_required_aborts_in_phase2
test_crosschain_intent_rejected_in_phase2
test_uniswap_v3_rejected_in_phase2
test_aave_protection_not_called_in_phase2
test_webhook_alert_sink_not_required_in_phase2
```

---

## 14. Phase2 Code Agent 投喂顺序

每次给 code agent 的上下文应该遵循这个顺序：

```text
1. scaffold/backend/<module>/AGENTS.md
2. docs/knowledge/01_core/01_system_invariants.md
3. docs/knowledge/01_core/02_domain_models.md
4. docs/knowledge/<module>/<module>.md
5. docs/contracts/<module>.contract.md
6. docs/prompts/<module>.prompt.md
7. 当前 Wave Gate
```

不要默认投喂完整 PRD。  
只有当 knowledge / contract 没有定义时，才回看 PRD。

---

## 15. Phase2 开发节奏

### 15.1 推荐顺序

```text
Step 1：Phase2 Materials Audit
Step 2：Phase2 Doc Delta Plan
Step 3：补 Wave 0 文件
Step 4：跑 Wave 0 Interface Freeze
Step 5：并行 Wave 1
Step 6：Wave 1 Gate
Step 7：并行 Wave 2
Step 8：Wave 2 Gate
Step 9：并行 Wave 3
Step 10：Wave 3 Gate
Step 11：并行 Wave 4
Step 12：Phase2 Go / No-Go
```

### 15.2 Wave 0 没完成前，不并行

Wave 0 冻结：

```text
Pydantic schema
Solidity ABI
Event schema
DB schema
Feature flags
Fixtures
Smoke commands
```

没有 Wave 0，后续 agent 会各自定义 schema 和 ABI，集成会失败。

---

## 16. Phase2 Go / No-Go

文件位置：

```text
docs/acceptance/00_overview/08_phase2_go_no_go.md
```

Go 条件：

```text
Core Execution Loop 在 fork/testnet 跑通
LocalExecutor happy path 通过
ReactiveAdapter happy path 通过或明确标记为 testnet limitation
ExecutionRecord 能从事件同步更新
JSON / Audit Markdown / Investment Memo 可导出
disabled features 不可误触发
所有 Wave Gate 通过
所有 critical tests 通过
```

No-Go 条件：

```text
状态机无法从 PendingEntry -> ActivePosition -> Closed
register tx 与 event sync 无法对齐
重复 callback 可重复执行
disabled features 可进入主链路
ExecutionRecord 与链上事件不一致
Core schema / ABI 未冻结
```

---

## 17. 推荐最小落地文件清单

第一批先生成这些，不要一次性铺满所有文件：

```text
docs/knowledge/00_meta/04_phase2_materials_audit.md
docs/knowledge/00_meta/05_phase2_doc_delta_plan.md
docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md
docs/knowledge/08_delivery/05_phase2_wave_plan.md
docs/knowledge/08_delivery/06_phase2_disabled_features.md

docs/contracts/phase2_interface_freeze.contract.md
docs/contracts/phase2_core_execution_loop.contract.md
docs/contracts/phase2_disabled_features.contract.md

docs/prompts/00_generic.prompt.md
docs/prompts/phase2_wave0_interface_freeze.prompt.md

docs/acceptance/waves/P2_W0.wave_gate.md
docs/acceptance/waves/P2_W1.wave_gate.md
docs/acceptance/waves/P2_W2.wave_gate.md
docs/acceptance/waves/P2_W3.wave_gate.md
docs/acceptance/waves/P2_W4.wave_gate.md
docs/acceptance/00_overview/08_phase2_go_no_go.md
```

第二批再补模块级：

```text
validation_engine
pre_registration_check
execution_compiler
investment_state_machine
price_oracle_adapter
local_executor
event_syncer
cli_execution
export_outputs
disabled_feature_tests
```

---

## 18. 外部参考

这些外部实践支持本范式：

- OpenAI Codex 的 `AGENTS.md` 指南说明，可以用仓库级和目录级 instruction 文件指导 code agent，并可按目录覆盖规则。
- GitHub Copilot repository custom instructions 支持给仓库提供项目级指导和偏好。
- Claude Code 使用 `CLAUDE.md` / memory 作为项目上下文和长期指令载体。
- Scrum Guide 将 Sprint Backlog 定义为 Sprint Goal、选入工作项以及交付 Increment 的可执行计划。Phase2 的 Wave Gate 可类比为每个 Wave 的目标、工作项和可交付增量。

---

## 19. 最终原则

Phase2 的文档组织规则：

```text
不要换范式
不要直接喂 PRD
不要复制一整套 phase2_* 平行目录
不要让 agent 自己猜范围
```

应该：

```text
沿用 Phase1 的 knowledge -> contracts -> prompts -> acceptance
在原模块上补 Phase2 delta
新增 Wave Gate 管理并行收口
所有 prompt 必须 agent-ready
所有 thread 必须留下验收证据
所有 disabled feature 必须默认关闭且有测试
```

一句话：

> Phase2 不是重建文档体系，而是在 Phase1 骨架上叠加 Core Execution Loop 的增量合同、并行 Wave 门禁和 agent-ready prompt。
