from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from strategy.models import (
    BpsRange,
    BoundaryDecision,
    StrategyIntent,
    StrategyTemplate,
    TradeIntent,
)
from strategy.strategy_boundary_service import StrategyBoundaryService


def _template(version: int) -> StrategyTemplate:
    return StrategyTemplate(
        template_id="swing_eth",
        version=version,
        auto_allowed_pairs=frozenset({"ETH/USDC"}),
        manual_allowed_pairs=frozenset({"ARB/USDC"}),
        auto_allowed_dexes=frozenset({"uniswap-v3"}),
        manual_allowed_dexes=frozenset({"sushiswap"}),
        auto_max_position_usd=Decimal("10000"),
        hard_max_position_usd=Decimal("20000"),
        auto_max_slippage_bps=100,
        hard_max_slippage_bps=300,
        auto_stop_loss_bps_range=BpsRange(min_bps=100, max_bps=300),
        manual_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=500),
        auto_take_profit_bps_range=BpsRange(min_bps=200, max_bps=800),
        manual_take_profit_bps_range=BpsRange(min_bps=100, max_bps=1200),
        auto_daily_trade_limit=3,
        hard_daily_trade_limit=6,
        execution_mode="conditional",
    )


def _strategy_intent(template_version: int) -> StrategyIntent:
    return StrategyIntent(
        strategy_intent_id="si_001",
        template_id="swing_eth",
        template_version=template_version,
        execution_mode="conditional",
        projected_daily_trade_count=2,
    )


def _trade_intent(pair: str = "ETH/USDC", position_usd: str = "5000") -> TradeIntent:
    return TradeIntent(
        trade_intent_id="ti_001",
        strategy_intent_id="si_001",
        pair=pair,
        dex="uniswap-v3",
        position_usd=Decimal(position_usd),
        max_slippage_bps=80,
        stop_loss_bps=200,
        take_profit_bps=500,
        entry_conditions=["price <= 1800"],
        ttl_seconds=3600,
    )


def test_auto_register_for_in_template_trade() -> None:
    service = StrategyBoundaryService(templates=[_template(1), _template(2)])

    result = service.evaluate(_strategy_intent(template_version=2), _trade_intent())

    assert result.boundary_decision == BoundaryDecision.AUTO_REGISTER
    assert any(item.rule_name == "template_version_boundary" for item in result.trace)


def test_manual_approval_for_outside_auto_but_inside_manual_boundary() -> None:
    service = StrategyBoundaryService(templates=[_template(2)])

    result = service.evaluate(_strategy_intent(template_version=2), _trade_intent(pair="ARB/USDC"))

    assert result.boundary_decision == BoundaryDecision.MANUAL_APPROVAL
    pair_trace = next(item for item in result.trace if item.rule_name == "pair")
    assert pair_trace.decision.value == "manual"


def test_reject_for_hard_boundary_violation() -> None:
    service = StrategyBoundaryService(templates=[_template(2)])

    result = service.evaluate(_strategy_intent(template_version=2), _trade_intent(position_usd="25000"))

    assert result.boundary_decision == BoundaryDecision.REJECT
    position_trace = next(item for item in result.trace if item.rule_name == "position_usd")
    assert position_trace.decision.value == "reject"


def test_manual_approval_for_non_latest_existing_template_version() -> None:
    service = StrategyBoundaryService(templates=[_template(1), _template(2)])

    result = service.evaluate(_strategy_intent(template_version=1), _trade_intent())

    assert result.boundary_decision == BoundaryDecision.MANUAL_APPROVAL
    version_trace = next(item for item in result.trace if item.rule_name == "template_version_boundary")
    assert version_trace.decision.value == "manual"
