from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from backend.data.context_builder.models import (
    CapitalFlow,
    DecisionContext,
    ExecutionState,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    RiskState,
    StrategyConstraints,
    TrendDirection,
)
from backend.decision.adapters.cryptoagents_runner import (
    CryptoAgentsRunnerDependencyError,
    CryptoAgentsStructuredOutputMissingError,
    ProductionCryptoAgentsRunner,
    _load_default_graph,
)


class _FakeGraph:
    def __init__(self, *, final_state, signal) -> None:
        self._final_state = final_state
        self._signal = signal
        self.calls: list[tuple[str, str]] = []

    def propagate(self, symbol: str, trade_date: str):
        self.calls.append((symbol, trade_date))
        return self._final_state, self._signal


class _FakeProjector:
    def __init__(self, *, result: dict[str, object]) -> None:
        self._result = result
        self.calls: list[tuple[DecisionContext, dict[str, object], object]] = []

    def project(
        self,
        *,
        decision_context: DecisionContext,
        final_state: dict[str, object],
        signal: object,
    ) -> dict[str, object]:
        self.calls.append((decision_context, final_state, signal))
        return dict(self._result)


def _decision_context() -> DecisionContext:
    return DecisionContext(
        market_trend=MarketTrend(
            direction=TrendDirection.UP,
            confidence_score=Decimal("0.72"),
            timeframe_minutes=240,
        ),
        capital_flow=CapitalFlow(
            net_inflow_usd=Decimal("1500000"),
            volume_24h_usd=Decimal("53000000"),
            whale_inflow_usd=Decimal("500000"),
            retail_inflow_usd=Decimal("1000000"),
        ),
        liquidity_depth=LiquidityDepth(
            pair="ETH/USDC",
            dex="uniswap_v3",
            depth_usd_2pct=Decimal("30000000"),
            total_tvl_usd=Decimal("800000000"),
        ),
        onchain_flow=OnchainFlow(
            active_address_delta_24h=2800,
            transaction_count_24h=1220000,
            gas_price_gwei=Decimal("18.3"),
        ),
        risk_state=RiskState(
            volatility_annualized=Decimal("0.44"),
            var_95_usd=Decimal("2200"),
            correlation_to_market=Decimal("0.81"),
        ),
        position_state=PositionState(
            current_position_usd=Decimal("0"),
            unrealized_pnl_usd=Decimal("0"),
        ),
        execution_state=ExecutionState(
            daily_trades_executed=0,
            daily_volume_usd=Decimal("0"),
        ),
        strategy_constraints=StrategyConstraints(
            pair="ETH/USDC",
            dex="uniswap_v3",
            max_position_usd=Decimal("5000"),
            max_slippage_bps=30,
            stop_loss_bps=150,
            take_profit_bps=300,
            ttl_seconds=7200,
            daily_trade_limit=2,
        ),
        context_id="ctx-001",
    )


