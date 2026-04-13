# Reactive Agent Structured CryptoAgents Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the upstream CryptoAgents multi-agent research flow, but make it produce stable local `PortfolioManagerOutput`-compatible conditional intents that can flow through the existing decision adapter and main-chain orchestration without changing reactive runtime behavior.

**Architecture:** Treat upstream CryptoAgents as a research engine, not an execution truth source. Add a local projection seam inside `backend/decision` that converts upstream graph state and final narrative decision into strict structured output, then keep using the existing `CryptoAgentsAdapter -> MainChainService -> reactive_runtime` path. Do not move any agent reasoning into `backend/reactive`; reactive remains deterministic callback execution plus verification.

**Tech Stack:** Python 3.11+, Pydantic v2, `unittest`, external `CryptoAgents` graph integration

---

## Scope Split

This work touches two local subsystems:

1. `backend/decision`
2. `backend/reactive` integration verification only

They are coupled enough to keep in one implementation plan, but actual code changes should stay concentrated in `backend/decision` and existing integration tests. Do not redesign `backend/reactive/adapters/runtime.py`.

## File Map

- Modify: `backend/decision/adapters/cryptoagents_runner.py`
  Responsibility: call upstream graph, normalize graph output, and hand off to a local structured projector when upstream only returns free text.
- Create: `backend/decision/adapters/cryptoagents_projector.py`
  Responsibility: convert upstream reports and final narrative decision into strict `PortfolioManagerOutput`-shaped data.
- Create: `backend/decision/prompts/__init__.py`
  Responsibility: package marker for prompt assets.
- Create: `backend/decision/prompts/cryptoagents_structured_output.md`
  Responsibility: one canonical local prompt that forces conditional intent output and forbids market-order style output.
- Modify: `backend/decision/adapters/cryptoagents_adapter.py`
  Responsibility: tighten local constraint alignment before building `StrategyIntent` and `TradeIntent`.
- Modify: `backend/decision/adapters/test_cryptoagents_runner.py`
  Responsibility: cover projector fallback, parse failures, and upstream-free-text normalization.
- Modify: `backend/decision/schemas/test_cryptoagents_adapter.py`
  Responsibility: cover local constraint violations and thesis / execution-field separation.
- Modify: `backend/decision/orchestrator/test_main_chain_service.py`
  Responsibility: prove the structured decision flows through registration and reactive execution unchanged.
- Reuse only, no redesign: `backend/reactive/adapters/runtime.py`
  Responsibility: deterministic runtime execution and callback verification remain unchanged.
- Reuse only, no redesign: `backend/reactive/adapters/test_reactive_runtime.py`
  Responsibility: keep runtime invariants locked while decision-layer changes land upstream.

## Out of Scope

- Replacing upstream LangGraph orchestration
- Moving agent logic into reactive runtime
- Letting AI generate calldata, sign, or bypass strategy / validation layers
- Building provider-routing, CLI polish, or memory/reflection features in this pass

### Task 1: Add a Local Structured Projection Seam

**Files:**
- Create: `backend/decision/adapters/cryptoagents_projector.py`
- Create: `backend/decision/prompts/__init__.py`
- Create: `backend/decision/prompts/cryptoagents_structured_output.md`
- Modify: `backend/decision/adapters/cryptoagents_runner.py`
- Test: `backend/decision/adapters/test_cryptoagents_runner.py`

- [ ] **Step 1: Write the failing runner test for free-text upstream output**

```python
def test_runner_projects_free_text_graph_output_into_structured_decision():
    fake_graph = _FakeGraph(
        final_state={
            "market_report": "trend up",
            "sentiment_report": "sentiment positive",
            "news_report": "ETF inflow positive",
            "fundamentals_report": "TVL rising",
            "final_trade_decision": "Buy on pullback with tight risk.",
        },
        signal="BUY",
    )

    fake_projector = _FakeProjector(
        result={
            "pair": "ETH/USDC",
            "dex": "uniswap_v3",
            "position_usd": "1000",
            "max_slippage_bps": 20,
            "stop_loss_bps": 100,
            "take_profit_bps": 250,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": 3600,
            "investment_thesis": "pullback entry",
            "confidence_score": "0.80",
            "agent_trace_steps": [...],
        }
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner.ProductionCryptoAgentsRunnerTestCase.test_runner_projects_free_text_graph_output_into_structured_decision -v`

Expected: FAIL because the runner currently only accepts pre-structured dict output.

- [ ] **Step 3: Write the failing test for projector parse failure**

```python
def test_runner_raises_parse_error_when_projector_returns_missing_fields():
    fake_projector = _FakeProjector(result={"pair": "ETH/USDC"})
    with self.assertRaises(CryptoAgentsStructuredOutputMissingError):
        runner.run(_decision_context())
```

- [ ] **Step 4: Run the two new tests**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner -v`

Expected: FAIL in the two new cases only.

- [ ] **Step 5: Create the canonical structured-output prompt asset**

Write `backend/decision/prompts/cryptoagents_structured_output.md` with these hard rules:

```text
Return JSON only.
Do not return markdown.
Output must include:
- pair
- dex
- position_usd
- max_slippage_bps
- stop_loss_bps
- take_profit_bps
- entry_conditions
- ttl_seconds
- projected_daily_trade_count
- investment_thesis
- confidence_score
- agent_trace_steps

