from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True)


class ShadowMonitorError(Exception):
    """Base error for shadow monitor domain failures."""


class MissingShadowMonitorSpecError(ShadowMonitorError):
    """Raised when required monitoring contract details are missing."""


class AlertSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class PositionState(str, Enum):
    ACTIVE_POSITION = "ActivePosition"
    CLOSED = "Closed"


class BreachOperator(str, Enum):
    LTE = "lte"
    GTE = "gte"


class BreachRule(BaseModel):
    model_config = _frozen_config()

    rule_id: str = Field(min_length=1)
    threshold_price: Decimal = Field(gt=0)
    operator: BreachOperator
    reason_code: str = Field(min_length=1)


class ActivePositionIntent(BaseModel):
    model_config = _frozen_config()

    intent_id: str = Field(min_length=1)
    trade_intent_id: str | None = Field(default=None, min_length=1)
    position_state: PositionState
    quantity: Decimal = Field(gt=0)
    breach_rules: list[BreachRule] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_active_position_state(self) -> "ActivePositionIntent":
        if self.position_state is not PositionState.ACTIVE_POSITION:
            raise ValueError("shadow_monitor only accepts ActivePosition intents")
        return self


class BackupRPCSnapshot(BaseModel):
    model_config = _frozen_config()

    intent_id: str = Field(min_length=1)
    position_state: PositionState
    mark_price: Decimal = Field(gt=0)
    observed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_observed_at_timezone(self) -> "BackupRPCSnapshot":
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        return self


class MonitorAlert(BaseModel):
    model_config = _frozen_config()

    code: str = Field(min_length=1)
    severity: AlertSeverity
    message: str = Field(min_length=1)
    source: str = Field(default="shadow_monitor", min_length=1)
    escalation_required: bool
    intent_id: str = Field(min_length=1)
    trade_intent_id: str | None = Field(default=None, min_length=1)
    breached_rule_id: str = Field(min_length=1)
    observed_price: Decimal = Field(gt=0)
    threshold_price: Decimal = Field(gt=0)
    grace_period_seconds: int = Field(ge=0)
    breach_duration_seconds: int = Field(ge=0)
    estimated_additional_loss_usd: Decimal = Field(ge=0)


class ForceCloseRecommendation(BaseModel):
    model_config = _frozen_config()

    action: str = Field(default="emergency_force_close", min_length=1)
    reason_code: str = Field(min_length=1)
    intent_id: str = Field(min_length=1)
    trade_intent_id: str | None = Field(default=None, min_length=1)
    breached_rule_id: str = Field(min_length=1)
    observed_price: Decimal = Field(gt=0)
    threshold_price: Decimal = Field(gt=0)
    estimated_additional_loss_usd: Decimal = Field(ge=0)
    escalation_required: bool = True


