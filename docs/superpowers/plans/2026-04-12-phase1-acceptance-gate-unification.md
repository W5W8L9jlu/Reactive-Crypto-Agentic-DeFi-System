# Phase1 Acceptance Gate Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一 Phase 1 验收口径，消除“回归通过但 doctor 显示 blocked”造成的误判与沟通歧义。

**Architecture:** 将验收拆成 3 个显式 gate：`llm`、`chain`、`full`。`doctor` 按 gate 只返回该 gate 的必需状态；`run_phase1_regression` 按用户选择执行对应 gate，不再混用语义。通过条件始终由同一判定函数输出，避免脚本间语义漂移。

**Tech Stack:** Python 3.14, unittest/pytest, existing CLI wiring (`backend/cli/wiring.py`), regression scripts (`scripts/*.py`).

---

## Scope Check

本问题涉及独立子系统：
1. 验收脚本层（`scripts/`）
2. CLI doctor 状态层（`backend/cli/wiring.py`）

两者可在同一计划内落地，因为目标是“验收口径一致性”且改动面紧耦合、可联合测试。

## File Structure

### 目标文件职责
- `scripts/check_llm_channel_smoke.py`
  - 只负责 gate-aware 诊断执行与退出码输出。
- `scripts/run_phase1_regression.py`
  - 只负责编排测试命令与 gate 调用，不直接定义业务诊断语义。
- `backend/cli/wiring.py`
  - 提供 gate-aware doctor payload（当前 payload 中 `status` 是 full 语义，需要拆分）。
- `backend/cli/test_wiring.py`（如已存在则扩展）
  - 校验 doctor payload 在不同 gate 的字段与状态。
- `scripts/tests/test_check_llm_channel_smoke.py`（新建）
  - 校验命令行参数与退出码行为。
- `scripts/tests/test_run_phase1_regression.py`（新建）
  - 校验编排逻辑不会出现“打印 blocked 但进程成功”的冲突输出。

---

### Task 1: 固化问题与验收基线（Root Cause Snapshot）

**Files:**
- Modify: `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`（追加一段“语义冲突复现”）
- Test: `scripts/run_phase1_regression.py`, `scripts/check_llm_channel_smoke.py`

- [ ] **Step 1: 复现冲突输出并保存证据**

Run:
```bash
python scripts/run_phase1_regression.py --with-chain --with-llm
```
Expected:
- 进程退出码 `0`
- 输出中出现 `llm_smoke: OK`
- 同时 payload 里可见 `status: "blocked"`（旧行为）

- [ ] **Step 2: 在验收证据文档追加“旧行为说明”**

追加示例文本：
```md
## 口径冲突复现（待修复）
- 命令：`python scripts/run_phase1_regression.py --with-chain --with-llm`
- 现象：`llm_smoke: OK` 与 payload 的 `status: blocked` 同时出现
- 判定：脚本通过条件与展示字段口径不一致
```

- [ ] **Step 3: Commit**

```bash
git add docs/acceptance/threads/wave5/ops_readiness.test_evidence.md
git commit -m "docs: 记录Phase1验收口径冲突复现证据"
```

---

### Task 2: 设计并实现 Gate-aware Doctor 语义

**Files:**
- Modify: `backend/cli/wiring.py`
- Test: `backend/cli/test_wiring.py`

- [ ] **Step 1: 写失败测试（先红）**

在 `backend/cli/test_wiring.py` 新增测试样例：
```python
def test_doctor_llm_gate_does_not_require_contract_gateway():
    services = build_production_services(contract_gateway=None, runtime_store=_tmp_store())
    payload = json.loads(services.doctor_check(gate="llm"))
    assert payload["gate"] == "llm"
    assert payload["gate_status"] in {"ok", "blocked"}
    assert "runtime ContractGateway not wired" not in payload["blocked_reasons"]
```

- [ ] **Step 2: 运行失败测试**

Run:
```bash
PYTHONPATH=. python -m pytest backend/cli/test_wiring.py -q
```
Expected: 新增测试失败（`doctor_check` 目前无 `gate` 参数或仍返回 full 语义）。

- [ ] **Step 3: 最小实现**

在 `backend/cli/wiring.py` 实施：
```python
def doctor_check(gate: str = "full") -> str:
    # gate in {"llm", "chain", "full"}
    # gate_status 按 gate 所需字段判定
    # legacy status 保留但标注 full_status，避免调用方误读
```

并返回结构：
```json
{
  "gate": "llm|chain|full",
  "gate_status": "ok|blocked",
  "full_status": "ok|blocked",
  "blocked_reasons": [...]
}
```

- [ ] **Step 4: 运行测试转绿**

Run:
```bash
PYTHONPATH=. python -m pytest backend/cli/test_wiring.py -q
```
Expected: 通过。

- [ ] **Step 5: Commit**

