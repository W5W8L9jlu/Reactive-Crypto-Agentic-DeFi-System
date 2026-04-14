from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

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
from backend.decision.adapters.cryptoagents_adapter import (
    CryptoAgentsAdapter,
    CryptoAgentsConstraintMismatchError,
)
from backend.strategy.models import StrategyTemplate


class _FakeRunner:
    def run(self, context: DecisionContext) -> dict[str, object]:
        return {
            "pair": context.strategy_constraints.pair,
            "dex": context.strategy_constraints.dex,
            "position_usd": "1200",
            "max_slippage_bps": 25,
            "stop_loss_bps": 120,
            "take_profit_bps": 260,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": 3600,
            "projected_daily_trade_count": 1,
            "investment_thesis": "趋势仍在，回撤分批布局。",
            "confidence_score": "0.82",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "给出条件入场意图",
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            ],
        }


class _ConstraintBreakingRunner:
    def run(self, context: DecisionContext) -> dict[str, object]:
        return {
            "pair": context.strategy_constraints.pair,
            "dex": context.strategy_constraints.dex,
            "position_usd": "999999",
            "max_slippage_bps": 999,
            "stop_loss_bps": 999,
            "take_profit_bps": 999,
            "entry_conditions": ["buy_now"],
            "ttl_seconds": 999999,
            "projected_daily_trade_count": 1,
            "investment_thesis": "invalid output",
            "confidence_score": "0.82",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "invalid output",
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            ],
        }


class _MarketOrderLikeConditionRunner:
    def run(self, context: DecisionContext) -> dict[str, object]:
        return {
            "pair": context.strategy_constraints.pair,
            "dex": context.strategy_constraints.dex,
            "position_usd": "1200",
            "max_slippage_bps": 20,
            "stop_loss_bps": 120,
            "take_profit_bps": 260,
            "entry_conditions": ["buy_now:immediate"],
            "ttl_seconds": 3600,
            "projected_daily_trade_count": 1,
            "investment_thesis": "invalid market-order-like condition",
            "confidence_score": "0.82",
            "agent_trace_steps": [
                {
                    "agent": "portfolio_manager",
                    "summary": "invalid market-order-like condition",
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            ],
        }


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


def _strategy_template() -> StrategyTemplate:
    from backend.strategy.models import BpsRange

    return StrategyTemplate(
        template_id="tpl-eth-swing",
        version=1,
        auto_allowed_pairs=frozenset({"ETH/USDC"}),
        manual_allowed_pairs=frozenset(),
        auto_allowed_dexes=frozenset({"uniswap_v3"}),
        manual_allowed_dexes=frozenset(),
        auto_max_position_usd=Decimal("5000"),
        hard_max_position_usd=Decimal("10000"),
        auto_max_slippage_bps=30,
        hard_max_slippage_bps=100,
        auto_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=200),
        manual_stop_loss_bps_range=BpsRange(min_bps=20, max_bps=300),
        auto_take_profit_bps_range=BpsRange(min_bps=100, max_bps=600),
        manual_take_profit_bps_range=BpsRange(min_bps=50, max_bps=1200),
        auto_daily_trade_limit=2,
        hard_daily_trade_limit=8,
        execution_mode="conditional",
    )


class CryptoAgentsAdapterTestCase(unittest.TestCase):
    def test_adapter_outputs_conditional_intent_and_separates_thesis(self) -> None:
        adapter = CryptoAgentsAdapter(runner=_FakeRunner())
        result = adapter.build_decision_or_raise(
            decision_context=_decision_context(),
            strategy_template=_strategy_template(),
        )

        self.assertEqual(result.strategy_intent.template_id, "tpl-eth-swing")
        self.assertEqual(result.trade_intent.pair, "ETH/USDC")
        self.assertEqual(result.trade_intent.dex, "uniswap_v3")
        self.assertEqual(result.trade_intent.position_usd, Decimal("1200"))
        self.assertNotIn("investment_thesis", result.trade_intent.model_dump(mode="python"))
        self.assertEqual(result.decision_meta.investment_thesis, "趋势仍在，回撤分批布局。")
        self.assertGreaterEqual(len(result.agent_trace.steps), 1)

    def test_adapter_rejects_output_when_constraints_are_violated(self) -> None:
        adapter = CryptoAgentsAdapter(runner=_ConstraintBreakingRunner())
        with self.assertRaises(CryptoAgentsConstraintMismatchError):
            adapter.build_decision_or_raise(
                decision_context=_decision_context(),
                strategy_template=_strategy_template(),
            )

    def test_adapter_rejects_market_order_like_entry_condition_even_with_colon(self) -> None:
        adapter = CryptoAgentsAdapter(runner=_MarketOrderLikeConditionRunner())
        with self.assertRaises(CryptoAgentsConstraintMismatchError):
            adapter.build_decision_or_raise(
                decision_context=_decision_context(),
                strategy_template=_strategy_template(),
            )


if __name__ == "__main__":
    unittest.main()
