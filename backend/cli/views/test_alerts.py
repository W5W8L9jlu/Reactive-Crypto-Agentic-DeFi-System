from __future__ import annotations

import unittest
from io import StringIO

from rich.console import Console

from backend.cli.views.alerts import AlertSeverity, AlertView, build_alerts_table, render_alerts_snapshot


class AlertViewRenderTests(unittest.TestCase):
    def test_render_alerts_snapshot_orders_critical_before_warning(self) -> None:
        alerts = [
            AlertView(
                code="WARN_LAG",
                severity=AlertSeverity.WARNING,
                message="lagging by 2 blocks",
                source="shadow-monitor",
                escalation_required=False,
            ),
            AlertView(
                code="CRIT_GRACE_TIMEOUT",
                severity=AlertSeverity.CRITICAL,
                message="grace period exceeded",
                source="shadow-monitor",
                escalation_required=True,
            ),
        ]

        rendered = render_alerts_snapshot(alerts)

        self.assertIn("[critical] CRIT_GRACE_TIMEOUT", rendered)
        self.assertIn("[warning] WARN_LAG", rendered)
        self.assertLess(rendered.index("CRIT_GRACE_TIMEOUT"), rendered.index("WARN_LAG"))

    def test_build_alerts_table_renders_empty_state(self) -> None:
        output = StringIO()
        console = Console(file=output, force_terminal=False, color_system=None, width=120)

        console.print(build_alerts_table([]))
        rendered = output.getvalue()

        self.assertIn("No active alerts", rendered)
        self.assertIn("Monitor Alerts", rendered)


if __name__ == "__main__":
    unittest.main()

