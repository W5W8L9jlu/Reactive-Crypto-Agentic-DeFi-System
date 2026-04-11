from __future__ import annotations

import os
import sys
import unittest
from decimal import Decimal

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.strategy.models import BpsRange, BoundaryDecision, StrategyIntent, StrategyTemplate, TradeIntent
from backend.strategy.strategy_boundary_service import StrategyBoundaryService


def _template() -> StrategyTemplate:
    return StrategyTemplate(
        template_id="tpl-risk",
        version=1,
        auto_allowed_pairs=frozenset({"ETH/USDC"}),
        manual_allowed_pairs=frozenset({"ARB/USDC"}),
        auto_allowed_dexes=frozenset({"uniswap-v3"}),
        manual_allowed_dexes=frozenset({"sushiswap"}),
        auto_max_position_usd=Decimal("5000"),
        hard_max_position_usd=Decimal("10000"),
        auto_max_slippage_bps=30,
        hard_max_slippage_bps=80,
        auto_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=200),
        manual_stop_loss_bps_range=BpsRange(min_bps=10, max_bps=400),
        auto_take_profit_bps_range=BpsRange(min_bps=100, max_bps=500),
        manual_take_profit_bps_range=BpsRange(min_bps=50, max_bps=1000),
        auto_daily_trade_limit=2,
        hard_daily_trade_limit=8,
        auto_max_daily_loss_pct_nav=Decimal("0.03"),
        hard_max_daily_loss_pct_nav=Decimal("0.05"),
        auto_max_consecutive_loss_count=2,
        hard_max_consecutive_loss_count=3,
        execution_mode="conditional",
    )


def _strategy_intent(
    *,
    projected_daily_loss_pct_nav: str,
    projected_consecutive_loss_count: int,
) -> StrategyIntent:
    return StrategyIntent(
        strategy_intent_id="si-risk-001",
        template_id="tpl-risk",
        template_version=1,
        execution_mode="conditional",
        projected_daily_trade_count=1,
        projected_daily_loss_pct_nav=Decimal(projected_daily_loss_pct_nav),
        projected_consecutive_loss_count=projected_consecutive_loss_count,
    )


def _trade_intent() -> TradeIntent:
    return TradeIntent(
        trade_intent_id="ti-risk-001",
        strategy_intent_id="si-risk-001",
        pair="ETH/USDC",
        dex="uniswap-v3",
        position_usd=Decimal("1000"),
        max_slippage_bps=20,
        stop_loss_bps=90,
        take_profit_bps=250,
        entry_conditions=["price_below:3000"],
        ttl_seconds=3600,
    )


class StrategyRiskBoundaryTests(unittest.TestCase):
    def test_auto_register_when_daily_loss_and_streak_within_auto_boundary(self) -> None:
        service = StrategyBoundaryService(templates=[_template()])

        result = service.evaluate(
            _strategy_intent(projected_daily_loss_pct_nav="0.01", projected_consecutive_loss_count=1),
            _trade_intent(),
        )

        self.assertEqual(result.boundary_decision, BoundaryDecision.AUTO_REGISTER)
        self.assertTrue(any(item.rule_name == "projected_daily_loss_pct_nav" for item in result.trace))
        self.assertTrue(any(item.rule_name == "projected_consecutive_loss_count" for item in result.trace))

    def test_manual_approval_when_daily_loss_exceeds_auto_but_within_hard_boundary(self) -> None:
        service = StrategyBoundaryService(templates=[_template()])

        result = service.evaluate(
            _strategy_intent(projected_daily_loss_pct_nav="0.04", projected_consecutive_loss_count=1),
            _trade_intent(),
        )

        self.assertEqual(result.boundary_decision, BoundaryDecision.MANUAL_APPROVAL)
        daily_loss_trace = next(item for item in result.trace if item.rule_name == "projected_daily_loss_pct_nav")
        self.assertEqual(daily_loss_trace.decision.value, "manual")

    def test_reject_when_consecutive_loss_exceeds_hard_boundary(self) -> None:
        service = StrategyBoundaryService(templates=[_template()])

        result = service.evaluate(
            _strategy_intent(projected_daily_loss_pct_nav="0.02", projected_consecutive_loss_count=4),
            _trade_intent(),
        )

        self.assertEqual(result.boundary_decision, BoundaryDecision.REJECT)
        streak_trace = next(item for item in result.trace if item.rule_name == "projected_consecutive_loss_count")
        self.assertEqual(streak_trace.decision.value, "reject")


if __name__ == "__main__":
    unittest.main()