class ProductionCryptoAgentsRunnerTestCase(unittest.TestCase):
    def test_load_default_graph_applies_model_overrides_from_env(self) -> None:
        captured: dict[str, object] = {}

        class _CaptureTradingGraph:
            def __init__(self, *, selected_analysts, debug, config):
                captured["selected_analysts"] = selected_analysts
                captured["debug"] = debug
                captured["config"] = config

            def propagate(self, company_name: str, trade_date: str):
                return {}, None

        class _FakeConfigModule:
            CRYPTO_CONFIG = {
                "deep_think_llm": "o4-mini",
                "quick_think_llm": "gpt-4o-mini",
            }

        class _FakeTradingModule:
            TradingAgentsGraph = _CaptureTradingGraph

        def _fake_import(name: str):
            if name == "cryptoagents.graph.trading_graph":
                return _FakeTradingModule
            if name == "cryptoagents.config":
                return _FakeConfigModule
            raise AssertionError(f"unexpected import: {name}")

        with patch("backend.decision.adapters.cryptoagents_runner._inject_cryptoagents_ref_path"):
            with patch("backend.decision.adapters.cryptoagents_runner.importlib.import_module", side_effect=_fake_import):
                with patch.dict(
                    os.environ,
                    {
                        "CRYPTOAGENTS_DEEP_THINK_LLM": "gpt-5.4",
                        "CRYPTOAGENTS_QUICK_THINK_LLM": "gpt-5.4-mini",
                        "OPENAI_BASE_URL": "",
                    },
                    clear=False,
                ):
                    _load_default_graph()

        config = captured["config"]
        self.assertEqual(config["deep_think_llm"], "gpt-5.4")
        self.assertEqual(config["quick_think_llm"], "gpt-5.4-mini")

    def test_load_default_graph_applies_llm_timeout_and_retry_overrides(self) -> None:
        captured_chat_kwargs: list[dict[str, object]] = []

        class _CaptureTradingGraph:
            def __init__(self, *, selected_analysts, debug, config):
                _ = selected_analysts, debug, config
                module.ChatOpenAI(model="quick-model")
                module.ChatOpenAI(model="deep-model")

            def propagate(self, company_name: str, trade_date: str):
                _ = company_name, trade_date
                return {}, None

        class _FakeConfigModule:
            CRYPTO_CONFIG = {}

        class _FakeTradingModule:
            TradingAgentsGraph = _CaptureTradingGraph

        module = _FakeTradingModule

        def _capture_chat_openai(*args, **kwargs):
            _ = args
            captured_chat_kwargs.append(dict(kwargs))
            return object()

        module.ChatOpenAI = _capture_chat_openai

        def _fake_import(name: str):
            if name == "cryptoagents.graph.trading_graph":
                return module
            if name == "cryptoagents.config":
                return _FakeConfigModule
            raise AssertionError(f"unexpected import: {name}")

        with patch("backend.decision.adapters.cryptoagents_runner._inject_cryptoagents_ref_path"):
            with patch("backend.decision.adapters.cryptoagents_runner.importlib.import_module", side_effect=_fake_import):
                with patch.dict(
                    os.environ,
                    {
                        "CRYPTOAGENTS_LLM_TIMEOUT_SECONDS": "45",
                        "CRYPTOAGENTS_LLM_MAX_RETRIES": "6",
                        "OPENAI_BASE_URL": "",
                    },
                    clear=False,
                ):
                    _load_default_graph()

        self.assertGreaterEqual(len(captured_chat_kwargs), 2)
        for kwargs in captured_chat_kwargs:
            self.assertEqual(kwargs["timeout"], 45.0)
            self.assertEqual(kwargs["max_retries"], 6)

    def test_load_default_graph_rejects_invalid_llm_timeout_override(self) -> None:
        class _CaptureTradingGraph:
            def __init__(self, *, selected_analysts, debug, config):
                _ = selected_analysts, debug, config

            def propagate(self, company_name: str, trade_date: str):
                _ = company_name, trade_date
                return {}, None

        class _FakeConfigModule:
            CRYPTO_CONFIG = {}

        class _FakeTradingModule:
            TradingAgentsGraph = _CaptureTradingGraph
            ChatOpenAI = object

        def _fake_import(name: str):
            if name == "cryptoagents.graph.trading_graph":
                return _FakeTradingModule
            if name == "cryptoagents.config":
                return _FakeConfigModule
            raise AssertionError(f"unexpected import: {name}")

        with patch("backend.decision.adapters.cryptoagents_runner._inject_cryptoagents_ref_path"):
            with patch("backend.decision.adapters.cryptoagents_runner.importlib.import_module", side_effect=_fake_import):
                with patch.dict(
                    os.environ,
                    {
                        "CRYPTOAGENTS_LLM_TIMEOUT_SECONDS": "0",
                        "OPENAI_BASE_URL": "",
                    },
                    clear=False,
                ):
                    with self.assertRaises(CryptoAgentsRunnerDependencyError):
                        _load_default_graph()

    def test_load_default_graph_applies_embedding_model_override_for_verified_relay(self) -> None:
        captured_embedding_model: dict[str, str] = {}

        class _CaptureTradingGraph:
            def __init__(self, *, selected_analysts, debug, config):
                _ = selected_analysts, debug, config

            def propagate(self, company_name: str, trade_date: str):
                _ = company_name, trade_date
                return {}, None

        class _FakeConfigModule:
            CRYPTO_CONFIG = {}

        class _FakeEmbeddingsClient:
            @staticmethod
            def create(*, model: str, input: str):
                captured_embedding_model["model"] = model
                _ = input
                return type(
                    "_EmbeddingResponse",
                    (),
                    {"data": [type("_EmbeddingItem", (), {"embedding": [0.1, 0.2, 0.3]})()]},
                )()

        class _FakeMemory:
            def __init__(self, name):
                _ = name
                self.client = type("_OpenAIClient", (), {"embeddings": _FakeEmbeddingsClient()})()

            def get_embedding(self, text):
                _ = text
                return []

        class _FakeMemoryModule:
            FinancialSituationMemory = _FakeMemory

        class _FakeTradingModule:
            TradingAgentsGraph = _CaptureTradingGraph
            ChatOpenAI = object

        def _fake_import(name: str):
            if name == "cryptoagents.graph.trading_graph":
                return _FakeTradingModule
            if name == "cryptoagents.config":
                return _FakeConfigModule
            if name == "cryptoagents.agents.utils.memory":
                return _FakeMemoryModule
            raise AssertionError(f"unexpected import: {name}")

        with patch("backend.decision.adapters.cryptoagents_runner._inject_cryptoagents_ref_path"):
            with patch("backend.decision.adapters.cryptoagents_runner.importlib.import_module", side_effect=_fake_import):
                with patch.dict(
                    os.environ,
                    {
                        "OPENAI_BASE_URL": "https://api.ofox.ai/v1",
                        "CRYPTOAGENTS_EMBEDDING_MODEL": "openai/text-embedding-3-small",
                    },
                    clear=False,
                ):
                    _load_default_graph()
                    memory = _FakeMemory("unit-test-memory")
                    embedding = memory.get_embedding("market context")

        self.assertEqual(captured_embedding_model["model"], "openai/text-embedding-3-small")
        self.assertEqual(embedding, [0.1, 0.2, 0.3])

    def test_runner_calls_real_graph_port_and_extracts_structured_decision(self) -> None:
        structured_output = {
            "pair": "ETH/USDC",
            "dex": "uniswap_v3",
            "position_usd": "1200",
            "max_slippage_bps": 20,
            "stop_loss_bps": 90,
            "take_profit_bps": 250,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": 3600,
            "projected_daily_trade_count": 1,
            "investment_thesis": "趋势仍在，回撤分批布局。",
            "confidence_score": "0.82",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "给出条件入场意图",
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ],
        }
        fake_graph = _FakeGraph(
            final_state={"structured_decision": structured_output},
            signal="BUY",
        )
        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: fake_graph,
            as_of_date_provider=lambda: date(2026, 1, 1),
        )

        output = runner.run(_decision_context())

        self.assertEqual(output, structured_output)
        self.assertEqual(fake_graph.calls, [("ETH", "2026-01-01")])

    def test_runner_passes_serialized_decision_context_when_graph_supports_it(self) -> None:
        structured_output = {
            "pair": "ETH/USDC",
            "dex": "uniswap_v3",
            "position_usd": "1200",
            "max_slippage_bps": 20,
            "stop_loss_bps": 90,
            "take_profit_bps": 250,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": 3600,
            "projected_daily_trade_count": 1,
            "investment_thesis": "context aware decision",
            "confidence_score": "0.81",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "uses injected decision_context",
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ],
        }
        captured: dict[str, object] = {}

        class _GraphWithDecisionContext:
            def propagate(self, symbol: str, trade_date: str, decision_context=None):
                captured["symbol"] = symbol
                captured["trade_date"] = trade_date
                captured["decision_context"] = decision_context
                return {"structured_decision": structured_output}, None

        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: _GraphWithDecisionContext(),
            as_of_date_provider=lambda: date(2026, 1, 1),
        )

        output = runner.run(_decision_context())

        self.assertEqual(output["investment_thesis"], "context aware decision")
        self.assertEqual(captured["symbol"], "ETH")
        self.assertEqual(captured["trade_date"], "2026-01-01")
        decision_context = captured["decision_context"]
        self.assertIsInstance(decision_context, dict)
        self.assertEqual(decision_context["context_id"], "ctx-001")
        self.assertEqual(decision_context["strategy_constraints"]["pair"], "ETH/USDC")

    def test_runner_rejects_unstructured_graph_output(self) -> None:
        fake_graph = _FakeGraph(
            final_state="free-text-without-structured-state",
            signal=None,
        )
        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: fake_graph,
            as_of_date_provider=lambda: date(2026, 1, 1),
        )

        with self.assertRaises(CryptoAgentsStructuredOutputMissingError):
            runner.run(_decision_context())

    def test_runner_projects_free_text_graph_output_into_structured_decision(self) -> None:
        fake_graph = _FakeGraph(
            final_state={
                "market_report": "trend up",
                "sentiment_report": "positive",
                "news_report": "ETF inflow",
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
                "projected_daily_trade_count": 1,
                "investment_thesis": "pullback entry",
                "confidence_score": "0.80",
                "agent_trace_steps": [
                    {
                        "agent": "portfolio_manager",
                        "summary": "projected fallback",
                        "timestamp": "2026-01-01T00:00:00+00:00",
                    }
                ],
            }
        )
        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: fake_graph,
            as_of_date_provider=lambda: date(2026, 1, 1),
            projector=fake_projector,
        )

        output = runner.run(_decision_context())

        self.assertEqual(output["pair"], "ETH/USDC")
        self.assertEqual(output["projected_daily_trade_count"], 1)
        self.assertEqual(len(fake_projector.calls), 1)

    def test_runner_raises_parse_error_when_projector_returns_missing_fields(self) -> None:
        fake_graph = _FakeGraph(
            final_state={"final_trade_decision": "Buy on pullback with tight risk."},
            signal="BUY",
        )
        fake_projector = _FakeProjector(result={"pair": "ETH/USDC"})
        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: fake_graph,
            as_of_date_provider=lambda: date(2026, 1, 1),
            projector=fake_projector,
        )

        with self.assertRaises(CryptoAgentsStructuredOutputMissingError):
            runner.run(_decision_context())

    def test_runner_rejects_signal_only_projection_input(self) -> None:
        fake_graph = _FakeGraph(
            final_state={},
            signal="SELL",
        )
        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: fake_graph,
            as_of_date_provider=lambda: date(2026, 1, 1),
        )

        with self.assertRaises(CryptoAgentsStructuredOutputMissingError):
            runner.run(_decision_context())

    def test_runner_retries_runtime_connection_error_then_succeeds(self) -> None:
        api_connection_error = type("APIConnectionError", (Exception,), {})
        structured_output = {
            "pair": "ETH/USDC",
            "dex": "uniswap_v3",
            "position_usd": "1200",
            "max_slippage_bps": 20,
            "stop_loss_bps": 90,
            "take_profit_bps": 250,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": 3600,
            "projected_daily_trade_count": 1,
            "investment_thesis": "retry success",
            "confidence_score": "0.8",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "retry success",
                    "timestamp": "2026-01-01T00:00:00+00:00",
                }
            ],
        }
        calls: list[tuple[str, str]] = []
        outcomes: list[object] = [
            api_connection_error("temporary failure"),
            ({"structured_decision": structured_output}, None),
        ]

        class _FlakyGraph:
            def propagate(self, symbol: str, trade_date: str):
                calls.append((symbol, trade_date))
                outcome = outcomes.pop(0)
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome

        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: _FlakyGraph(),
            as_of_date_provider=lambda: date(2026, 1, 1),
            runtime_retry_attempts=2,
            retry_backoff_seconds=0,
            sleep_fn=lambda _: None,
        )

        output = runner.run(_decision_context())

        self.assertEqual(output["investment_thesis"], "retry success")
        self.assertEqual(calls, [("ETH", "2026-01-01"), ("ETH", "2026-01-01")])

    def test_runner_raises_dependency_error_after_retry_exhaustion(self) -> None:
        api_connection_error = type("APIConnectionError", (Exception,), {})
        calls: list[tuple[str, str]] = []

        class _AlwaysFailGraph:
            def propagate(self, symbol: str, trade_date: str):
                calls.append((symbol, trade_date))
                raise api_connection_error("network broken")

        runner = ProductionCryptoAgentsRunner(
            graph_factory=lambda: _AlwaysFailGraph(),
            as_of_date_provider=lambda: date(2026, 1, 1),
            runtime_retry_attempts=2,
            retry_backoff_seconds=0,
            sleep_fn=lambda _: None,
        )

        with self.assertRaises(CryptoAgentsRunnerDependencyError):
            runner.run(_decision_context())
        self.assertEqual(calls, [("ETH", "2026-01-01"), ("ETH", "2026-01-01")])


if __name__ == "__main__":
    unittest.main()
