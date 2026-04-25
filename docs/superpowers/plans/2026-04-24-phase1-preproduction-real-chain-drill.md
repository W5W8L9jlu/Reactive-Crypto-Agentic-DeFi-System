# Phase1 Preproduction Real Chain Drill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 推进 Phase1 预生产上线，补齐真实链路演练证据并收口预生产清单。

**Architecture:** 复用现有 `scripts/run_sepolia_smoke.py` 和预生产验收文档，不新增业务路径。把工作拆成四段：运行前置核验、真实链路演练、证据固化、清单收口。所有结论都以真实链上回执、monitor 结果和文档签收为准，不靠推断补齐。

**Tech Stack:** Python 3.14, Foundry, web3.py, existing smoke scripts, docs/acceptance markdown.

---

## Scope Check

本次只推进一个子项目：**Phase1 预生产真实链路演练**。

允许涉及的文件主要是：
- `scripts/check_sepolia_smoke_env.py`
- `scripts/run_sepolia_smoke.py`
- `docs/acceptance/threads/wave5/sepolia_smoke.test_evidence.md`
- `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`
- `docs/acceptance/00_overview/07_phase1_preproduction_go_no_go.md`

不新增新业务模块，不改合约，不改 CLI 路由逻辑。

---

## File Structure

### 目标文件职责
- `scripts/check_sepolia_smoke_env.py`
  - 只负责检查预生产 smoke 所需环境变量是否齐全。
- `scripts/run_sepolia_smoke.py`
  - 只负责执行真实链路 smoke，并输出可留档结果。
- `docs/acceptance/threads/wave5/sepolia_smoke.test_evidence.md`
  - 只记录本次真实 smoke 的命令、tx、回执、最终状态。
- `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`
  - 只记录运维就绪度、监控/告警、恢复与执行联动的补证。
- `docs/acceptance/00_overview/07_phase1_preproduction_go_no_go.md`
  - 只汇总预生产门禁状态，不引入新的口径。

---

### Task 1: 运行前置核验

**Files:**
- Test: `scripts/check_sepolia_smoke_env.py`
- Test: `backend/cli/wiring.py`（只读核对，不改实现）
- Modify: `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`（如需追加本次核验结果）

- [x] **Step 1: 确认预生产环境变量可用**

Run:
```bash
python scripts/check_sepolia_smoke_env.py
```

Expected:
- 退出码 `0`
- 输出 `Sepolia smoke env check: OK`

- [x] **Step 2: 确认控制地址与 artifact 仍然可解析**

Run:
```bash
python -c "import os; from pathlib import Path; from web3 import Web3; print('rpc=', bool(os.environ.get('SEPOLIA_RPC_URL') or os.environ.get('BASE_SEPOLIA_RPC_URL'))); print('pk=', bool(os.environ.get('SEPOLIA_PRIVATE_KEY'))); print('addr=', bool(os.environ.get('REACTIVE_INVESTMENT_COMPILER_ADDRESS'))); print('artifact=', Path('backend/contracts/out/ReactiveInvestmentCompiler.sol/ReactiveInvestmentCompiler.json').exists())"
```

Expected:
- `rpc=True`
- `pk=True`
- `addr=True`
- `artifact=True`

- [x] **Step 3: 记录阻塞条件**

If `SEPOLIA_PRIVATE_KEY` is missing, stop and record the blocker in `ops_readiness.test_evidence.md` instead of guessing.

---

### Task 2: 真实链路演练

**Files:**
- Test: `scripts/run_sepolia_smoke.py`
- Modify: `docs/acceptance/threads/wave5/sepolia_smoke.test_evidence.md`

- [x] **Step 1: 运行完整 smoke**

Run:
```bash
python scripts/run_sepolia_smoke.py
```

Expected:
- `dry-run boundary: manual_approval`
- `approval action: approved`
- `register tx` 有值
- `execute entry tx` 有值
- `monitor alert count: 1`
- `force-close tx` 有值
- `final state: Closed`

- [x] **Step 2: 验证 smoke artifact**

Confirm the generated artifact JSON exists under:
```text
docs/acceptance/threads/wave5/artifacts/
```

Expected:
- 新 artifact 文件存在
- 其中包含本次链路的 tx、状态和 monitor 结果

- [x] **Step 3: 如完整 smoke 失败，退回到最小可复现链路**

If `run_sepolia_smoke.py` fails at the final force-close stage:
```bash
python scripts/run_sepolia_smoke.py --skip-force-close
python -m backend.cli.entrypoint execution force-close <intent_id>
```

Expected:
- 先拿到 `ActivePosition`
- 再由 CLI 完成真实 force-close

---

### Task 3: 证据固化

**Files:**
- Modify: `docs/acceptance/threads/wave5/sepolia_smoke.test_evidence.md`
- Modify: `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`

- [x] **Step 1: 追加本次运行结果**

Write only facts:
- 命令
- deployer / contract / tx
- register / execute / force-close 结果
- monitor alert count
- 最终状态

- [x] **Step 2: 追加运维就绪补证**

Write only facts:
- environment check 结果
- runtime dependency 结果
- monitor / emergency linkage 结果

- [x] **Step 3: 保持 Markdown 摘抄，不做总结改写**

Only append evidence and concise notes. Do not turn evidence files into long narrative summaries.

---

### Task 4: 预生产清单收口

**Files:**
- Modify: `docs/acceptance/00_overview/07_phase1_preproduction_go_no_go.md`

- [x] **Step 1: 更新已完成项**

If the run succeeds, mark as complete:
- 目标预生产环境可重复完成 `PendingEntry -> ActivePosition -> Closed`
- 目标预生产环境 Shadow Monitor 对账通过
- 目标预生产环境关键告警触发通过
- 目标预生产环境 force-close 预案签收
- 在目标预生产环境完成一次完整用户路径演练

- [x] **Step 2: 更新“还差什么”**

Remove resolved blockers only. Keep any unresolved blocker explicit.

- [x] **Step 3: 保持当前签收事实**

Do not rewrite the already signed items unless the runtime facts changed.

---

## Verification

Run these checks in order:
```bash
python scripts/check_sepolia_smoke_env.py
python scripts/run_sepolia_smoke.py
python -m pytest backend/validation/test_pre_registration_check.py backend/monitor/test_shadow_monitor.py backend/contracts/core/test_investment_state_machine_contract_emergency_force_close.py backend/cli/test_phase1_end_to_end.py backend/cli/test_phase1_gate.py backend/cli/test_force_close_integration.py -q
```

Expected:
- 前置环境检查通过
- smoke 真实链路通过
- 预生产清单只剩真实未完成项

---

## Done Criteria

- 真实链路 smoke 留档
- 监控与对账证据留档
- 预生产清单状态与真实结果一致
- 不再保留已完成项的占位状态
