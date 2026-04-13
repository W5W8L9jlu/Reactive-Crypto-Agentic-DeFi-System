# Phase1 Runtime Reliability Repair Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Phase 1 的 CLI 用户路径只在“真实 CryptoAgents 投研成功 + 实际链上注册成功”时才报告成功，彻底移除 fallback 掩盖与环境漂移带来的验收假阳性。

**Architecture:** 修复分 5 个层次推进。先把 `decision` 路径改成 fail-closed 并显式暴露 `decision_source`，同时从用户路径移除 fallback；再把 `OPENAI_BASE_URL` 与自定义网关语义收敛成可诊断、可验收的环境合同；然后补上真实用户路径 smoke gates，覆盖 strict `decision dry-run` 与真实 `decision run`；接着只对安全的 RPC 读操作与 receipt 轮询做稳态化，避免重复广播；最后收敛 Python 版本与默认 timeout/retry，冻结 Phase 1 运行矩阵。所有修复都遵循 lean defensive coding：不允许用大量 `fallback` / broad `try/except` / 分支噪音去淹没核心业务逻辑。

**Tech Stack:** Python CLI (`Typer`, `Rich`), Pydantic v2 schemas, CryptoAgents adapter seam, `openai` + `langchain-openai`, `web3.py`, `unittest`/`pytest`, regression scripts in `scripts/`.

---

## Scope Check

本计划覆盖 4 个彼此相关但可顺序落地的子系统：

1. `backend/decision/` 的真实投研语义
2. `backend/cli/` 的路由/doctor/用户输出
3. `backend/execution/runtime/` 的链上注册稳态
4. `scripts/` 与运行时文档的验收门禁

它们共同服务一个目标：让“CLI 里得到投资建议并上链注册”成为可信的 Phase 1 验收口径，因此应放在同一计划中实施。

## File Structure

### 目标文件职责

- `backend/decision/schemas/cryptoagents_adapter.py`
  - `PortfolioManagerOutput` / `DecisionMeta` 的真相字段定义；新增 `decision_source` 的最佳落点。
- `backend/decision/adapters/cryptoagents_adapter.py`
  - 把 runner 输出映射成 `CryptoAgentsDecision`；不能吞掉来源信息。
- `backend/decision/adapters/cryptoagents_runner.py`
  - 真实 CryptoAgents graph 调用、LLM runtime retry、`OPENAI_BASE_URL`/timeout/retry 收敛点。
- `backend/cli/wiring.py`
  - decision route 行为、doctor payload、fallback 移除点、运行时环境显式错误。
- `backend/cli/app.py`
  - `decision run` / `decision dry-run` CLI 入口；必要时增加显式失败提示。
- `backend/execution/runtime/errors.py`
  - 执行层显式异常类型，区分“可重试读失败”与“广播状态不确定”。
- `backend/execution/runtime/contract_gateway.py`
  - 链上 register/trigger/receipt adapter；只对安全阶段做 retry，不掩盖广播歧义。
- `scripts/check_llm_channel_smoke.py`
  - 基于 CLI 合同做 LLM/doctor smoke gate；需要升级为“真实用户路径”门禁。
- `scripts/run_phase1_regression.py`
  - Phase 1 总回归编排器；需要串联 doctor + strict dry-run + real run。
- `scripts/test_phase1_regression.py`
  - 校验 smoke 编排参数矩阵与失败语义。
- `backend/decision/adapters/test_cryptoagents_runner.py`
  - runner 的 gateway/timeout/retry/base-url 行为测试。
- `backend/decision/schemas/test_cryptoagents_adapter.py`
  - schema/adapter 对 `decision_source` 的强类型约束测试。
- `backend/cli/test_wiring.py`
  - CLI 决策路由、doctor 输出、fallback 策略与错误语义测试。
- `backend/execution/runtime/test_contract_gateway.py`
  - 纯单元层验证 preflight retry、广播歧义错误与 receipt polling。
- `backend/execution/runtime/test_web3_contract_gateway_integration.py`
  - Web3 integration happy path；真实 receipt 仍可拿到。
