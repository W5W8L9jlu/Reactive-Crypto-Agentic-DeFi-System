from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict

from backend.cli.models import (
    ApprovalAction,
    ApprovalBattleCard,
    DecisionMeta,
    RiskLevel,
    bps_to_percent_str,
    format_decimal_short,
)
from backend.cli.views.approval_battle_card import render_approval_battle_card
from backend.execution.compiler.models import RegisterPayload
from backend.strategy.models import TradeIntent
from backend.validation.models import ExecutionPlan, ValidationResult

from .errors import ApprovalBlockedError, ApprovalExpiredError, MissingMachineTruthError


class ApprovalResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: ApprovalAction
    trade_intent_id: str
    reason: str
    decided_at: datetime


class ApprovalApprovedResult(ApprovalResult):
    action: Literal[ApprovalAction.APPROVE] = ApprovalAction.APPROVE


class ApprovalRejectedResult(ApprovalResult):
    action: Literal[ApprovalAction.REJECT] = ApprovalAction.REJECT


def build_approval_battle_card(
    *,
    trade_intent: TradeIntent,
    execution_plan: ExecutionPlan,
    validation_result: ValidationResult,
    decision_meta: DecisionMeta,
    now: datetime | None = None,
) -> ApprovalBattleCard:
    reference_time = now or datetime.now(tz=timezone.utc)
    register_payload = execution_plan.register_payload
    risk_level, risk_notes = _derive_risk_level(
        trade_intent=trade_intent,
        validation_result=validation_result,
    )
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
        entry_valid_until=_entry_valid_until(register_payload),
        max_gas_price_gwei=register_payload.max_gas_price_gwei,
        entry_amount_out_minimum=str(register_payload.entry_amount_out_minimum),
        is_valid=validation_result.is_valid,
        validation_summary=_validation_summary(validation_result),
        decision_meta=decision_meta,
        ttl_remaining_display=ttl_display,
        is_expired=is_expired,
        risk_level=risk_level,
        risk_notes=risk_notes,
        machine_truth_ref=f"mt:{trade_intent.trade_intent_id}",
    )


def show_approval(
    *,
    trade_intent: TradeIntent,
    execution_plan: ExecutionPlan,
    validation_result: ValidationResult,
    decision_meta: DecisionMeta,
    machine_truth_json: str | None = None,
    raw: bool = False,
    now: datetime | None = None,
) -> str:
    if raw:
        if machine_truth_json is None:
            raise MissingMachineTruthError("raw approval output requires machine truth JSON")
        return machine_truth_json

    card = build_approval_battle_card(
        trade_intent=trade_intent,
        execution_plan=execution_plan,
        validation_result=validation_result,
        decision_meta=decision_meta,
        now=now,
    )
    return render_approval_battle_card(card)


def approve_intent(
    *,
    trade_intent: TradeIntent,
    execution_plan: ExecutionPlan,
    validation_result: ValidationResult,
    decision_meta: DecisionMeta,
    now: datetime | None = None,
) -> ApprovalApprovedResult:
    reference_time = now or datetime.now(tz=timezone.utc)
    card = build_approval_battle_card(
        trade_intent=trade_intent,
        execution_plan=execution_plan,
        validation_result=validation_result,
        decision_meta=decision_meta,
        now=reference_time,
    )
    allowed, reason = card.can_approve()
    if allowed:
        return ApprovalApprovedResult(
            trade_intent_id=trade_intent.trade_intent_id,
            reason="approved by operator",
            decided_at=reference_time,
        )

    if card.is_expired:
        raise ApprovalExpiredError(reason)

    raise ApprovalBlockedError(reason)


def reject_intent(
    *,
    trade_intent: TradeIntent,
    decision_meta: DecisionMeta,
    reason: str,
    now: datetime | None = None,
) -> ApprovalRejectedResult:
    reference_time = now or datetime.now(tz=timezone.utc)
    return ApprovalRejectedResult(
        trade_intent_id=trade_intent.trade_intent_id,
        reason=reason,
        decided_at=reference_time,
    )


def _entry_valid_until(register_payload: RegisterPayload) -> datetime:
    return datetime.fromtimestamp(register_payload.entry_valid_until, tz=timezone.utc)


def _validation_summary(validation_result: ValidationResult) -> str:
    if validation_result.is_valid:
        return "pass"
    issue_count = len(validation_result.issues)
    if issue_count == 0:
        return "fail: validation failed without issue details"
    return f"fail: {issue_count} issue(s)"


def _derive_risk_level(
    *,
    trade_intent: TradeIntent,
    validation_result: ValidationResult,
) -> tuple[RiskLevel, list[str]]:
    risk_notes: list[str] = []
    risk_level = RiskLevel.LOW

    if trade_intent.stop_loss_bps > 500:
        risk_notes.append("wide stop loss")
        risk_level = RiskLevel.MEDIUM

    if trade_intent.take_profit_bps > 1000 and risk_level == RiskLevel.LOW:
        risk_notes.append("distant take profit target")
        risk_level = RiskLevel.MEDIUM

    if trade_intent.max_slippage_bps > 100:
        risk_notes.append("high slippage tolerance")
        risk_level = RiskLevel.HIGH

    if not validation_result.is_valid:
        risk_level = RiskLevel.HIGH
        risk_notes.extend(issue.message for issue in validation_result.issues)

    return risk_level, risk_notes
