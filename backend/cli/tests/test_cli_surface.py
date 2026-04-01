from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli.app import COMMAND_GROUPS, ExportArtifactKind, resolve_route
from cli.alerts import MonitorAlertSeverity, MonitorAlertView
from cli.errors import UnresolvedCliRouteError
from cli.models import ApprovalBattleCard, DecisionMeta, RiskLevel
from cli.views import render_approval_battle_card_text, render_monitor_alerts_text


def _battle_card() -> ApprovalBattleCard:
    return ApprovalBattleCard(
        trade_intent_id="ti_001",
        strategy_intent_id="si_001",
        pair="ETH/USDC",
        dex="uniswap-v3",
        position_usd=Decimal("1250"),
        position_usd_display="$1250.00",
        max_slippage_bps=50,
        max_slippage_display="0.5%",
        stop_loss_bps=200,
        stop_loss_display="2.0%",
        take_profit_bps=500,
        take_profit_display="5.0%",
        entry_valid_until=datetime(2026, 4, 1, 12, 5, tzinfo=timezone.utc),
        max_gas_price_gwei=35,
        entry_amount_out_minimum="1000000",
        is_valid=True,
        validation_summary="pass",
        decision_meta=DecisionMeta(
            trade_intent_id="ti_001",
            created_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
            ttl_seconds=180,
        ),
        ttl_remaining_display="2m 30s",
        is_expired=False,
        risk_level=RiskLevel.MEDIUM,
        risk_notes=["manual approval required"],
        machine_truth_ref="mt:ti_001",
    )


def test_command_surface_registers_all_required_groups() -> None:
    assert tuple(group.name for group in COMMAND_GROUPS) == (
        "strategy",
        "decision",
        "approval",
        "execution",
        "export",
        "monitor",
    )


def test_command_surface_resolves_minimum_entrypoints() -> None:
    expected_paths = (
        ("strategy", "show"),
        ("decision", "run"),
        ("approval", "show"),
        ("approval", "approve"),
        ("approval", "reject"),
        ("execution", "show"),
        ("export", "render"),
        ("monitor", "alerts"),
        ("monitor", "takeover"),
    )

    for path in expected_paths:
        route = resolve_route(path)
        assert route.group == path[0]
        assert route.name == path[1]


def test_unknown_route_raises_clear_domain_error() -> None:
    with pytest.raises(UnresolvedCliRouteError):
        resolve_route(("monitor", "unknown"))


def test_export_route_freezes_known_artifact_kinds() -> None:
    assert tuple(kind.value for kind in ExportArtifactKind) == (
        "machine_truth_json",
        "audit_markdown",
        "investment_memo",
    )


def test_render_approval_battle_card_hides_machine_truth_without_raw_flag() -> None:
    rendered = render_approval_battle_card_text(_battle_card(), show_raw=False)

    assert "ETH/USDC" in rendered
    assert "TTL" in rendered
    assert "2m 30s" in rendered
    assert "mt:ti_001" not in rendered


def test_render_approval_battle_card_exposes_machine_truth_reference_with_raw_flag() -> None:
    rendered = render_approval_battle_card_text(_battle_card(), show_raw=True)

    assert "mt:ti_001" in rendered
    assert "--raw" in rendered


def test_render_monitor_alert_view_shows_alert_state_and_manual_action() -> None:
    alert = MonitorAlertView(
        alert_id="alert_001",
        severity=MonitorAlertSeverity.CRITICAL,
        summary="shadow monitor grace period exceeded",
        source="shadow_monitor",
        grace_state="expired",
        requires_manual_action=True,
    )

    rendered = render_monitor_alerts_text([alert])

    assert "alert_001" in rendered
    assert "CRITICAL" in rendered
    assert "shadow monitor grace period exceeded" in rendered
    assert "manual action required" in rendered