- `.env.example`
  - 验收环境变量合同；需明确官方 OpenAI / 自定义网关 / timeout/retry / Python 版本说明。
- `pyproject.toml`
  - Python 运行版本边界。
- `README.md`
  - 项目根文档；新增 Phase 1 acceptance runtime profile。
- `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`
  - 记录 strict dry-run、real run、runtime matrix 的证据。
- `docs/acceptance/threads/wave5/00_generic.thread_acceptance.md`
  - 冻结新的 Phase 1 可交付门槛。

---

### Task 1: 移除用户路径中的 fallback，显式输出 `decision_source`

**Files:**
- Modify: `backend/decision/schemas/cryptoagents_adapter.py`
- Modify: `backend/decision/adapters/cryptoagents_adapter.py`
- Modify: `backend/cli/wiring.py`
- Modify: `backend/cli/app.py`
- Test: `backend/decision/schemas/test_cryptoagents_adapter.py`
- Test: `backend/cli/test_wiring.py`

- [ ] **Step 1: 先写失败测试，锁定“默认 fail-closed + 显式来源”语义**

在 `backend/decision/schemas/test_cryptoagents_adapter.py` 增加：

```python
def test_portfolio_manager_output_requires_decision_source():
    payload = {
        "pair": "ETH/USDC",
        "dex": "uniswap_v3",
        "position_usd": "1200",
        "max_slippage_bps": 20,
        "stop_loss_bps": 90,
        "take_profit_bps": 250,
        "entry_conditions": ["price_below:3000"],
        "ttl_seconds": 3600,
        "investment_thesis": "test",
        "confidence_score": "0.5",
        "agent_trace_steps": [
            {"agent": "portfolio_manager", "summary": "ok", "timestamp": "2026-04-12T00:00:00Z"}
        ],
    }
    with pytest.raises(ValidationError):
        PortfolioManagerOutput.model_validate(payload)
```

在 `backend/cli/test_wiring.py` 增加：

```python
def test_decision_dry_run_rejects_fallback_by_default(self) -> None:
    runner = FakeRunner(decision_source="fallback")
    services = build_production_services(
        runtime_store=self._new_store(),
        decision_adapter=build_cryptoagents_decision_adapter(runner=runner),
    )
    with self.assertRaises(CLISurfaceInputError):
        services.decision_dry_run("ctx-001")
```

- [ ] **Step 2: 运行局部测试，确认先红**

Run:
```bash
python -m pytest backend/decision/schemas/test_cryptoagents_adapter.py -q
python -m pytest backend/cli/test_wiring.py -k "fallback or decision_source" -q
```

Expected:
- 新增 case 失败
- 当前实现无法显式区分 `production` / `fallback`
- 当前实现仍允许 fallback 混入用户路径

- [ ] **Step 3: 最小实现**

实现要点：

```python
class PortfolioManagerOutput(BaseModel):
    decision_source: Literal["production", "fallback"]

class DecisionMeta(BaseModel):
    decision_source: Literal["production", "fallback"]
```

```python
decision_meta = DecisionMeta(
    investment_thesis=portfolio_output.investment_thesis,
    confidence_score=portfolio_output.confidence_score,
    decision_source=portfolio_output.decision_source,
)
```

```python
if decision.decision_meta.decision_source != "production":
    raise CLISurfaceInputError("decision route requires production decision; fallback is not allowed in user paths")
```

CLI 输出至少包含：

```json
{
  "decision_source": "production"
}
```

推荐策略：
- 默认 fail-closed
- `decision run` / `decision dry-run` 用户路径中直接移除 `_ResilientCryptoAgentsRunner`
- `_DeterministicFallbackRunner` 只能保留在测试替身或完全隔离的开发辅助工具里，不能接入生产 wiring
- 不再让 fallback 冒充验收成功

- [ ] **Step 4: 测试转绿**

Run:
```bash
python -m pytest backend/decision/schemas/test_cryptoagents_adapter.py -q
python -m pytest backend/cli/test_wiring.py -k "fallback or decision_source" -q
```

