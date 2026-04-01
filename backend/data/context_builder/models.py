from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class MarketTrend(BaseModel):
    model_config = ConfigDict(frozen=True)

    direction: TrendDirection
    confidence_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    timeframe_minutes: int = Field(ge=1)
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class CapitalFlow(BaseModel):
    model_config = ConfigDict(frozen=True)

    net_inflow_usd: Decimal
    volume_24h_usd: Decimal
    whale_inflow_usd: Decimal
    retail_inflow_usd: Decimal
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class LiquidityDepth(BaseModel):
    model_config = ConfigDict(frozen=True)

    pair: str
    dex: str
    depth_usd_2pct: Decimal
    total_tvl_usd: Decimal
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class OnchainFlow(BaseModel):
    model_config = ConfigDict(frozen=True)

    active_address_delta_24h: int
    transaction_count_24h: int
    gas_price_gwei: Decimal = Field(ge=Decimal("0"))
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class RiskState(BaseModel):
    model_config = ConfigDict(frozen=True)

    volatility_annualized: Decimal = Field(ge=Decimal("0"))
    var_95_usd: Decimal
    correlation_to_market: Decimal = Field(ge=Decimal("-1"), le=Decimal("1"))
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class PositionState(BaseModel):
    model_config = ConfigDict(frozen=True)

    current_position_usd: Decimal = Field(default=Decimal("0"))
    unrealized_pnl_usd: Decimal = Field(default=Decimal("0"))
    entry_price_usd: Decimal | None = None
    position_opened_at: datetime | None = None
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ExecutionState(BaseModel):
    model_config = ConfigDict(frozen=True)

    daily_trades_executed: int = Field(ge=0, default=0)
    daily_volume_usd: Decimal = Field(default=Decimal("0"))
    last_execution_at: datetime | None = None
    aggregated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class StrategyConstraints(BaseModel):
    model_config = ConfigDict(frozen=True)

    pair: str
    dex: str
    max_position_usd: Decimal = Field(gt=Decimal("0"))
    max_slippage_bps: int = Field(ge=0)
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)
    ttl_seconds: int = Field(ge=1)
    daily_trade_limit: int = Field(ge=0)


class DecisionContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_trend: MarketTrend
    capital_flow: CapitalFlow
    liquidity_depth: LiquidityDepth
    onchain_flow: OnchainFlow
    risk_state: RiskState
    position_state: PositionState
    execution_state: ExecutionState
    strategy_constraints: StrategyConstraints
    context_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    sources: Mapping[str, str] = Field(default_factory=dict)

    @field_serializer("generated_at")
    def serialize_generated_at(self, value: datetime) -> str:
        return value.isoformat()
