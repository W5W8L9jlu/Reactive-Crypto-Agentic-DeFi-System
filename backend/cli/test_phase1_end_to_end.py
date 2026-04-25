from __future__ import annotations

import json
import unittest

from typer.testing import CliRunner

from backend.cli.app import CLISurfaceServices, create_cli_app


class Phase1EndToEndCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.app = create_cli_app(services=self._build_services())

    @staticmethod
    def _build_services() -> CLISurfaceServices:
        def approval_show(intent_id: str, raw: bool, machine_truth_json: str | None) -> str:
            if raw:
                return machine_truth_json or json.dumps(
                    {
                        "intent_id": intent_id,
                        "approval_status": "approved",
                        "decision": "approve",
                    },
                    ensure_ascii=False,
                )
            return (
                "Approval Battle Card\n"
                f"Intent: {intent_id}\n"
                "Phase: phase1\n"
                "TTL Remaining: 5m 0s\n"
                "Approve: allowed"
            )

        return CLISurfaceServices(
            strategy_create=lambda: json.dumps(
                {
                    "strategy_id": "strat-phase1-001",
                    "template_id": "tpl-eth-swing",
                    "status": "created",
                },
                ensure_ascii=False,
            ),
            strategy_list=lambda: json.dumps(
                [
                    {
                        "strategy_id": "strat-phase1-001",
                        "template_id": "tpl-eth-swing",
                        "status": "created",
                    }
                ],
                ensure_ascii=False,
            ),
            strategy_show=lambda strategy_id: json.dumps(
                {"strategy_id": strategy_id, "status": "created"},
                ensure_ascii=False,
            ),
            strategy_edit=lambda strategy_id: json.dumps(
                {"strategy_id": strategy_id, "status": "updated"},
                ensure_ascii=False,
            ),
            decision_run=lambda strategy_id: json.dumps(
                {
                    "strategy_id": strategy_id,
                    "intent_id": "intent-phase1-001",
                    "approval_status": "pending",
                    "execution_plan": {"route": "phase1"},
                },
                ensure_ascii=False,
            ),
            decision_dry_run=lambda strategy_id: json.dumps(
                {
                    "strategy_id": strategy_id,
                    "intent_id": "intent-phase1-001",
                    "status": "dry_run",
                    "validation_result": {"is_valid": True, "issues": []},
                },
                ensure_ascii=False,
            ),
            approval_list=lambda: json.dumps(
                [
                    {
                        "intent_id": "intent-phase1-001",
                        "approval_status": "pending",
                        "phase": "phase1",
                    }
                ],
                ensure_ascii=False,
            ),
            approval_show=approval_show,
            approval_approve=lambda intent_id: json.dumps(
                {"intent_id": intent_id, "status": "approved"},
                ensure_ascii=False,
            ),
            approval_reject=lambda intent_id, reason: json.dumps(
                {"intent_id": intent_id, "status": "rejected", "reason": reason},
                ensure_ascii=False,
            ),
            execution_show=lambda intent_id: json.dumps(
                {"intent_id": intent_id, "status": "pending"},
                ensure_ascii=False,
            ),
            execution_logs=lambda intent_id: json.dumps(
                {"intent_id": intent_id, "entries": []},
                ensure_ascii=False,
            ),
            execution_force_close=lambda intent_id: json.dumps(
                {
                    "intent_id": intent_id,
                    "status": "success",
                    "tx_hash": "0x" + "2" * 64,
                    "block_number": 1,
                },
                ensure_ascii=False,
            ),
            execution_fork_replay=lambda intent_id, from_block, to_block: json.dumps(
                {
                    "intent_id": intent_id,
                    "from_block": from_block,
                    "to_block": to_block,
                },
                ensure_ascii=False,
            ),
            export_json=lambda intent_id: json.dumps(
                {
                    "intent_id": intent_id,
                    "decision_artifact": {"x": 1},
                    "execution_record": {"y": 2},
                },
                ensure_ascii=False,
            ),
            export_markdown=lambda intent_id: f"# Phase 1 Audit\nintent={intent_id}",
            export_memo=lambda intent_id: f"# Phase 1 Memo\nintent={intent_id}",
            monitor_alerts=lambda critical_only: [],
            monitor_shadow_status=lambda: json.dumps(
                {"status": "healthy", "tracked_intents": 1, "critical_alerts": 0},
                ensure_ascii=False,
            ),
            doctor_check=lambda gate: json.dumps({"gate": gate, "status": "ok"}, ensure_ascii=False),
        )

    def test_phase1_main_user_path_surfaces_structured_outputs(self) -> None:
        commands = [
            (["strategy", "create"], ["Route: strategy.create", '"strategy_id": "strat-phase1-001"', '"status": "created"']),
            (["strategy", "list"], ["Route: strategy.list", '"strategy_id": "strat-phase1-001"']),
            (
                ["decision", "dry-run", "--strategy", "strat-phase1-001"],
                [
                    "Route: decision.dry-run",
                    '"intent_id": "intent-phase1-001"',
                    '"status": "dry_run"',
                    '"is_valid": true',
                ],
            ),
            (
                ["decision", "run", "--strategy", "strat-phase1-001"],
                [
                    "Route: decision.run",
                    '"intent_id": "intent-phase1-001"',
                    '"approval_status": "pending"',
                    '"route": "phase1"',
                ],
            ),
            (["approval", "list"], ["Route: approval.list", '"intent_id": "intent-phase1-001"']),
            (
                ["approval", "show", "intent-phase1-001"],
                ["Route: approval.show", "Approval Battle Card", "Phase: phase1", "TTL Remaining: 5m 0s"],
            ),
            (
                ["approval", "show", "intent-phase1-001", "--raw", "--machine-truth-json", '{"decision":"approved"}'],
                ["Route: approval.show", '{"decision":"approved"}'],
            ),
            (
                ["approval", "approve", "intent-phase1-001"],
                ["Route: approval.approve", '"intent_id": "intent-phase1-001"', '"status": "approved"'],
            ),
            (
                ["execution", "show", "intent-phase1-001"],
                ["Route: execution.show", '"status": "pending"'],
            ),
            (
                ["execution", "force-close", "intent-phase1-001"],
                ["Route: execution.force-close", '"status": "success"', '"block_number": 1'],
            ),
            (
                ["export", "json", "intent-phase1-001"],
                ["Route: export.json", '"decision_artifact"', '"execution_record"'],
            ),
            (
                ["export", "markdown", "intent-phase1-001"],
                ["Route: export.markdown", "# Phase 1 Audit", "intent=intent-phase1-001"],
            ),
        ]

        for args, expected_snippets in commands:
            result = self.runner.invoke(self.app, args)
            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            for snippet in expected_snippets:
                self.assertIn(snippet, result.stdout)


if __name__ == "__main__":
    unittest.main()
