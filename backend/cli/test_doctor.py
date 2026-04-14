from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from typer.testing import CliRunner

from backend.cli.app import CLISurfaceServices, create_cli_app, create_default_cli_app
from backend.cli.wiring import build_production_services, build_runtime_store_from_env


class CLIDoctorTests(unittest.TestCase):
    def _doctor_payload(
        self,
        *,
        env: dict[str, str],
        gate: str = "full",
        contract_gateway: object | None = None,
        use_default_call: bool = False,
    ) -> dict[str, object]:
        with patch.dict(os.environ, env, clear=True):
            services = build_production_services(
                contract_gateway=contract_gateway,
                runtime_store=build_runtime_store_from_env(),
            )
            if use_default_call:
                return json.loads(services.doctor_check())
            return json.loads(services.doctor_check(gate))

    def test_doctor_reports_blocked_when_runtime_env_is_missing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
            }
            payload = self._doctor_payload(env=env, use_default_call=True)

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["gate"], "full")
        self.assertEqual(payload["gate_status"], "blocked")
        self.assertEqual(payload["full_status"], "blocked")
        self.assertEqual(payload["status"], payload["full_status"])
        self.assertTrue(payload["db_exists"])
        self.assertIn("missing OPENAI_API_KEY", payload["blocked_reasons"])
        self.assertIn("missing OPENAI_BASE_URL", payload["blocked_reasons"])

    def test_doctor_blocks_local_proxy_in_production(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
                "REACTIVE_ENV": "production",
                "OPENAI_API_KEY": "test-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "HTTP_PROXY": "http://127.0.0.1:7890",
            }
            payload = self._doctor_payload(env=env)

        self.assertFalse(payload["proxy_policy_ok"])
        self.assertIn("HTTP_PROXY", payload["local_proxy_vars"])
        self.assertIn("local proxy is forbidden in production", " ".join(payload["blocked_reasons"]))

    def test_doctor_allows_local_proxy_outside_production(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
                "REACTIVE_ENV": "development",
                "OPENAI_API_KEY": "test-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "HTTP_PROXY": "http://127.0.0.1:7890",
            }
            with patch("backend.cli.wiring._probe_openai_connectivity", return_value=(True, None)):
                payload = self._doctor_payload(env=env)

        self.assertTrue(payload["proxy_policy_ok"])
        self.assertTrue(payload["decision_llm_ready"])
        self.assertTrue(payload["llm_connectivity_ok"])

    def test_doctor_gate_llm_ignores_chain_blockers(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
                "REACTIVE_ENV": "development",
                "OPENAI_API_KEY": "test-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
            }
            with patch("backend.cli.wiring._probe_openai_connectivity", return_value=(True, None)):
                payload = self._doctor_payload(env=env, gate="llm")

        self.assertEqual(payload["gate"], "llm")
        self.assertEqual(payload["gate_status"], "ok")
        self.assertEqual(payload["full_status"], "blocked")
        self.assertEqual(payload["status"], payload["full_status"])
        self.assertEqual(payload["blocked_reasons"], [])

    def test_doctor_gate_chain_ignores_llm_blockers(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            artifact_path = Path(tmp_dir) / "artifact.json"
            artifact_path.write_text("{}", encoding="utf-8")
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
                "SEPOLIA_RPC_URL": "http://127.0.0.1:8545",
                "SEPOLIA_PRIVATE_KEY": "0xabc",
                "REACTIVE_INVESTMENT_COMPILER_ADDRESS": "0xdef",
                "REACTIVE_INVESTMENT_COMPILER_ARTIFACT": str(artifact_path),
            }
            payload = self._doctor_payload(env=env, gate="chain", contract_gateway=object())

        self.assertEqual(payload["gate"], "chain")
        self.assertEqual(payload["gate_status"], "ok")
        self.assertEqual(payload["full_status"], "blocked")
        self.assertEqual(payload["status"], payload["full_status"])
        self.assertEqual(payload["blocked_reasons"], [])

    def test_doctor_gate_chain_does_not_probe_llm_connectivity(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            artifact_path = Path(tmp_dir) / "artifact.json"
            artifact_path.write_text("{}", encoding="utf-8")
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
                "SEPOLIA_RPC_URL": "http://127.0.0.1:8545",
                "SEPOLIA_PRIVATE_KEY": "0xabc",
                "REACTIVE_INVESTMENT_COMPILER_ADDRESS": "0xdef",
                "REACTIVE_INVESTMENT_COMPILER_ARTIFACT": str(artifact_path),
                "OPENAI_API_KEY": "test-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
            }
            with patch(
                "backend.cli.wiring._probe_openai_connectivity",
                side_effect=AssertionError("chain gate must not probe llm connectivity"),
            ):
                payload = self._doctor_payload(env=env, gate="chain", contract_gateway=object())

        self.assertEqual(payload["gate"], "chain")
        self.assertEqual(payload["gate_status"], "ok")

    def test_doctor_cli_accepts_gate_option(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
            }
            with patch.dict(os.environ, env, clear=True):
                app = create_default_cli_app()
                runner = CliRunner()
                result = runner.invoke(app, ["doctor", "--gate", "llm"])

        self.assertEqual(result.exit_code, 0, msg=result.stdout)

    def test_doctor_cli_gate_option_is_backward_compatible_with_zero_arg_handler(self) -> None:
        services = CLISurfaceServices(
            doctor_check=lambda: json.dumps(
                {
                    "status": "ok",
                    "gate": "full",
                    "gate_status": "ok",
                    "full_status": "ok",
                    "blocked_reasons": [],
                },
                ensure_ascii=False,
            )
        )
        app = create_cli_app(services=services)
        runner = CliRunner()
        result = runner.invoke(app, ["doctor", "--gate", "llm"])
        self.assertEqual(result.exit_code, 0, msg=result.stdout)

    def test_doctor_cli_gate_option_supports_keyword_only_gate_handler(self) -> None:
        calls: list[str] = []

        def doctor_check(*, gate: str = "full") -> str:
            calls.append(gate)
            return json.dumps(
                {
                    "status": "ok",
                    "gate": gate,
                    "gate_status": "ok",
                    "full_status": "ok",
                    "blocked_reasons": [],
                },
                ensure_ascii=False,
            )

        services = CLISurfaceServices(doctor_check=doctor_check)
        app = create_cli_app(services=services)
        runner = CliRunner()
        result = runner.invoke(app, ["doctor", "--gate", "llm"])
        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        self.assertEqual(calls, ["llm"])


if __name__ == "__main__":
    unittest.main()