Expected:
- 全部通过
- `decision run` / `decision dry-run` 默认且唯一只接受 `production`

- [ ] **Step 5: Commit**

```bash
git add backend/decision/schemas/cryptoagents_adapter.py backend/decision/adapters/cryptoagents_adapter.py backend/cli/wiring.py backend/cli/app.py backend/decision/schemas/test_cryptoagents_adapter.py backend/cli/test_wiring.py
git commit -m "fix: make decision source explicit and fail closed by default"
```

---

### Task 2: 收敛 LLM 出口，明确官方 OpenAI 与自定义网关合同

**Files:**
- Modify: `backend/decision/adapters/cryptoagents_runner.py`
- Modify: `backend/cli/wiring.py`
- Modify: `scripts/check_llm_channel_smoke.py`
- Modify: `.env.example`
- Modify: `README.md`
- Test: `backend/decision/adapters/test_cryptoagents_runner.py`
- Test: `backend/cli/test_wiring.py`
- Test: `scripts/test_phase1_regression.py`

- [ ] **Step 1: 写失败测试，锁定 base-url 语义**

在 `backend/cli/test_wiring.py` 增加：

```python
def test_doctor_treats_missing_openai_base_url_as_official_default(self) -> None:
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
        payload = json.loads(build_production_services(runtime_store=self._new_store()).doctor_check("llm"))
    assert payload["openai_base_url_mode"] == "official_default"
```

在 `backend/decision/adapters/test_cryptoagents_runner.py` 增加：

```python
def test__classify_openai_base_url_labels_custom_gateway():
    with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://custom.gateway/v1"}, clear=False):
        assert _classify_openai_base_url() == "custom_gateway"
```

- [ ] **Step 2: 运行局部测试，确认先红**

Run:
```bash
python -m pytest backend/decision/adapters/test_cryptoagents_runner.py -q
python -m pytest backend/cli/test_wiring.py -k "openai_base_url" -q
```

Expected:
- 当前实现把缺失 `OPENAI_BASE_URL` 当成 not ready
- 无法显式区分官方默认与自定义网关

- [ ] **Step 3: 最小实现**

实现要点：

```python
def _classify_openai_base_url() -> str:
    raw = os.environ.get("OPENAI_BASE_URL", "").strip()
    if raw == "":
        return "official_default"
    if raw.rstrip("/") in {"https://api.openai.com", "https://api.openai.com/v1"}:
        return "official_explicit"
    return "custom_gateway"
```

`doctor` payload 增加：

```json
{
  "openai_base_url_mode": "official_default|official_explicit|custom_gateway",
  "llm_gateway_policy_ok": true
}
```

Phase 1 验收建议：
- `official_default` / `official_explicit` 直接允许
- `custom_gateway` 直接判定为 Phase 1 验收 blocked，直到仓库后续显式定义并文档化允许合同
- `check_llm_channel_smoke.py` 输出里打印上述模式，避免“看似连通、实际不受支持”

`.env.example` / `README.md` 明确：
- 官方 OpenAI 直连时 `OPENAI_BASE_URL` 可留空
- 自定义网关不是默认验收配置

- [ ] **Step 4: 测试转绿**

Run:
```bash
python -m pytest backend/decision/adapters/test_cryptoagents_runner.py -q
python -m pytest backend/cli/test_wiring.py -k "openai_base_url" -q
python -m unittest scripts.test_phase1_regression -v
```

Expected:
- `doctor` 与 smoke 能准确暴露 `openai_base_url_mode`
- 官方默认直连不会被误报 blocked
- 自定义 gateway 在 Phase 1 验收中必须显式失败，而不是走分支兜底

- [ ] **Step 5: Commit**

```bash
git add backend/decision/adapters/cryptoagents_runner.py backend/cli/wiring.py scripts/check_llm_channel_smoke.py .env.example README.md backend/decision/adapters/test_cryptoagents_runner.py backend/cli/test_wiring.py scripts/test_phase1_regression.py
git commit -m "fix: normalize openai endpoint policy for phase1 acceptance"
```

---

### Task 3: 新增真实用户路径 smoke gate，替代“只看 doctor”

