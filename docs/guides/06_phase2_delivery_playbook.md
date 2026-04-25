# Phase2 Delivery Playbook

## 目标

按 PRD v11 的 Core Execution Loop 推进 Phase2：单链、long-only、Uniswap V2-compatible、注册时资金托管、LocalExecutor first、ReactiveExecutorAdapter v1 later。

Phase2 不以“模块是否写完”为完成标准，而以 W0-W4 Wave Gate 是否通过和闭环是否可复现为完成标准。

## 开发顺序

```text
W0: Contract Freeze
W1: Offline Core Loop
W2: Local Chain Mock Loop
W3: Fork/Testnet E2E Loop
W4: Reactive + Hardening + Export Closure
```

## W0 之前禁止并行发明接口

W0 必须先冻结：

- Pydantic schema
- Solidity ABI
- contract events
- `ExecutionRecord` persistence shape
- CLI command skeleton
- fixtures
- error taxonomy
- feature flags

W0 未过 gate 前，不应启动 W1-W4 多 agent 并行开发。

## 每个 Agent 的读取顺序

1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. `docs/knowledge/00_meta/03_phase2_wave_parallelization_map.md`
4. `docs/knowledge/08_delivery/05_phase2_wave_plan.md`
5. 相关 module knowledge
6. 相关 `docs/contracts/*.contract.md`
7. 相关 `docs/prompts/*.prompt.md`
8. 当前 `docs/acceptance/waves/P2_W*.wave_gate.md`
9. 对应 `scaffold/backend/*/AGENTS.md`

只有当 knowledge / contract 没有定义时，才回看 PRD。

## Wave Gate 验收口径

### W0: Contract Freeze

目标：冻结接口，禁止并行发明 schema、ABI、event、error。

Smoke:

```powershell
python scripts/workflow.py audit-manifest --strict
```

### W1: Offline Core Loop

目标：fixture-only dry-run。

路径：

```text
TradeIntent fixture -> Validation -> PreRegistrationCheck fixture result -> ExecutionPlan -> Export
```

### W2: Local Chain Mock Loop

目标：local chain/mock DEX 状态机闭环。

路径：

```text
register -> PendingEntry -> entry -> ActivePosition -> exit -> Closed
```

### W3: Fork/Testnet E2E Loop

目标：真实 RPC / fork RPC + Uniswap V2-compatible 链路。

要求：执行真相来自 RPC 和链上事件，indexer 不能替代执行真相。

### W4: Reactive + Hardening + Export Closure

目标：ReactiveExecutorAdapter v1、幂等、异常、disabled feature 快速失败、最终导出闭环。

## Module Work Rule

模块仍按 contract/prompt 执行，但合并必须服务当前 Wave 的 vertical smoke。孤立模块完成不等于 Wave 完成。

## Disabled Feature Rule

Phase2 禁止接入主链路：

- complete Approval Flow queue
- Shadow Monitor daemon
- Aave Protection
- Uniswap V3
- cross-chain / Hyperlane
- webhook alerts
- Postgres / Redis

被调用时必须快速失败或明确保持 disabled，不允许静默 fallback。

## 证据位置

```text
docs/acceptance/threads/phase2_wave0/
docs/acceptance/threads/phase2_wave1/
docs/acceptance/threads/phase2_wave2/
docs/acceptance/threads/phase2_wave3/
docs/acceptance/threads/phase2_wave4/
```

每个 thread 至少包含：

- `<thread>.delivery_note.md`
- `<thread>.test_evidence.md`
- `<thread>.thread_acceptance.md`

## 何时判定 HOLD

- 当前 Wave smoke test 失败。
- W0 冻结接口被绕开。
- 触发时重新编译 ExecutionPlan。
- disabled feature 进入主链路。
- JSON / Audit Markdown / Memo 字段不一致。
- EventSyncer 无法从链上事件恢复 ExecutionRecord。
- fork/testnet 证据缺失但声称 E2E 完成。
