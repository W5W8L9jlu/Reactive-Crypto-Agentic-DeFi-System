from __future__ import annotations

import unittest

from typer.testing import CliRunner

from backend.cli.app import CLISurfaceServices, create_cli_app
from backend.cli.views.alerts import AlertSeverity, AlertView


class CLISurfaceRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.app = create_cli_app(services=self._build_services())

    @staticmethod
    def _build_services() -> CLISurfaceServices:
        return CLISurfaceServices(
            strategy_list=lambda: "strategy-route-ok",
            decision_run=lambda context_id: f"decision-route-ok:{context_id}",
            approval_show=lambda raw, machine_truth_json: (
                machine_truth_json
                if raw
                else "Approval Battle Card\nTTL Remaining: 5m 0s\nApprove: allowed"
            ),
            approval_approve=lambda trade_intent_id: f"approved:{trade_intent_id}",
            approval_reject=lambda trade_intent_id, reason: f"rejected:{trade_intent_id}:{reason}",
            execution_status=lambda trade_intent_id: f"execution-status:{trade_intent_id}",
            export_bundle=lambda trade_intent_id: f"export-bundle:{trade_intent_id}",
            monitor_alerts=lambda critical_only: (
                [
                    AlertView(
                        code="CRIT_GRACE_TIMEOUT",
                        severity=AlertSeverity.CRITICAL,
                        message="grace period exceeded",
                        source="shadow-monitor",
                        escalation_required=True,
                    )
                ]
                if critical_only
                else [
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
            ),
        )

    def test_help_contains_six_command_groups(self) -> None:
        result = self.runner.invoke(self.app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("strategy", result.stdout)
        self.assertIn("decision", result.stdout)
        self.assertIn("approval", result.stdout)
        self.assertIn("execution", result.stdout)
        self.assertIn("export", result.stdout)
        self.assertIn("monitor", result.stdout)

    def test_route_commands_are_wired(self) -> None:
        checks = [
            (["strategy", "list"], "strategy-route-ok"),
            (["decision", "run", "--context-id", "ctx-001"], "decision-route-ok:ctx-001"),
            (["approval", "approve", "--trade-intent-id", "ti-001"], "approved:ti-001"),
            (
                ["approval", "reject", "--trade-intent-id", "ti-001", "--reason", "manual-stop"],
                "rejected:ti-001:manual-stop",
            ),
            (["execution", "status", "--trade-intent-id", "ti-001"], "execution-status:ti-001"),
            (["export", "bundle", "--trade-intent-id", "ti-001"], "export-bundle:ti-001"),
            (["monitor", "alerts", "--critical-only"], "CRIT_GRACE_TIMEOUT"),
        ]
        for args, expected in checks:
            result = self.runner.invoke(self.app, args)
            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn(expected, result.stdout)

    def test_approval_show_supports_default_and_raw_mode(self) -> None:
        default_result = self.runner.invoke(self.app, ["approval", "show"])
        self.assertEqual(default_result.exit_code, 0)
        self.assertIn("Approval Battle Card", default_result.stdout)
        self.assertIn("TTL Remaining", default_result.stdout)

        raw_result = self.runner.invoke(
            self.app,
            ["approval", "show", "--raw", "--machine-truth-json", '{"id":"ti-001"}'],
        )
        self.assertEqual(raw_result.exit_code, 0)
        self.assertIn('{"id":"ti-001"}', raw_result.stdout)

    def test_approval_show_raw_requires_machine_truth_json(self) -> None:
        result = self.runner.invoke(self.app, ["approval", "show", "--raw"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("requires `--machine-truth-json`", result.stdout)


if __name__ == "__main__":
    unittest.main()

