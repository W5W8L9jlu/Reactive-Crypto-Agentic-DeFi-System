from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from backend.strategy.models import StrategyIntent, TradeIntent


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True)


class AgentTraceStep(BaseModel):
    model_config = _frozen_config()

    agent: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    timestamp: datetime


class AgentTrace(BaseModel):
    model_config = _frozen_config()

    steps: tuple[AgentTraceStep, ...]


class PortfolioManagerOutput(BaseModel):
    model_config = _frozen_config()

    pair: str = Field(min_length=1)
    dex: str = Field(min_length=1)
    position_usd: Decimal = Field(gt=0)
    max_slippage_bps: int = Field(ge=0)
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)
    entry_conditions: tuple[str, ...] = Field(min_length=1)
    ttl_seconds: int = Field(ge=1)
    projected_daily_trade_count: int = Field(ge=0, default=0)
    investment_thesis: str = Field(min_length=1)
    confidence_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    agent_trace_steps: tuple[AgentTraceStep, ...] = Field(min_length=1)


class DecisionMeta(BaseModel):
    model_config = _frozen_config()

    investment_thesis: str = Field(min_length=1)
    confidence_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class CryptoAgentsDecision(BaseModel):
    model_config = _frozen_config()

    strategy_intent: StrategyIntent
    trade_intent: TradeIntent
    decision_meta: DecisionMeta
    agent_trace: AgentTrace


__all__ = [
    "AgentTrace",
    "AgentTraceStep",
    "CryptoAgentsDecision",
    "DecisionMeta",
    "PortfolioManagerOutput",
]