**Files:**
- Create: `scripts/check_decision_runtime_smoke.py`
- Modify: `scripts/run_phase1_regression.py`
- Modify: `scripts/test_phase1_regression.py`
- Modify: `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`
- Modify: `docs/acceptance/threads/wave5/00_generic.thread_acceptance.md`

- [ ] **Step 1: 写失败测试，要求回归脚本串联 strict dry-run + real run**

在 `scripts/test_phase1_regression.py` 增加：

```python
def test_with_llm_calls_decision_runtime_smoke(self) -> None:
    commands = []
    with patch.object(sys, "argv", ["run_phase1_regression.py", "--with-llm"]):
        with patch.object(phase1_regression, "_run", side_effect=lambda command, cwd: commands.append(command)):
            phase1_regression.main()
    self.assertIn(
        [sys.executable, "scripts/check_decision_runtime_smoke.py", "--strict-dry-run"],
        commands,
    )
```

```python
def test_with_chain_and_llm_calls_real_run_smoke(self) -> None:
    commands = []
    with patch.object(sys, "argv", ["run_phase1_regression.py", "--with-llm", "--with-chain"]):
        with patch.object(phase1_regression, "_run", side_effect=lambda command, cwd: commands.append(command)):
            phase1_regression.main()
    self.assertIn(
        [sys.executable, "scripts/check_decision_runtime_smoke.py", "--decision-run"],
        commands,
    )
```

- [ ] **Step 2: 运行测试，确认先红**

Run:
```bash
python -m unittest scripts.test_phase1_regression -v
```

Expected:
- 当前编排器只会调用 `doctor` smoke，不会走真实 `decision` 用户路径

- [ ] **Step 3: 实现新的 smoke script**

`scripts/check_decision_runtime_smoke.py` 的 happy path：

1. 调 `python -m backend.cli.entrypoint strategy create`
2. 解析输出里的 `strategy_id`
3. `--strict-dry-run` 模式下：
   - 注入 `REACTIVE_DECISION_STRICT=true`
   - 调 `python -m backend.cli.entrypoint decision dry-run --strategy <id>`
   - 断言返回 JSON 中 `decision_source == "production"`
4. `--decision-run` 模式下：
   - 调 `python -m backend.cli.entrypoint decision run --strategy <id>`
   - 断言存在非空 `intent_id`
   - 断言存在非空 `register_tx_hash`
   - 用现有 `build_contract_gateway_from_runtime_env()` 或等价 runtime gateway 读取 `register_tx_hash` 对应 receipt
   - 断言 receipt 中 `tx_hash` 与 `register_tx_hash` 一致，且 `status == "success"`

关键输出：

```text
decision_runtime_smoke: OK
decision_source: production
register_tx_hash: 0x...
register_receipt_status: success
```

- [ ] **Step 4: 接入总回归**

在 `scripts/run_phase1_regression.py` 中改成：

```python
if args.with_llm:
    _run([python, "scripts/check_llm_channel_smoke.py", smoke_gate_flag], cwd=repo_root)
    _run([python, "scripts/check_decision_runtime_smoke.py", "--strict-dry-run"], cwd=repo_root)
if args.with_llm and args.with_chain:
    _run([python, "scripts/check_decision_runtime_smoke.py", "--decision-run"], cwd=repo_root)
```

- [ ] **Step 5: 测试转绿**

Run:
```bash
python -m unittest scripts.test_phase1_regression -v
```

Expected:
- 回归脚本现在必须覆盖真实 `decision` 路径
- LLM gate green 不再等价于产品链路 green
- real `decision run` smoke 不会因“只有 tx hash 没有成功 receipt”而误报通过

- [ ] **Step 6: 更新验收文档**

在 `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md` 与 `docs/acceptance/threads/wave5/00_generic.thread_acceptance.md` 追加：
- strict `decision dry-run` 命令
- real `decision run` 命令
- `decision_source=production` 与 `register_tx_hash` 的验收截图/日志要求

- [ ] **Step 7: Commit**

