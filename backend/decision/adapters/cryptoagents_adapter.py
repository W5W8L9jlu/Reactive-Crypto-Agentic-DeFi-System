from __future__ import annotations

from typing import Protocol

from pydantic import ValidationError

from backend.data.context_builder.models import DecisionContext
from backend.decision.schemas.cryptoagents_adapter import (
    AgentTrace,
    CryptoAgentsDecision,
    DecisionMeta,
    PortfolioManagerOutput,
)
from backend.strategy.models import StrategyIntent, StrategyTemplate, TradeIntent


class CryptoAgentsAdapterError(ValueError):
    """Base domain error for the CryptoAgents adapter seam."""


class CryptoAgentsOutputParseError(CryptoAgentsAdapterError):
    """Raised when runner output cannot be parsed as structured conditional intent."""


class CryptoAgentsConstraintMismatchError(CryptoAgentsAdapterError):
    """Raised when adapter output violates explicit DecisionContext constraints."""


class CryptoAgentsRunnerPort(Protocol):
    def run(self, context: DecisionContext) -> PortfolioManagerOutput | dict[str, object]: ...


class CryptoAgentsAdapter:
    def __init__(self, *, runner: CryptoAgentsRunnerPort) -> None:
        self._runner = runner

    def build_decision_or_raise(
        self,
        *,
        decision_context: DecisionContext,
        strategy_template: StrategyTemplate,
    ) -> CryptoAgentsDecision:
        try:
            portfolio_output = PortfolioManagerOutput.model_validate(self._runner.run(decision_context))
        except ValidationError as exc:
            raise CryptoAgentsOutputParseError(str(exc)) from exc

        self._assert_context_alignment(decision_context=decision_context, portfolio_output=portfolio_output)

        strategy_intent_id = f"si-{decision_context.context_id}"
        trade_intent_id = f"ti-{decision_context.context_id}"

        strategy_intent = StrategyIntent(
            strategy_intent_id=strategy_intent_id,
            template_id=strategy_template.template_id,
            template_version=strategy_template.version,
            execution_mode="conditional",
            projected_daily_trade_count=portfolio_output.projected_daily_trade_count,
        )
        trade_intent = TradeIntent(
            trade_intent_id=trade_intent_id,
            strategy_intent_id=strategy_intent_id,
            pair=portfolio_output.pair,
            dex=portfolio_output.dex,
            position_usd=portfolio_output.position_usd,
            max_slippage_bps=portfolio_output.max_slippage_bps,
            stop_loss_bps=portfolio_output.stop_loss_bps,
            take_profit_bps=portfolio_output.take_profit_bps,
            entry_conditions=list(portfolio_output.entry_conditions),
            ttl_seconds=portfolio_output.ttl_seconds,
        )
        decision_meta = DecisionMeta(
            investment_thesis=portfolio_output.investment_thesis,
            confidence_score=portfolio_output.confidence_score,
        )
        agent_trace = AgentTrace(steps=portfolio_output.agent_trace_steps)
        return CryptoAgentsDecision(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            decision_meta=decision_meta,
            agent_trace=agent_trace,
        )

    @staticmethod
    def _assert_context_alignment(
        *,
        decision_context: DecisionContext,
        portfolio_output: PortfolioManagerOutput,
    ) -> None:
        constraints = decision_context.strategy_constraints
        if portfolio_output.pair != decision_context.strategy_constraints.pair:
            raise CryptoAgentsConstraintMismatchError("portfolio output pair must match decision_context.strategy_constraints.pair")
        if portfolio_output.dex != decision_context.strategy_constraints.dex:
            raise CryptoAgentsConstraintMismatchError("portfolio output dex must match decision_context.strategy_constraints.dex")
        if portfolio_output.position_usd > constraints.max_position_usd:
            raise CryptoAgentsConstraintMismatchError(
                "portfolio output position_usd exceeds decision_context.strategy_constraints.max_position_usd"
            )
        if portfolio_output.max_slippage_bps > constraints.max_slippage_bps:
            raise CryptoAgentsConstraintMismatchError(
                "portfolio output max_slippage_bps exceeds decision_context.strategy_constraints.max_slippage_bps"
            )
        if portfolio_output.stop_loss_bps > constraints.stop_loss_bps:
            raise CryptoAgentsConstraintMismatchError(
                "portfolio output stop_loss_bps exceeds decision_context.strategy_constraints.stop_loss_bps"
            )
        if portfolio_output.take_profit_bps > constraints.take_profit_bps:
            raise CryptoAgentsConstraintMismatchError(
                "portfolio output take_profit_bps exceeds decision_context.strategy_constraints.take_profit_bps"
            )
        if portfolio_output.ttl_seconds > constraints.ttl_seconds:
            raise CryptoAgentsConstraintMismatchError(
                "portfolio output ttl_seconds exceeds decision_context.strategy_constraints.ttl_seconds"
            )
        for item in portfolio_output.entry_conditions:
            text = item.strip().lower()
            if ":" not in text:
                raise CryptoAgentsConstraintMismatchError(
                    "portfolio output entry_conditions must use conditional expression format"
                )
            left, right = text.split(":", maxsplit=1)
            if not left or not right:
                raise CryptoAgentsConstraintMismatchError(
                    "portfolio output entry_conditions must use non-empty conditional expression format"
                )
            if any(token in text for token in ("buy_now", "sell_now", "market", "immediate")):
                raise CryptoAgentsConstraintMismatchError(
                    "portfolio output entry_conditions must not contain market-order style semantics"
                )


__all__ = [
    "CryptoAgentsAdapter",
    "CryptoAgentsAdapterError",
    "CryptoAgentsConstraintMismatchError",
    "CryptoAgentsOutputParseError",
    "CryptoAgentsRunnerPort",
]