class ShadowMonitorResult(BaseModel):
    model_config = _frozen_config()

    checked_at: datetime
    alerts: list[MonitorAlert] = Field(default_factory=list)
    force_close_recommendations: list[ForceCloseRecommendation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_checked_at_timezone(self) -> "ShadowMonitorResult":
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("checked_at must be timezone-aware")
        return self


class ShadowMonitor:
    def __init__(
        self,
        *,
        grace_period_seconds: int,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if grace_period_seconds < 0:
            raise ValueError("grace_period_seconds must be >= 0")
        self._grace_period_seconds = grace_period_seconds
        self._clock = clock or _utc_now
        self._breach_started_at: dict[tuple[str, str], datetime] = {}

    @property
    def grace_period_seconds(self) -> int:
        return self._grace_period_seconds

    def reconcile_positions(
        self,
        *,
        active_positions: Sequence[ActivePositionIntent | dict[str, Any]],
        snapshots: Sequence[BackupRPCSnapshot | dict[str, Any]],
        checked_at: datetime | None = None,
    ) -> ShadowMonitorResult:
        now = checked_at or self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("checked_at must be timezone-aware")

        intents = [ActivePositionIntent.model_validate(item) for item in active_positions]
        snapshot_by_intent = self._index_snapshots(snapshots)

        alerts: list[MonitorAlert] = []
        recommendations: list[ForceCloseRecommendation] = []
        for intent in intents:
            snapshot = snapshot_by_intent.get(intent.intent_id)
            if snapshot is None:
                raise MissingShadowMonitorSpecError(
                    f"missing backup RPC snapshot for intent_id={intent.intent_id}"
                )
            position_alerts, position_recommendations = self._evaluate_position(
                intent=intent,
                snapshot=snapshot,
                checked_at=now,
            )
            alerts.extend(position_alerts)
            recommendations.extend(position_recommendations)

        return ShadowMonitorResult(
            checked_at=now,
            alerts=alerts,
            force_close_recommendations=recommendations,
        )

    def _index_snapshots(
        self,
        snapshots: Sequence[BackupRPCSnapshot | dict[str, Any]],
    ) -> dict[str, BackupRPCSnapshot]:
        indexed: dict[str, BackupRPCSnapshot] = {}
        for item in snapshots:
            snapshot = BackupRPCSnapshot.model_validate(item)
            if snapshot.intent_id in indexed:
                raise MissingShadowMonitorSpecError(
                    f"duplicate backup RPC snapshot for intent_id={snapshot.intent_id}"
                )
            indexed[snapshot.intent_id] = snapshot
        return indexed

    def _evaluate_position(
        self,
        *,
        intent: ActivePositionIntent,
        snapshot: BackupRPCSnapshot,
        checked_at: datetime,
    ) -> tuple[list[MonitorAlert], list[ForceCloseRecommendation]]:
        if snapshot.intent_id != intent.intent_id:
            raise MissingShadowMonitorSpecError(
                "backup RPC snapshot intent_id must match active position intent_id"
            )

        if snapshot.position_state is PositionState.CLOSED:
            self._clear_intent_breach_state(intent.intent_id)
            return [], []

        alerts: list[MonitorAlert] = []
        recommendations: list[ForceCloseRecommendation] = []

        for rule in intent.breach_rules:
            key = (intent.intent_id, rule.rule_id)
            if not _is_price_breached(
                observed_price=snapshot.mark_price,
                threshold_price=rule.threshold_price,
                operator=rule.operator,
            ):
                self._breach_started_at.pop(key, None)
                continue

            breach_started_at = self._breach_started_at.setdefault(key, checked_at)
            breach_duration_seconds = int((checked_at - breach_started_at).total_seconds())

            if breach_duration_seconds < self._grace_period_seconds:
                alerts.append(
                    MonitorAlert(
                        code="SHADOW_MONITOR_GRACE",
                        severity=AlertSeverity.WARNING,
                        message=(
                            "Threshold breached but still in grace period; waiting for normal callback to close."
                        ),
                        escalation_required=False,
                        intent_id=intent.intent_id,
                        trade_intent_id=intent.trade_intent_id,
                        breached_rule_id=rule.rule_id,
                        observed_price=snapshot.mark_price,
                        threshold_price=rule.threshold_price,
                        grace_period_seconds=self._grace_period_seconds,
                        breach_duration_seconds=breach_duration_seconds,
                        estimated_additional_loss_usd=Decimal("0"),
                    )
                )
                continue

            additional_loss = _estimate_additional_loss_usd(
                quantity=intent.quantity,
                observed_price=snapshot.mark_price,
                threshold_price=rule.threshold_price,
            )
            alerts.append(
                MonitorAlert(
                    code="SHADOW_MONITOR_CRITICAL_STALE_POSITION",
                    severity=AlertSeverity.CRITICAL,
                    message=(
                        "Threshold still breached after grace period and state has not closed; escalate for force-close."
                    ),
                    escalation_required=True,
                    intent_id=intent.intent_id,
                    trade_intent_id=intent.trade_intent_id,
                    breached_rule_id=rule.rule_id,
                    observed_price=snapshot.mark_price,
                    threshold_price=rule.threshold_price,
                    grace_period_seconds=self._grace_period_seconds,
                    breach_duration_seconds=breach_duration_seconds,
                    estimated_additional_loss_usd=additional_loss,
                )
            )
            recommendations.append(
                ForceCloseRecommendation(
                    reason_code=rule.reason_code,
                    intent_id=intent.intent_id,
                    trade_intent_id=intent.trade_intent_id,
                    breached_rule_id=rule.rule_id,
                    observed_price=snapshot.mark_price,
                    threshold_price=rule.threshold_price,
                    estimated_additional_loss_usd=additional_loss,
                )
            )

        return alerts, recommendations

    def _clear_intent_breach_state(self, intent_id: str) -> None:
        keys = [key for key in self._breach_started_at if key[0] == intent_id]
        for key in keys:
            self._breach_started_at.pop(key, None)


def _is_price_breached(
    *,
    observed_price: Decimal,
    threshold_price: Decimal,
    operator: BreachOperator,
) -> bool:
    if operator is BreachOperator.LTE:
        return observed_price <= threshold_price
    return observed_price >= threshold_price


def _estimate_additional_loss_usd(
    *,
    quantity: Decimal,
    observed_price: Decimal,
    threshold_price: Decimal,
) -> Decimal:
    # TODO: replace with strategy-side canonical risk formula once loss-estimation contract is frozen.
    return (quantity * (observed_price - threshold_price).copy_abs()).quantize(Decimal("0.00000001"))


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


__all__ = [
    "ActivePositionIntent",
    "AlertSeverity",
    "BackupRPCSnapshot",
    "BreachOperator",
    "BreachRule",
    "ForceCloseRecommendation",
    "MissingShadowMonitorSpecError",
    "MonitorAlert",
    "PositionState",
    "ShadowMonitor",
    "ShadowMonitorError",
    "ShadowMonitorResult",
]
