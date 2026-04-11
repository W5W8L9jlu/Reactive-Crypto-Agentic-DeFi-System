from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

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
            strategy_create=lambda: "strategy-create-ok",
            strategy_list=lambda: "strategy-route-ok",
            strategy_show=lambda strategy_id: f"strategy-show-ok:{strategy_id}",
            strategy_edit=lambda strategy_id: f"strategy-edit-ok:{strategy_id}",
            decision_run=lambda strategy_id: f"decision-route-ok:{strategy_id}",
            decision_dry_run=lambda strategy_id: f"decision-dry-run-ok:{strategy_id}",
            approval_list=lambda: "approval-list-ok",
            approval_show=lambda intent_id, raw, machine_truth_json: (
                (machine_truth_json if machine_truth_json is not None else f'{{"intent_id":"{intent_id}"}}')
                if raw
                else f"Approval Battle Card\nIntent: {intent_id}\nTTL Remaining: 5m 0s\nApprove: allowed"
            ),
            approval_approve=lambda intent_id: f"approved:{intent_id}",
            approval_reject=lambda intent_id, reason: f"rejected:{intent_id}:{reason}",
            execution_show=lambda intent_id: f"execution-show:{intent_id}",
            execution_logs=lambda intent_id: f"execution-logs:{intent_id}",
            execution_force_close=lambda intent_id: f"execution-force-close:{intent_id}",
            execution_fork_replay=(
                lambda intent_id, from_block, to_block: f"execution-fork-replay:{intent_id}:{from_block}:{to_block}"
            ),
            export_json=lambda intent_id: f'{{"intent_id":"{intent_id}"}}',
            export_markdown=lambda intent_id: f"# Audit Markdown Excerpt\nintent={intent_id}",
            export_memo=lambda intent_id: f"# Investment Memo\nintent={intent_id}",
            monitor_alerts=lambda critical_only: (
                [
                    AlertView(
                        code="SHADOW_MONITOR_CRITICAL_STALE_POSITION",
                        severity=AlertSeverity.CRITICAL,
                        message="threshold breached after grace period",
                        source="shadow-monitor",
                        escalation_required=True,
                        intent_id="intent-001",
                        observed_price="2910",
                        threshold_price="2950",
                        breach_blocks=4,
                        estimated_additional_loss_usd="40",
                        detected_at=datetime(2026, 4, 9, 10, 0, tzinfo=timezone.utc),
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
                        code="SHADOW_MONITOR_CRITICAL_STALE_POSITION",
                        severity=AlertSeverity.CRITICAL,
                        message="grace period exceeded",
                        source="shadow-monitor",
                        escalation_required=True,
                        intent_id="intent-001",
                        observed_price="2910",
                        threshold_price="2950",
                        breach_blocks=4,
                        estimated_additional_loss_usd="40",
                        detected_at=datetime(2026, 4, 9, 10, 0, tzinfo=timezone.utc),
                    ),
                ]
            ),
            monitor_shadow_status=lambda: "shadow-status-ok",
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
            (["strategy", "create"], "strategy-create-ok"),
            (["strategy", "list"], "strategy-route-ok"),
            (["strategy", "show", "strat-001"], "strategy-show-ok:strat-001"),
            (["strategy", "edit", "strat-001"], "strategy-edit-ok:strat-001"),
            (["decision", "run", "--strategy", "strat-001"], "decision-route-ok:strat-001"),
            (["decision", "dry-run", "--strategy", "strat-001"], "decision-dry-run-ok:strat-001"),
            (["approval", "list"], "approval-list-ok"),
            (["approval", "approve", "intent-001"], "approved:intent-001"),
            (
                ["approval", "reject", "intent-001", "--reason", "manual-stop"],
                "rejected:intent-001:manual-stop",
            ),
            (["execution", "show", "intent-001"], "execution-show:intent-001"),
            (["execution", "logs", "intent-001"], "execution-logs:intent-001"),
            (["execution", "force-close", "intent-001"], "execution-force-close:intent-001"),
            (
                ["execution", "fork-replay", "intent-001", "--from-block", "100", "--to-block", "120"],
                "execution-fork-replay:intent-001:100:120",
            ),
            (["export", "json", "intent-001"], '{"intent_id":"intent-001"}'),
            (["export", "markdown", "intent-001"], "# Audit Markdown Excerpt"),
            (["export", "memo", "intent-001"], "# Investment Memo"),
            (["monitor", "alerts", "--critical-only"], "SHADOW_MONITOR_CRITICAL_STALE_POSITION"),
            (["monitor", "shadow-status"], "shadow-status-ok"),
        ]
        for args, expected in checks:
            result = self.runner.invoke(self.app, args)
            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn(expected, result.stdout)

    def test_approval_show_supports_default_and_raw_mode(self) -> None:
        default_result = self.runner.invoke(self.app, ["approval", "show", "intent-001"])
        self.assertEqual(default_result.exit_code, 0)
        self.assertIn("Approval Battle Card", default_result.stdout)
        self.assertIn("TTL Remaining", default_result.stdout)

        raw_result = self.runner.invoke(
            self.app,
            ["approval", "show", "intent-001", "--raw", "--machine-truth-json", '{"id":"ti-001"}'],
        )
        self.assertEqual(raw_result.exit_code, 0)
        self.assertIn('{"id":"ti-001"}', raw_result.stdout)

    def test_approval_show_raw_works_without_machine_truth_override(self) -> None:
        result = self.runner.invoke(self.app, ["approval", "show", "intent-001", "--raw"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('{"intent_id":"intent-001"}', result.stdout)

    def test_monitor_alerts_renders_critical_force_close_banner(self) -> None:
        result = self.runner.invoke(self.app, ["monitor", "alerts", "--critical-only"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("CRITICAL ALERT", result.stdout)
        self.assertIn("agent-cli execution force-close intent-001", result.stdout)

    def test_valid_theme_from_env_keeps_route_output(self) -> None:
        with patch.dict(os.environ, {"REACTIVE_CLI_THEME": "minimal"}, clear=False):
            result = self.runner.invoke(self.app, ["strategy", "create"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Route: strategy.create", result.stdout)
        self.assertIn("strategy-create-ok", result.stdout)

    def test_invalid_theme_from_env_exits_with_code_2(self) -> None:
        with patch.dict(os.environ, {"REACTIVE_CLI_THEME": "invalid-theme"}, clear=False):
            result = self.runner.invoke(self.app, ["strategy", "create"])
        self.assertEqual(result.exit_code, 2)
        self.assertIn("REACTIVE_CLI_THEME", result.stdout)


if __name__ == "__main__":
    unittest.main()