Rules:
- conditional intent only
- no market order language
- no calldata
- thesis text must stay separate from execution fields
- pair and dex must match strategy constraints exactly
```

- [ ] **Step 6: Implement `cryptoagents_projector.py`**

Use one small focused interface:

```python
class CryptoAgentsProjectorPort(Protocol):
    def project(
        self,
        *,
        decision_context: DecisionContext,
        final_state: dict[str, Any],
        signal: Any,
    ) -> dict[str, Any]: ...
```

Implement one local default projector that:

1. Reads the local prompt asset
2. Builds a projection payload from:
   - `DecisionContext`
   - analyst reports
   - upstream final decision text
3. Calls one LLM or structured-output backend
4. Returns a dict shaped exactly like `PortfolioManagerOutput`
5. Raises a local parse error on missing / invalid fields

- [ ] **Step 7: Wire the projector into `cryptoagents_runner.py`**

Use this rule:

```python
structured = _extract_structured_output(...)
if structured is None:
    structured = projector.project(
        decision_context=context,
        final_state=final_state,
        signal=signal,
    )
return _validate_required_structured_keys(structured)
```

Do not silently fall back to BUY/HOLD/SELL text.

- [ ] **Step 8: Run focused runner tests**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner -v`

Expected: PASS, including old extraction tests and new projector-fallback tests.

- [ ] **Step 9: Commit**

```bash
git add backend/decision/adapters/cryptoagents_runner.py backend/decision/adapters/cryptoagents_projector.py backend/decision/adapters/test_cryptoagents_runner.py backend/decision/prompts/__init__.py backend/decision/prompts/cryptoagents_structured_output.md
git commit -m "feat: add structured projector for CryptoAgents output"
```

### Task 2: Tighten Adapter Constraint Alignment at the Decision Boundary

**Files:**
- Modify: `backend/decision/adapters/cryptoagents_adapter.py`
- Modify: `backend/decision/schemas/test_cryptoagents_adapter.py`

- [ ] **Step 1: Write the failing test for slippage overflow**

```python
def test_adapter_rejects_output_when_slippage_exceeds_context_cap():
    runner = _FakeRunner(max_slippage_bps=35)
    with self.assertRaises(CryptoAgentsConstraintMismatchError):
        adapter.build_decision_or_raise(...)
```

- [ ] **Step 2: Write the failing test for TTL mismatch**

```python
def test_adapter_rejects_output_when_ttl_exceeds_context_cap():
    runner = _FakeRunner(ttl_seconds=10800)
    with self.assertRaises(CryptoAgentsConstraintMismatchError):
        adapter.build_decision_or_raise(...)
```

- [ ] **Step 3: Write the failing test for non-conditional entry**

```python
def test_adapter_rejects_empty_or_nonconditional_entry_conditions():
    runner = _FakeRunner(entry_conditions=["buy_now"])
    with self.assertRaises(CryptoAgentsConstraintMismatchError):
        adapter.build_decision_or_raise(...)
```

- [ ] **Step 4: Run adapter tests to confirm failures**

Run: `python -m unittest backend.decision.schemas.test_cryptoagents_adapter -v`

Expected: FAIL in the newly added validation cases.

- [ ] **Step 5: Implement minimal alignment checks in `cryptoagents_adapter.py`**

Add explicit checks for:

```python
portfolio_output.position_usd <= decision_context.strategy_constraints.max_position_usd
portfolio_output.max_slippage_bps <= decision_context.strategy_constraints.max_slippage_bps
portfolio_output.stop_loss_bps <= decision_context.strategy_constraints.stop_loss_bps
portfolio_output.take_profit_bps <= decision_context.strategy_constraints.take_profit_bps
portfolio_output.ttl_seconds <= decision_context.strategy_constraints.ttl_seconds
all(":" in item for item in portfolio_output.entry_conditions)
```

Keep errors explicit. Do not add silent clamping.

- [ ] **Step 6: Run adapter tests**

Run: `python -m unittest backend.decision.schemas.test_cryptoagents_adapter -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/decision/adapters/cryptoagents_adapter.py backend/decision/schemas/test_cryptoagents_adapter.py
git commit -m "fix: enforce conditional intent constraints in adapter"
```

### Task 3: Preserve a Stable Local Agent Trace

**Files:**
- Modify: `backend/decision/adapters/cryptoagents_projector.py`
- Modify: `backend/decision/adapters/test_cryptoagents_runner.py`

- [ ] **Step 1: Write the failing test for missing trace synthesis**

```python
def test_projector_synthesizes_agent_trace_steps_from_upstream_reports():
    output = projector.project(...)
    assert output["agent_trace_steps"][0]["agent"] == "market_analyst"
    assert len(output["agent_trace_steps"]) >= 3
```