```bash
git add scripts/check_decision_runtime_smoke.py scripts/run_phase1_regression.py scripts/test_phase1_regression.py docs/acceptance/threads/wave5/ops_readiness.test_evidence.md docs/acceptance/threads/wave5/00_generic.thread_acceptance.md
git commit -m "test: gate phase1 acceptance on real decision runtime path"
```

---

### Task 4: 稳态化 RPC 注册链路，但禁止掩盖广播歧义

**Files:**
- Modify: `backend/execution/runtime/errors.py`
- Modify: `backend/execution/runtime/contract_gateway.py`
- Test: `backend/execution/runtime/test_contract_gateway.py`
- Test: `backend/execution/runtime/test_web3_contract_gateway_integration.py`

- [ ] **Step 1: 写失败测试，区分“可安全重试”与“广播状态不确定”**

在 `backend/execution/runtime/test_contract_gateway.py` 增加：

```python
def test_send_transaction_retries_read_only_preflight_errors():
    # get_transaction_count / get_block first fail, second succeed
```

```python
def test_send_transaction_raises_uncertain_broadcast_error_when_send_raw_transaction_disconnects():
    # send_raw_transaction raises ConnectionResetError after tx is signed
```

```python
def test_wait_for_receipt_retries_transient_connection_reset():
    # wait_for_transaction_receipt transient fail -> retry -> receipt
```

- [ ] **Step 2: 运行测试，确认先红**

Run:
```bash
python -m pytest backend/execution/runtime/test_contract_gateway.py -q
```

Expected:
- 当前实现不会区分 preflight/read/send/wait 阶段
- `ConnectionResetError` 直接向上冒泡

- [ ] **Step 3: 最小实现**

在 `backend/execution/runtime/errors.py` 增加：

```python
class ExecutionTransportRetryExhaustedError(ExecutionLayerDomainError): ...
class ContractBroadcastUncertainError(ExecutionLayerDomainError): ...
```

在 `contract_gateway.py` 中拆分 `_send_transaction()`：

```python
nonce = _read_with_retry(...)
latest_block = _read_with_retry(...)
signed = ...
tx_hash = _broadcast_or_raise_uncertain(...)
receipt = _wait_receipt_with_retry(tx_hash)
```

关键约束：
- 只 retry 读操作与 receipt polling
- 不在 `send_raw_transaction` 失败后自动重发同一笔交易
- 不写 broad `try/except Exception` 来吞掉广播根因；只允许极窄范围的异常归类并保留原始 cause
- 错误信息里必须带 `sender` / `nonce` / `intent_id`

- [ ] **Step 4: 测试转绿**

Run:
```bash
python -m pytest backend/execution/runtime/test_contract_gateway.py -q
python -m pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q
```

Expected:
- 单元测试通过
- 集成 happy path 不回归

- [ ] **Step 5: Commit**

```bash
git add backend/execution/runtime/errors.py backend/execution/runtime/contract_gateway.py backend/execution/runtime/test_contract_gateway.py backend/execution/runtime/test_web3_contract_gateway_integration.py
git commit -m "fix: harden rpc register path without masking ambiguous broadcast state"
```

---

### Task 5: 冻结 Phase 1 运行矩阵，收敛 Python 版本与 timeout/retry 默认值

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `backend/decision/adapters/cryptoagents_runner.py`
- Modify: `docs/acceptance/threads/wave5/ops_readiness.test_evidence.md`
- Modify: `docs/acceptance/threads/wave5/00_generic.thread_acceptance.md`

- [ ] **Step 1: 写失败测试/校验，确认当前运行矩阵未冻结**

Run:
```bash
python -c "import sys; print(sys.version)"
python -m backend.cli.entrypoint --help
python scripts/check_decision_runtime_smoke.py --strict-dry-run
```

Expected:
- 当前环境可能是 Python 3.14
- 运行中会出现 `langchain_core` / `requests` 兼容告警

- [ ] **Step 2: 先固定 Python 运行矩阵**

`pyproject.toml` 调整为显式 Phase 1 目标范围，例如：

```toml
requires-python = ">=3.11,<3.13"
```

