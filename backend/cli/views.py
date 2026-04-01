from __future__ import annotations

from collections.abc import Iterable

from .alerts import MonitorAlertView
from .models import ApprovalBattleCard


def render_approval_battle_card_text(
    card: ApprovalBattleCard,
    *,
    show_raw: bool = False,
) -> str:
    lines = [
        "Approval Battle Card",
        f"Trade Intent: {card.trade_intent_id}",
        f"Strategy Intent: {card.strategy_intent_id}",
        f"Pair: {card.pair}",
        f"DEX: {card.dex}",
        f"Position: {card.position_usd_display}",
        f"Validation: {card.validation_summary}",
        f"TTL: {card.ttl_remaining_display}",
        f"Risk: {card.risk_level.value}",
    ]

    if card.risk_notes:
        lines.append(f"Notes: {', '.join(card.risk_notes)}")

    can_approve, reason = card.can_approve()
    lines.append(f"Actionable: {'yes' if can_approve else 'no'}")
    if reason:
        lines.append(f"Blocker: {reason}")

    if show_raw:
        lines.append("--raw machine truth reference")
        lines.append(card.machine_truth_ref)
        lines.append("TODO: wire an explicit machine truth adapter before exposing payload.")

    return "\n".join(lines)


def render_monitor_alerts_text(alerts: Iterable[MonitorAlertView]) -> str:
    lines = ["Monitor Alerts"]

    for alert in alerts:
        lines.extend(
            [
                f"[{alert.severity.value.upper()}] {alert.alert_id}",
                f"Source: {alert.source}",
                f"Grace State: {alert.grace_state}",
                f"Summary: {alert.summary}",
                "Manual Action: manual action required"
                if alert.requires_manual_action
                else "Manual Action: optional",
            ]
        )

    return "\n".join(lines)
