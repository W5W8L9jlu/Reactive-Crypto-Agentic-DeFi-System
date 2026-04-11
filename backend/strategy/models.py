from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, PositiveInt, model_validator


class BpsRange(BaseModel):
    min_bps: int = Field(ge=0)
    max_bps: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> "BpsRange":
        if self.min_bps > self.max_bps:
            raise ValueError("min_bps must be <= max_bps")
        return self

    def contains(self, value: int) -> bool:
        return self.min_bps <= value <= self.max_bps


class StrategyTemplate(BaseModel):
    template_id: str
    version: PositiveInt

    auto_allowed_pairs: frozenset[str] = Field(default_factory=frozenset)
    manual_allowed_pairs: frozenset[str] = Field(default_factory=frozenset)

    auto_allowed_dexes: frozenset[str] = Field(default_factory=frozenset)
    manual_allowed_dexes: frozenset[str] = Field(default_factory=frozenset)

    auto_max_position_usd: Decimal = Field(gt=0)
    hard_max_position_usd: Decimal = Field(gt=0)

    auto_max_slippage_bps: int = Field(ge=0)
    hard_max_slippage_bps: int = Field(ge=0)

    auto_stop_loss_bps_range: BpsRange
    manual_stop_loss_bps_range: BpsRange

    auto_take_profit_bps_range: BpsRange
    manual_take_profit_bps_range: BpsRange

    auto_daily_trade_limit: int = Field(ge=0)
    hard_daily_trade_limit: int = Field(ge=0)
    auto_max_daily_loss_pct_nav: Decimal = Field(ge=0, le=1, default=Decimal("0"))
    hard_max_daily_loss_pct_nav: Decimal = Field(ge=0, le=1, default=Decimal("0"))
    auto_max_consecutive_loss_count: int = Field(ge=0, default=0)
    hard_max_consecutive_loss_count: int = Field(ge=0, default=0)

    execution_mode: Literal["conditional"] = "conditional"

    @model_validator(mode="after")
    def validate_boundaries(self) -> "StrategyTemplate":
        if self.hard_max_position_usd < self.auto_max_position_usd:
            raise ValueError("hard_max_position_usd must be >= auto_max_position_usd")
        if self.hard_max_slippage_bps < self.auto_max_slippage_bps:
            raise ValueError("hard_max_slippage_bps must be >= auto_max_slippage_bps")
        if self.hard_daily_trade_limit < self.auto_daily_trade_limit:
            raise ValueError("hard_daily_trade_limit must be >= auto_daily_trade_limit")
        if self.hard_max_daily_loss_pct_nav < self.auto_max_daily_loss_pct_nav:
            raise ValueError("hard_max_daily_loss_pct_nav must be >= auto_max_daily_loss_pct_nav")
        if self.hard_max_consecutive_loss_count < self.auto_max_consecutive_loss_count:
            raise ValueError("hard_max_consecutive_loss_count must be >= auto_max_consecutive_loss_count")
        return self


class StrategyIntent(BaseModel):
    strategy_intent_id: str
    template_id: str
    template_version: PositiveInt
    execution_mode: Literal["conditional"] = "conditional"
    projected_daily_trade_count: int = Field(ge=0, default=0)
    projected_daily_loss_pct_nav: Decimal = Field(ge=0, le=1, default=Decimal("0"))
    projected_consecutive_loss_count: int = Field(ge=0, default=0)


class TradeIntent(BaseModel):
    trade_intent_id: str
    strategy_intent_id: str

    pair: str
    dex: str
    position_usd: Decimal = Field(gt=0)
    max_slippage_bps: int = Field(ge=0)
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)

    entry_conditions: list[str] = Field(min_length=1)
    ttl_seconds: PositiveInt


class BoundaryDecision(str, Enum):
    AUTO_REGISTER = "auto_register"
    MANUAL_APPROVAL = "manual_approval"
    REJECT = "reject"


class RuleDecision(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    REJECT = "reject"


class RuleEvaluationTrace(BaseModel):
    rule_name: str
    decision: RuleDecision
    observed: Any
    note: str


class ContractBindingHint(BaseModel):
    source_field: str
    target_field: str
    binding_kind: Literal["identity", "compiler_derived", "runtime_derived"]
    unit: Literal["identity", "usd_notional", "bps", "seconds"]
    owner: Literal["strategy_boundary_service", "validation_engine", "execution_compiler", "reactive_runtime"]
    note: str


class BoundaryDecisionResult(BaseModel):
    strategy_intent_id: str
    trade_intent_id: str
    template_id: str
    template_version: int
    boundary_decision: BoundaryDecision
    trace: list[RuleEvaluationTrace]
    contract_binding_hints: tuple[ContractBindingHint, ...] = ()
    decided_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