```bash
git add backend/cli/wiring.py backend/cli/test_wiring.py
git commit -m "fix: 统一doctor为gate-aware状态语义"
```

---

### Task 3: 统一 check_llm_channel_smoke 的判定与输出

**Files:**
- Modify: `scripts/check_llm_channel_smoke.py`
- Test: `scripts/tests/test_check_llm_channel_smoke.py`

- [ ] **Step 1: 写失败测试**

```python
def test_llm_only_reports_gate_status_only(monkeypatch):
    code, out = run_cli("--llm-only")
    assert code == 0
    assert "llm_smoke: OK" in out
    assert '"gate": "llm"' in out
```

- [ ] **Step 2: 运行失败测试**

Run:
```bash
PYTHONPATH=. python -m pytest scripts/tests/test_check_llm_channel_smoke.py -q
```
Expected: 失败（旧输出无 gate 字段或存在冲突状态）。

- [ ] **Step 3: 最小实现**

核心改动：
```python
# old: services.doctor_check()
payload = json.loads(services.doctor_check(gate="llm" if args.llm_only else "full"))
passed = payload.get("gate_status") == "ok"
```

- [ ] **Step 4: 运行测试转绿**

Run:
```bash
PYTHONPATH=. python -m pytest scripts/tests/test_check_llm_channel_smoke.py -q
```
Expected: 通过。

- [ ] **Step 5: Commit**

```bash
git add scripts/check_llm_channel_smoke.py scripts/tests/test_check_llm_channel_smoke.py
git commit -m "fix: 对齐llm-smoke与doctor gate状态判定"
```

---

### Task 4: 统一回归编排入口与最终验收门禁

**Files:**
- Modify: `scripts/run_phase1_regression.py`
- Test: `scripts/tests/test_run_phase1_regression.py`

- [ ] **Step 1: 写失败测试**

```python
def test_with_chain_and_llm_invokes_full_gate():
    calls = capture_subprocess_calls(["--with-chain", "--with-llm"])
    assert ["python", "scripts/check_llm_channel_smoke.py", "--full"] in calls
```

- [ ] **Step 2: 运行失败测试**

Run:
```bash
PYTHONPATH=. python -m pytest scripts/tests/test_run_phase1_regression.py -q
```
Expected: 失败（旧逻辑用 `--llm-only`）。

- [ ] **Step 3: 最小实现**

建议参数策略：
```python
if args.with_llm and args.with_chain:
    _run([python, "scripts/check_llm_channel_smoke.py", "--full"], cwd=repo_root)
elif args.with_llm:
    _run([python, "scripts/check_llm_channel_smoke.py", "--llm-only"], cwd=repo_root)
```

- [ ] **Step 4: 运行测试转绿**

Run:
```bash
PYTHONPATH=. python -m pytest scripts/tests/test_run_phase1_regression.py -q
```
Expected: 通过。

- [ ] **Step 5: Commit**

```bash
git add scripts/run_phase1_regression.py scripts/tests/test_run_phase1_regression.py
git commit -m "fix: phase1回归脚本按场景选择正确gate"
```

---

### Task 5: 最终回归与交付口径冻结

**Files:**
- Modify: `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`
- Modify: `docs/acceptance/threads/wave5/00_generic.thread_acceptance.md`

- [ ] **Step 1: 运行完整验证**

Run:
```bash
PYTHONPATH=. python -m pytest backend/cli/test_wiring.py -q
PYTHONPATH=. python -m pytest scripts/tests/test_check_llm_channel_smoke.py scripts/tests/test_run_phase1_regression.py -q
python scripts/run_phase1_regression.py --with-chain --with-llm
```
Expected:
- 全部通过
- 输出不再出现“通过同时 blocked”的冲突口径

- [ ] **Step 2: 更新验收文档**

写入：
- gate 定义
- 执行命令
- 输出样例
- 通过标准

- [ ] **Step 3: Commit**

```bash
git add docs/acceptance/threads/wave5/ops_readiness.test_evidence.md docs/acceptance/threads/wave5/00_generic.thread_acceptance.md
git commit -m "docs: 冻结Phase1统一验收口径与证据"
```

---

## 风险与回滚

- 风险 1：老脚本调用方依赖 `status` 字段。
  - 处理：保留 `full_status` 与兼容字段一个发布周期，文档标注废弃时间。
- 风险 2：新增 gate 参数后调用入口不一致。
  - 处理：在脚本测试中固定参数矩阵（llm-only / chain-only / full）。
- 回滚策略：
  - 回滚 `scripts/*` 与 `backend/cli/wiring.py` 最近两次提交即可恢复旧行为。

## 完成定义（DoD）

- `--with-chain --with-llm` 的回归输出中，判定字段与展示字段语义一致。
- doctor 输出明确标识 `gate` 与 `gate_status`，不再混淆 full 状态。
- 新增测试覆盖并全部通过。
- 验收文档已更新，团队可按同一口径判定“Phase 1 可交付”。