`README.md` 与 acceptance docs 先只追加：
- Phase 1 官方 Python 版本
- 进入验收前必须在该版本下重跑 smoke

- [ ] **Step 3: 在固定矩阵下运行真实 smoke**

Run:
```bash
python -m pytest backend/decision/adapters/test_cryptoagents_runner.py -q
python -m unittest scripts.test_phase1_regression -v
python scripts/check_decision_runtime_smoke.py --strict-dry-run
```

Expected:
- pinned Python 版本下，strict dry-run 不再出现 Python 3.14 兼容告警

- [ ] **Step 4: 仅在矩阵收敛后，再调 timeout/retry 默认值**

`.env.example` 增加 Phase 1 推荐默认值：

```dotenv
# Phase 1 acceptance profile
CRYPTOAGENTS_LLM_TIMEOUT_SECONDS=60
CRYPTOAGENTS_LLM_MAX_RETRIES=1
```

`README.md` 与 acceptance docs 此时再追加：
- 官方 OpenAI / 自定义 gateway 策略
- strict dry-run / real run / doctor 的通过标准

`cryptoagents_runner.py` 中仅做“保守默认值”收敛：
- 保持现有 env 钩子
- 把默认超时/重试改成适合 CLI 的短路径
- 不用 timeout/retry 去掩盖结构性网络故障

- [ ] **Step 5: 运行最终回归**

Run:
```bash
python -m pytest backend/decision/adapters/test_cryptoagents_runner.py -q
python -m pytest backend/execution/runtime/test_contract_gateway.py -q
python -m unittest scripts.test_phase1_regression -v
python scripts/run_phase1_regression.py --with-llm --with-chain
```

Expected:
- `doctor --gate full` 通过
- `check_llm_channel_smoke.py` 通过
- strict `decision dry-run` 通过且 `decision_source=production`
- real `decision run` 通过且拿到 `register_tx_hash` 与成功 receipt
- 无 Python 3.14 兼容告警出现在 Phase 1 验收环境

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example README.md backend/decision/adapters/cryptoagents_runner.py docs/acceptance/threads/wave5/ops_readiness.test_evidence.md docs/acceptance/threads/wave5/00_generic.thread_acceptance.md
git commit -m "chore: freeze phase1 runtime matrix and acceptance profile"
```

---

## 风险与回滚

- 风险 1：默认 fail-closed 会让之前“能跑通 demo” 的 fallback 路径直接失败。
  - 处理：接受这次破坏性变更；fallback 不再属于用户路径，也不再属于 Phase 1 验收口径。
- 风险 2：把缺失 `OPENAI_BASE_URL` 解释成官方默认，可能影响当前依赖“必须显式配置 base URL”的本地脚本。
  - 处理：`doctor` payload 保留 `openai_base_url_mode`，并在 docs 中标注迁移方式。
- 风险 3：RPC 稳态化若实现不当，可能导致重复广播。
  - 处理：只 retry 读与 receipt 阶段；广播阶段只抛 `ContractBroadcastUncertainError`，不自动 resend。
- 风险 4：收窄 Python 版本可能让部分开发机短期需要降版本。
  - 处理：先冻结 Phase 1 验收矩阵，再决定是否保留更宽的开发矩阵。
- 回滚策略：
  - Task 1/2/3/4/5 各自独立提交，按任务粒度回滚。

## 完成定义（DoD）

- `decision dry-run` 与 `decision run` 用户路径中不存在 fallback。
- 所有成功的 `decision` 结果都显式包含 `decision_source=production`。
- `OPENAI_BASE_URL` 语义明确，官方默认与自定义 gateway 可区分、可诊断、可验收。
- Phase 1 总回归必须包含 strict dry-run 和 real decision run 两条真实用户路径。
- 真实 `decision run` 成功时必须拿到可验证的 `register_tx_hash` / receipt。
- Phase 1 验收环境冻结到明确的 Python 版本与 timeout/retry 配置，不再依赖“当前机器碰巧能跑”。
- 修复过程中不允许用 broad `try/except`、隐式 fallback 或多余分支把根因埋掉。
