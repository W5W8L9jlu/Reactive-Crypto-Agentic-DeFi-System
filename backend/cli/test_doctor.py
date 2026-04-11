from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from typer.testing import CliRunner

from backend.cli.app import create_default_cli_app


class CLIDoctorTests(unittest.TestCase):
    @staticmethod
    def _extract_payload(stdout: str) -> dict[str, object]:
        cleaned = stdout.replace("│", " ").replace("\n", " ")
        marker = cleaned.find("{")
        if marker == -1:
            raise AssertionError(stdout)
        return json.loads(cleaned[marker : cleaned.rfind("}") + 1])

    def test_doctor_reports_blocked_when_runtime_env_is_missing(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            env = {
                "REACTIVE_CLI_DB_PATH": str(Path(tmp_dir) / "cli_state.db"),
            }
            with patch.dict(os.environ, env, clear=True):
                app = create_default_cli_app()
                runner = CliRunner()
                result = runner.invoke(app, ["doctor"])

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        payload = self._extract_payload(result.stdout)
        self.assertEqual(payload["status"], "blocked")
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
            with patch.dict(os.environ, env, clear=True):
                app = create_default_cli_app()
                runner = CliRunner()
                result = runner.invoke(app, ["doctor"])

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        payload = self._extract_payload(result.stdout)
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
            with patch.dict(os.environ, env, clear=True):
                with patch("backend.cli.wiring._probe_openai_connectivity", return_value=(True, None)):
                    app = create_default_cli_app()
                    runner = CliRunner()
                    result = runner.invoke(app, ["doctor"])

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        payload = self._extract_payload(result.stdout)
        self.assertTrue(payload["proxy_policy_ok"])
        self.assertTrue(payload["decision_llm_ready"])
        self.assertTrue(payload["llm_connectivity_ok"])


if __name__ == "__main__":
    unittest.main()