- [ ] **Step 2: Run the focused test**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner -v`

Expected: FAIL because the projector does not yet synthesize deterministic trace steps.

- [ ] **Step 3: Implement minimal trace synthesis**

Derive steps in this order when source reports exist:

```python
[
    {"agent": "market_analyst", "summary": summarize(final_state["market_report"])},
    {"agent": "news_analyst", "summary": summarize(final_state["news_report"])},
    {"agent": "fundamentals_analyst", "summary": summarize(final_state["fundamentals_report"])},
    {"agent": "portfolio_manager", "summary": summarize(final_state["final_trade_decision"])},
]
```

Rules:

1. Short summaries only
2. UTC timestamps only
3. No raw full transcript dumps

- [ ] **Step 4: Run runner tests again**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner -v`

Expected: PASS with deterministic trace coverage.

- [ ] **Step 5: Commit**

```bash
git add backend/decision/adapters/cryptoagents_projector.py backend/decision/adapters/test_cryptoagents_runner.py
git commit -m "feat: synthesize stable agent trace from upstream reports"
```

### Task 4: Prove End-to-End Main-Chain Integration Without Changing Reactive Runtime

**Files:**
- Modify: `backend/decision/orchestrator/test_main_chain_service.py`
- Reuse: `backend/reactive/adapters/runtime.py`
- Reuse: `backend/reactive/adapters/test_reactive_runtime.py`

- [ ] **Step 1: Write the failing integration test for structured decision -> register -> entry trigger**

```python
def test_main_chain_service_accepts_projected_structured_decision_and_executes_entry():
    result = service.run_or_raise(request)
    assert result.decision.trade_intent.entry_conditions == ["price_below:3000"]
    assert result.reactive_runtime_result.callback_verified is True
```

- [ ] **Step 2: Write the failing integration test for stop-loss path**

```python
def test_main_chain_service_preserves_trade_intent_ids_into_stop_loss_runtime():
    result = service.run_or_raise(request_with_stop_loss_trigger)
    assert result.reactive_runtime_result.trigger_type is ReactiveTriggerType.STOP_LOSS
```

- [ ] **Step 3: Run focused main-chain tests**

Run: `python -m unittest backend.decision.orchestrator.test_main_chain_service -v`

Expected: FAIL until the new projector-backed decision path is fully wired through orchestration fixtures.

- [ ] **Step 4: Adjust orchestration test fixtures only as needed**

Do not change `backend/reactive/adapters/runtime.py` unless a real invariant bug is uncovered.

Allowed changes:

1. inject projector-backed fake runner output
2. update fixture payloads
3. assert callback verification fields

- [ ] **Step 5: Run the main-chain tests again**

Run: `python -m unittest backend.decision.orchestrator.test_main_chain_service -v`

Expected: PASS.

- [ ] **Step 6: Re-run runtime invariants to ensure no regression**

Run: `python -m unittest backend.reactive.adapters.test_reactive_runtime -v`

Expected: PASS unchanged.

- [ ] **Step 7: Commit**

```bash
git add backend/decision/orchestrator/test_main_chain_service.py
git commit -m "test: cover projected decision through main-chain runtime flow"
```

### Task 5: Final Verification Pass

**Files:**
- No new files
- Verify: `backend/decision/adapters/test_cryptoagents_runner.py`
- Verify: `backend/decision/schemas/test_cryptoagents_adapter.py`
- Verify: `backend/decision/orchestrator/test_main_chain_service.py`
- Verify: `backend/reactive/adapters/test_reactive_runtime.py`

- [ ] **Step 1: Run runner tests**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner -v`

Expected: PASS

- [ ] **Step 2: Run adapter schema tests**

Run: `python -m unittest backend.decision.schemas.test_cryptoagents_adapter -v`

Expected: PASS

- [ ] **Step 3: Run main-chain orchestration tests**

Run: `python -m unittest backend.decision.orchestrator.test_main_chain_service -v`

Expected: PASS

- [ ] **Step 4: Run reactive runtime tests**

Run: `python -m unittest backend.reactive.adapters.test_reactive_runtime -v`

Expected: PASS

- [ ] **Step 5: Run the four groups together**

Run: `python -m unittest backend.decision.adapters.test_cryptoagents_runner backend.decision.schemas.test_cryptoagents_adapter backend.decision.orchestrator.test_main_chain_service backend.reactive.adapters.test_reactive_runtime -v`

Expected: PASS

- [ ] **Step 6: Commit verification-only if needed**

```bash
git status
```

Expected: clean working tree or only intentionally staged changes.

## Follow-Up Plan Candidates

Not part of this implementation pass:

1. Multi-provider LLM client abstraction inspired by `TradingAgents`
2. Vendor-routed crypto data provider layer inspired by `TradingAgents.dataflows.interface`
3. Rich CLI / approval-surface observability inspired by `TradingAgents.cli`
4. BM25 reflection memory for post-trade memo generation only

## Success Criteria

- Upstream CryptoAgents can remain mostly untouched
- Local runner accepts both pre-structured output and projector-produced output
- Local adapter rejects any non-conditional or out-of-bounds execution fields
- Main-chain orchestration still reaches reactive runtime successfully
- Reactive runtime code and invariants stay deterministic and unchanged
