from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from backend.monitor.shadow_monitor import (
    AlertSeverity,
    ActivePositionIntent,
    BackupRPCSnapshot,
    BreachOperator,
    BreachRule,
    PositionState,
    ShadowMonitor,
)


class ShadowMonitorTestCase(unittest.TestCase):
    def test_breached_active_position_becomes_critical_after_grace_period(self) -> None:
        checked_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        monitor = ShadowMonitor(grace_period_seconds=30)

        active_position = ActivePositionIntent(
            intent_id="ap-001",
            trade_intent_id="ti-001",
            position_state=PositionState.ACTIVE_POSITION,
            quantity=Decimal("10"),
            breach_rules=[
                BreachRule(
                    rule_id="rule-001",
                    threshold_price=Decimal("100"),
                    operator=BreachOperator.LTE,
                    reason_code="POSITION_BREACH",
                )
            ],
        )
        breached_snapshot = BackupRPCSnapshot(
            intent_id="ap-001",
            position_state=PositionState.ACTIVE_POSITION,
            mark_price=Decimal("90"),
            observed_at=checked_at,
        )

        initial_result = monitor.reconcile_positions(
            active_positions=[active_position],
            snapshots=[breached_snapshot],
            checked_at=checked_at,
        )
        followup_result = monitor.reconcile_positions(
            active_positions=[active_position],
            snapshots=[breached_snapshot.model_copy(update={"observed_at": checked_at + timedelta(seconds=31)})],
            checked_at=checked_at + timedelta(seconds=31),
        )

        self.assertEqual(initial_result.alerts[0].severity, AlertSeverity.WARNING)
        self.assertEqual(followup_result.alerts[0].severity, AlertSeverity.CRITICAL)
        self.assertEqual(
            followup_result.alerts[0].code,
            "SHADOW_MONITOR_CRITICAL_STALE_POSITION",
        )
        self.assertTrue(followup_result.alerts[0].escalation_required)
        self.assertEqual(len(followup_result.force_close_recommendations), 1)
        recommendation = followup_result.force_close_recommendations[0]
        self.assertEqual(recommendation.action, "emergency_force_close")
        self.assertEqual(recommendation.reason_code, "POSITION_BREACH")
        self.assertEqual(recommendation.breached_rule_id, "rule-001")


if __name__ == "__main__":
    unittest.main()
