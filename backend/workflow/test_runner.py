from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
import sys

from backend.workflow import runner


class WorkflowRunnerTests(unittest.TestCase):
    def test_plan_includes_first_phase_and_module(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(["plan"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Data Foundation", output)
        self.assertIn("provider_architecture", output)
        self.assertIn("Senior Developer", output)
        self.assertIn("Code Reviewer", output)
        self.assertIn("Git Workflow Master", output)

    def test_dispatch_brief_includes_roles_and_test_target(self) -> None:
        brief = runner.build_dispatch_brief("decision_context_builder")

        self.assertIn("Data Engineer", brief)
        self.assertIn("Senior Developer", brief)
        self.assertIn("API Tester", brief)
        self.assertIn("Test Results Analyzer", brief)
        self.assertIn("Code Reviewer", brief)
        self.assertIn("Git Workflow Master", brief)
        self.assertIn("Senior Developer Gate", brief)
        self.assertIn("Code Reviewer Gate", brief)
        self.assertIn("Git Workflow Master Gate", brief)
        self.assertIn("backend/data/context_builder/test_context_builder.py", brief)

    def test_package_command_includes_required_sections(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(["package", "decision_context_builder"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("Task Package: DecisionContextBuilder", output)
        self.assertIn("**Module:** `decision_context_builder`", output)
        self.assertIn("**Title:** `DecisionContextBuilder`", output)
        self.assertIn("**Phase:** `Data Foundation`", output)
        self.assertIn("docs/knowledge/01_core/01_system_invariants.md", output)
        self.assertIn("backend/data/context_builder/", output)
        self.assertIn("Senior Developer", output)
        self.assertIn("Code Reviewer", output)
        self.assertIn("Git Workflow Master", output)
        self.assertIn("Senior Developer Gate", output)
        self.assertIn("Code Reviewer Gate", output)
        self.assertIn("Git Workflow Master Gate", output)
        self.assertIn("## Prompt Body", output)
        self.assertIn("You are a Codex subagent working on module `DecisionContextBuilder`", output)

    def test_task_card_command_renders_task_semantics(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(
                [
                    "task-card",
                    "decision_context_builder",
                    "--goal",
                    "Deliver a cleaner context builder boundary.",
                    "--acceptance",
                    "Preserve POSIX-style paths.",
                    "--acceptance",
                    "Keep module-local tests passing.",
                    "--non-goals",
                    "Do not change unrelated data fetchers.",
                    "--risks",
                    "Contract drift across downstream consumers.",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("## 1. 目标", output)
        self.assertIn("- Deliver a cleaner context builder boundary.", output)
        self.assertIn("- [ ] Preserve POSIX-style paths.", output)
        self.assertIn("- [ ] Keep module-local tests passing.", output)
        self.assertIn("- Do not change unrelated data fetchers.", output)
        self.assertIn("- Contract drift across downstream consumers.", output)
        self.assertIn("## 5. 文件范围", output)
        self.assertIn("backend/data/context_builder/", output)

    def test_draft_command_emits_contract_based_review_payload(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(["draft", "decision_context_builder"])

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("# Draft Summary", output)
        self.assertIn("# Full Draft", output)
        self.assertIn("DecisionContextBuilder", output)
        self.assertIn("统一输出完整 DecisionContext", output)
        self.assertIn("## 2. 验收标准", output)

    def test_build_task_draft_includes_summary_and_full_markdown(self) -> None:
        payload = runner.build_task_draft("decision_context_builder")

        self.assertEqual(payload["status"], "Draft")
        self.assertIn("goal", payload["summary"])
        self.assertGreaterEqual(len(payload["summary"]["acceptance_highlights"]), 1)
        self.assertIn("统一输出完整 DecisionContext", payload["markdown"])

    def test_draft_command_can_write_review_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft_path = Path(temp_dir) / "draft.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(
                    [
                        "draft",
                        "decision_context_builder",
                        "--instruction",
                        "Keep edits narrow.",
                        "--write",
                        str(draft_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(draft_path.exists())
            written = json.loads(draft_path.read_text(encoding="utf-8"))
            self.assertEqual(written["status"], "Draft")
            self.assertIn("summary", written)
            self.assertEqual(written["draft"]["instructions"], ["Keep edits narrow."])

    def test_split_command_recommends_single_module_for_specific_goal(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(
                [
                    "split",
                    "--goal",
                    "Improve provider architecture shared HTTP client and RPC provider fallback handling.",
                ]
            )

        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn("# Project Decomposition", output)
        self.assertIn("## Review Gate", output)
        self.assertIn("provider_architecture", output)
        self.assertIn("Direct module workflow", output)

        proposal = runner.build_project_decomposition(
            "Improve provider architecture shared HTTP client and RPC provider fallback handling."
        )
        self.assertEqual(proposal["status"], "Proposed")
        self.assertIn("role_outputs", proposal)
        self.assertIn("technical_writer", proposal["role_outputs"])
        self.assertIn("Technical Writer Synthesis", proposal["markdown"])
        self.assertEqual(proposal["recommended_mode"], "single-module")
        self.assertEqual(proposal["recommended_module"], "provider_architecture")

    def test_split_command_writes_project_decomposition_for_broad_goal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "decomposition.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(
                    [
                        "split",
                        "--goal",
                        "Build the full project workflow across data, decision, execution, runtime, and delivery.",
                        "--context",
                        "Need module boundaries and dependencies before coding.",
                        "--write",
                        str(proposal_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Project decomposition required", output)
            self.assertIn("## Review Gate", output)
            self.assertIn("## Technical Writer Synthesis", output)
            self.assertTrue(proposal_path.exists())
            written = json.loads(proposal_path.read_text(encoding="utf-8"))
            self.assertEqual(written["status"], "Proposed")
            self.assertIn("role_outputs", written)
            self.assertIn("technical_writer", written["role_outputs"])
            self.assertEqual(written["recommended_mode"], "project-decomposition")
            self.assertIn("summary", written)
            self.assertGreater(len(written["summary"]["top_candidate_ids"]), 0)

    def test_review_split_command_displays_proposal_without_editing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            runner.write_json_file(
                proposal_path,
                runner.build_project_decomposition(
                    "Build the full project workflow across data, decision, execution, runtime, and delivery."
                ),
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = runner.main(["review-split", "--from-split", str(proposal_path)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("# Project Decomposition", output)
            self.assertIn("## Review Gate", output)
            self.assertIn("## Technical Writer Synthesis", output)
            self.assertIn("Project decomposition required", output)
            self.assertEqual(
                json.loads(proposal_path.read_text(encoding="utf-8"))["status"],
                "Proposed",
            )

    def test_approve_split_command_emits_approved_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            proposal = runner.build_project_decomposition(
                "Build the full project workflow across data, decision, execution, runtime, and delivery."
            )
            runner.write_json_file(proposal_path, proposal)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(["approve-split", "--from-split", str(proposal_path)])

            self.assertEqual(exit_code, 0)
            approved = json.loads(buffer.getvalue())
            self.assertEqual(approved["status"], "Approved")
            self.assertEqual(approved["recommended_mode"], "project-decomposition")
            self.assertIn("summary", approved)
            self.assertIn("role_outputs", approved)
            self.assertIn("technical_writer", approved["role_outputs"])

    def test_approve_split_command_writes_default_approved_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            proposal = runner.build_project_decomposition(
                "Build the full project workflow across data, decision, execution, runtime, and delivery."
            )
            runner.write_json_file(proposal_path, proposal)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(["approve-split", "--from-split", str(proposal_path)])

            self.assertEqual(exit_code, 0)
            approved_path = proposal_path.with_name("proposal.approved.json")
            self.assertTrue(approved_path.exists())
            approved = json.loads(approved_path.read_text(encoding="utf-8"))
            self.assertEqual(approved["status"], "Approved")
            self.assertEqual(approved["recommended_mode"], "project-decomposition")

    def test_spawn_decomposition_command_rejects_unapproved_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            runner.write_json_file(
                proposal_path,
                runner.build_project_decomposition(
                    "Build the full project workflow across data, decision, execution, runtime, and delivery."
                ),
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = runner.main(["spawn-decomposition", "--from-split", str(proposal_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn("Project decomposition must be Approved", stderr.getvalue())

    def test_spawn_decomposition_command_emits_role_packets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            proposal = runner.build_project_decomposition(
                "Build the full project workflow across data, decision, execution, runtime, and delivery."
            )
            proposal["status"] = "Approved"
            runner.write_json_file(proposal_path, proposal)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(["spawn-decomposition", "--from-split", str(proposal_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["status"], "ReadyForSpawn")
            self.assertEqual(
                payload["spawn_order"],
                [
                    "Product Manager",
                    "Workflow Architect",
                    "Software Architect",
                    "Senior Project Manager",
                    "Technical Writer",
                ],
            )
            self.assertEqual(len(payload["spawn_groups"][0]["agents"]), 4)
            self.assertEqual(len(payload["spawn_groups"][1]["agents"]), 1)
            self.assertEqual(payload["spawn_groups"][1]["agents"][0]["role"], "Technical Writer")
            self.assertIn("spawn_agent", payload["spawn_groups"][0]["agents"][0])
            self.assertIn(
                "Approved decomposition proposal",
                payload["spawn_groups"][0]["agents"][0]["spawn_agent"]["items"][1]["text"],
            )
            self.assertEqual(
                payload["spawn_groups"][1]["agents"][0]["depends_on"],
                [
                    "Product Manager",
                    "Workflow Architect",
                    "Software Architect",
                    "Senior Project Manager",
                ],
            )

    def test_spawn_decomposition_command_can_emit_bundle_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            emit_dir = Path(temp_dir) / "bundle"
            proposal = runner.build_project_decomposition(
                "Build the full project workflow across data, decision, execution, runtime, and delivery."
            )
            proposal["status"] = "Approved"
            runner.write_json_file(proposal_path, proposal)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(
                    [
                        "spawn-decomposition",
                        "--from-split",
                        str(proposal_path),
                        "--emit-dir",
                        str(emit_dir),
                    ]
                )

            self.assertEqual(exit_code, 0)
            module_ids = runner._proposal_module_ids(proposal)
            first_module_id = module_ids[0]
            second_module_id = module_ids[1]
            self.assertTrue((emit_dir / "README.md").exists())
            self.assertTrue((emit_dir / "manifest.json").exists())
            self.assertTrue((emit_dir / "01-product-manager.json").exists())
            self.assertTrue((emit_dir / "05-technical-writer.json").exists())
            for index, module_id in enumerate(module_ids[:5], start=1):
                module_bundle_dir = emit_dir / "modules" / f"{index:02d}-{runner._role_slug(module_id)}"
                self.assertTrue((module_bundle_dir / "manifest.json").exists())
            self.assertTrue((emit_dir / "modules" / f"01-{runner._role_slug(first_module_id)}" / "draft.json").exists())
            self.assertTrue((emit_dir / "modules" / f"01-{runner._role_slug(first_module_id)}" / "review.md").exists())
            self.assertTrue((emit_dir / "modules" / f"01-{runner._role_slug(first_module_id)}" / "approved.json").exists())
            self.assertTrue((emit_dir / "modules" / f"01-{runner._role_slug(first_module_id)}" / "spawn.json").exists())
            self.assertTrue((emit_dir / "modules" / f"02-{runner._role_slug(second_module_id)}" / "manifest.json").exists())
            readme = (emit_dir / "README.md").read_text(encoding="utf-8")
            manifest = json.loads((emit_dir / "manifest.json").read_text(encoding="utf-8"))
            product_manager_packet = json.loads((emit_dir / "01-product-manager.json").read_text(encoding="utf-8"))
            module_manifest = json.loads(
                (emit_dir / "modules" / f"01-{runner._role_slug(first_module_id)}" / "manifest.json").read_text(encoding="utf-8")
            )
            module_spawn = json.loads(
                (emit_dir / "modules" / f"01-{runner._role_slug(first_module_id)}" / "spawn.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "ReadyForSpawn")
            self.assertIn("Codex-ready project decomposition spawn bundle", readme)
            self.assertIn("manifest.json", readme)
            self.assertIn("05-technical-writer.json", readme)
            self.assertIn("modules/", readme)
            self.assertEqual(product_manager_packet["role"], "Product Manager")
            self.assertEqual(product_manager_packet["group"], "review-pack")
            self.assertIn("spawn_agent", product_manager_packet)
            self.assertIn("Check whether the decomposition still reflects", product_manager_packet["spawn_agent"]["message"])
            self.assertEqual(module_manifest["status"], "ReadyForSpawn")
            self.assertEqual(module_manifest["module_id"], first_module_id)
            self.assertEqual(module_spawn["status"], "Approved")
            self.assertEqual(module_spawn["module_id"], first_module_id)
            self.assertEqual(module_spawn["task_card"]["status"], "Approved")

    def test_workflow_main_sets_utf8_stdio_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal_path = Path(temp_dir) / "proposal.json"
            proposal = runner.build_project_decomposition(
                "Build the full project workflow across data, decision, execution, runtime, and delivery."
            )
            proposal["status"] = "Approved"
            runner.write_json_file(proposal_path, proposal)

            env = os.environ.copy()
            env.pop("PYTHONIOENCODING", None)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.workflow.runner",
                    "spawn-decomposition",
                    "--from-split",
                    str(proposal_path),
                ],
                cwd=runner.REPO_ROOT,
                env=env,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            self.assertIn("ReadyForSpawn", result.stdout.decode("utf-8"))

    def test_approve_command_rejects_unapproved_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft_path = Path(temp_dir) / "draft.json"
            runner.write_json_file(draft_path, runner.build_task_draft("decision_context_builder"))

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = runner.main(["approve", "--from-draft", str(draft_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn("Draft must be marked Approved", stderr.getvalue())

    def test_approve_command_emits_spawn_payload_from_reviewed_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            draft_path = Path(temp_dir) / "draft.json"
            draft = runner.build_task_draft("decision_context_builder")
            draft["status"] = "Approved"
            runner.write_json_file(draft_path, draft)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = runner.main(["approve", "--from-draft", str(draft_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["status"], "Approved")
            self.assertEqual(payload["task_card"]["status"], "Approved")
        self.assertEqual(payload["task_card"]["goal"], draft["draft"]["goal"])
        self.assertIn("Use this task card as the source of truth", payload["prompt_body"])
        self.assertIn("Code Reviewer", payload["prompt_body"])
        self.assertIn("Git Workflow Master", payload["prompt_body"])

    def test_spawn_text_command_emits_json_payload(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(["spawn-text", "decision_context_builder"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["module_id"], "decision_context_builder")
        self.assertEqual(payload["title"], "DecisionContextBuilder")
        self.assertEqual(payload["phase"], "Data Foundation")
        self.assertEqual(payload["workflow_roles"]["senior_developer"], "Senior Developer")
        self.assertEqual(payload["workflow_roles"]["reviewer"], "Code Reviewer")
        self.assertEqual(payload["workflow_roles"]["git_master"], "Git Workflow Master")
        self.assertIn("docs/knowledge/01_core/01_system_invariants.md", payload["read_first"])
        self.assertIn("backend/data/context_builder/", payload["only_edit"])
        self.assertIn("python -m pytest backend/data/context_builder/test_context_builder.py -q", payload["suggested_checks"])
        self.assertIn("Code Reviewer Gate", payload["prompt"])
        self.assertIn("Git Workflow Master Gate", payload["prompt"])
        self.assertIn("Senior Developer Gate", payload["prompt"])
        self.assertIn("You are a Codex subagent working on module `DecisionContextBuilder`", payload["prompt"])

    def test_spawn_task_command_emits_task_package_payload(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = runner.main(
                [
                    "spawn-task",
                    "decision_context_builder",
                    "--goal",
                    "Deliver a cleaner context builder boundary.",
                    "--acceptance",
                    "Preserve POSIX-style paths.",
                    "--non-goals",
                    "Do not change unrelated data fetchers.",
                    "--risks",
                    "Contract drift across downstream consumers.",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertIn("module_package", payload)
        self.assertIn("task_card", payload)
        self.assertIn("prompt_body", payload)
        self.assertEqual(payload["module_package"]["module_id"], "decision_context_builder")
        self.assertEqual(payload["task_card"]["goal"], "Deliver a cleaner context builder boundary.")
        self.assertIn("Preserve POSIX-style paths.", payload["task_card"]["markdown"])
        self.assertIn("Use this task card as the source of truth", payload["prompt_body"])
        self.assertIn("Senior Developer", payload["prompt_body"])
        self.assertIn("Code Reviewer", payload["prompt_body"])
        self.assertIn("Git Workflow Master", payload["prompt_body"])
        self.assertIn("Preserve POSIX-style paths in any output or references.", payload["prompt_body"])

    def test_spawn_alias_matches_spawn_text(self) -> None:
        text_buffer = io.StringIO()
        alias_buffer = io.StringIO()
        with redirect_stdout(text_buffer):
            text_exit_code = runner.main(["spawn-text", "decision_context_builder"])
        with redirect_stdout(alias_buffer):
            alias_exit_code = runner.main(["spawn", "decision_context_builder"])

        self.assertEqual(text_exit_code, 0)
        self.assertEqual(alias_exit_code, 0)
        self.assertEqual(json.loads(text_buffer.getvalue()), json.loads(alias_buffer.getvalue()))

    def test_manifest_validation_passes(self) -> None:
        self.assertEqual(runner.validate_manifest(), [])

    def test_next_returns_ordered_module(self) -> None:
        self.assertEqual(runner.next_module("decision_context_builder"), "strategy_boundary_service")


if __name__ == "__main__":
    unittest.main()
