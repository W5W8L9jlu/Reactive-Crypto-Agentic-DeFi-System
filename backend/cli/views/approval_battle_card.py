from __future__ import annotations

from backend.cli.models import ApprovalBattleCard


def render_approval_battle_card(card: ApprovalBattleCard) -> str:
    approve_allowed, approve_reason = card.can_approve()
    approve_status = "allowed" if approve_allowed else f"blocked ({approve_reason})"

    lines = [
        "Approval Battle Card",
        f"Trade Intent: {card.trade_intent_id}",
        f"Strategy Intent: {card.strategy_intent_id}",
        f"Market: {card.pair} on {card.dex}",
        f"Position: {card.position_usd_display}",
        f"Max Slippage: {card.max_slippage_display}",
        f"Stop Loss: {card.stop_loss_display}",
        f"Take Profit: {card.take_profit_display}",
        f"Entry Valid Until: {card.entry_valid_until.isoformat()}",
        f"TTL Remaining: {card.ttl_remaining_display}",
        f"Validation: {card.validation_summary}",
        f"Risk Level: {card.risk_level.value}",
        f"Approve: {approve_status}",
        "Reject: allowed",
    ]

    if card.risk_notes:
        lines.append("Risk Notes:")
        lines.extend(f"- {note}" for note in card.risk_notes)
    else:
        lines.append("Risk Notes: none")

    return "\n".join(lines)
