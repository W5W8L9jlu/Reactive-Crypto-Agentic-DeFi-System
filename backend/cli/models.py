from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DecisionMeta(BaseModel):
    """Decision metadata used by CLI surfaces."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    trade_intent_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    ttl_seconds: int = Field(ge=1)
    ttl_source: str = Field(default="trade_intent.ttl_seconds")

    def is_expired(self, now: datetime | None = None) -> bool:
        reference_time = now or datetime.now(tz=timezone.utc)
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        return reference_time > expiry

    def remaining_seconds(self, now: datetime | None = None) -> int:
        reference_time = now or datetime.now(tz=timezone.utc)
        expiry = self.created_at + timedelta(seconds=self.ttl_seconds)
        remaining = int((expiry - reference_time).total_seconds())
        return max(0, remaining)

    def format_ttl(self, now: datetime | None = None) -> str:
        remaining = self.remaining_seconds(now)
        if remaining <= 0:
            return "expired"

        minutes, seconds = divmod(remaining, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"


class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalBattleCard(BaseModel):
    """Structured approval view object for the CLI surface."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    trade_intent_id: str
    strategy_intent_id: str
    pair: str
    dex: str

    position_usd: Decimal
    position_usd_display: str

    max_slippage_bps: int
    max_slippage_display: str
    stop_loss_bps: int
    stop_loss_display: str
    take_profit_bps: int
    take_profit_display: str

    entry_valid_until: datetime
    max_gas_price_gwei: int | None = None
    entry_amount_out_minimum: str | None = None

    is_valid: bool
    validation_summary: str

    decision_meta: DecisionMeta
    ttl_remaining_display: str
    is_expired: bool

    risk_level: RiskLevel
    risk_notes: list[str] = Field(default_factory=list)

    machine_truth_ref: str

    @model_validator(mode="after")
    def validate_expired_state(self) -> "ApprovalBattleCard":
        if self.is_expired and self.ttl_remaining_display != "expired":
            raise ValueError("Expired cards must render an expired TTL label.")
        return self

    def can_approve(self) -> tuple[bool, str]:
        if self.is_expired:
            return False, "intent expired; approval blocked"
        if not self.is_valid:
            return False, "validation failed; approval blocked"
        return True, ""


def bps_to_percent_str(bps: int) -> str:
    percent = bps / 100
    return f"{percent:.1f}%"


def format_decimal_short(value: Decimal, prefix: str = "$") -> str:
    if value >= 1000:
        return f"{prefix}{value / 1000:.1f}k"
    return f"{prefix}{value:.2f}"


def _risk_rank(level: RiskLevel) -> int:
    return {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
    }[level]


def build_approval_battle_card(
    *,
    trade_intent: Any,
    execution_plan: Any,
    validation_result: Any,
    decision_meta: DecisionMeta,
    now: datetime | None = None,
) -> ApprovalBattleCard:
    """Map structured upstream objects into an approval card."""

    reference_time = now or datetime.now(tz=timezone.utc)

    register_payload = execution_plan.register_payload
    entry_valid_until_ts = register_payload.get("entryValidUntil")
    if entry_valid_until_ts:
        entry_valid_until = datetime.fromtimestamp(entry_valid_until_ts, tz=timezone.utc)
    else:
        entry_valid_until = decision_meta.created_at + timedelta(seconds=decision_meta.ttl_seconds)

    issue_count = len(validation_result.issues)
    if validation_result.is_valid:
        validation_summary = "pass"
    elif issue_count == 0:
        validation_summary = "fail: validation failed without issue details"
    else:
        validation_summary = f"fail: {issue_count} issue(s)"

    risk_notes: list[str] = []
    risk_level = RiskLevel.LOW

    if trade_intent.stop_loss_bps > 500:
        risk_notes.append("wide stop loss")
        risk_level = RiskLevel.MEDIUM

    if trade_intent.take_profit_bps > 1000 and _risk_rank(risk_level) < _risk_rank(RiskLevel.MEDIUM):
        risk_notes.append("distant take profit target")
        risk_level = RiskLevel.MEDIUM

    if trade_intent.max_slippage_bps > 100:
        risk_notes.append("high slippage tolerance")
        risk_level = RiskLevel.HIGH

    is_expired = decision_meta.is_expired(reference_time)
    ttl_display = "expired" if is_expired else decision_meta.format_ttl(reference_time)

    return ApprovalBattleCard(
        trade_intent_id=trade_intent.trade_intent_id,
        strategy_intent_id=trade_intent.strategy_intent_id,
        pair=trade_intent.pair,
        dex=trade_intent.dex,
        position_usd=trade_intent.position_usd,
        position_usd_display=format_decimal_short(trade_intent.position_usd),
        max_slippage_bps=trade_intent.max_slippage_bps,
        max_slippage_display=bps_to_percent_str(trade_intent.max_slippage_bps),
        stop_loss_bps=trade_intent.stop_loss_bps,
        stop_loss_display=bps_to_percent_str(trade_intent.stop_loss_bps),
        take_profit_bps=trade_intent.take_profit_bps,
        take_profit_display=bps_to_percent_str(trade_intent.take_profit_bps),
        entry_valid_until=entry_valid_until,
        max_gas_price_gwei=register_payload.get("maxGasPriceGwei"),
        entry_amount_out_minimum=(
            str(register_payload["entryAmountOutMinimum"])
            if register_payload.get("entryAmountOutMinimum") is not None
            else None
        ),
        is_valid=validation_result.is_valid,
        validation_summary=validation_summary,
        decision_meta=decision_meta,
        ttl_remaining_display=ttl_display,
        is_expired=is_expired,
        risk_level=risk_level,
        risk_notes=risk_notes,
        machine_truth_ref=f"mt:{trade_intent.trade_intent_id}",
    )
