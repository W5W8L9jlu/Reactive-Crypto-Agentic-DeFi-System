from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parent
scripts_dir_str = str(SCRIPTS_DIR)
if scripts_dir_str not in sys.path:
    sys.path.insert(0, scripts_dir_str)

import check_llm_channel_smoke as llm_smoke
import run_phase1_regression as phase1_regression


class _FakeDoctorServices:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.calls: list[str] = []

    def doctor_check(self, gate: str = "full") -> str:
        self.calls.append(gate)
        return json.dumps(self._payload, ensure_ascii=False)


class CheckLLMChannelSmokeTests(unittest.TestCase):
    def test_llm_only_uses_llm_gate_and_passes_by_gate_status(self) -> None:
        services = _FakeDoctorServices(
            {
                "gate_status": "ok",
                "full_status": "blocked",
                "status": "blocked",
            }
        )
        with patch.object(sys, "argv", ["check_llm_channel_smoke.py", "--llm-only"]):
            with patch.object(llm_smoke, "_build_services", return_value=services):
                with redirect_stdout(io.StringIO()):
                    exit_code = llm_smoke.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(services.calls, ["llm"])

    def test_full_flag_uses_full_gate(self) -> None:
        services = _FakeDoctorServices(
            {
                "gate_status": "ok",
                "full_status": "ok",
                "status": "ok",
            }
        )
        with patch.object(sys, "argv", ["check_llm_channel_smoke.py", "--full"]):
            with patch.object(llm_smoke, "_build_services", return_value=services):
                with redirect_stdout(io.StringIO()):
                    exit_code = llm_smoke.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(services.calls, ["full"])

    def test_full_flag_returns_nonzero_when_gate_blocked(self) -> None:
        services = _FakeDoctorServices(
            {
                "gate_status": "blocked",
                "full_status": "blocked",
                "status": "blocked",
            }
        )
        with patch.object(sys, "argv", ["check_llm_channel_smoke.py", "--full"]):
            with patch.object(llm_smoke, "_build_services", return_value=services):
                with redirect_stdout(io.StringIO()):
                    exit_code = llm_smoke.main()

        self.assertEqual(exit_code, 1)
        self.assertEqual(services.calls, ["full"])

    def test_default_behavior_keeps_full_gate(self) -> None:
        services = _FakeDoctorServices(
            {
                "gate_status": "ok",
                "full_status": "ok",
                "status": "ok",
            }
        )
        with patch.object(sys, "argv", ["check_llm_channel_smoke.py"]):
            with patch.object(llm_smoke, "_build_services", return_value=services):
                with redirect_stdout(io.StringIO()):
                    exit_code = llm_smoke.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(services.calls, ["full"])


class RunPhase1RegressionTests(unittest.TestCase):
    def test_with_llm_and_chain_calls_smoke_full(self) -> None:
        commands: list[list[str]] = []
        with patch.object(sys, "argv", ["run_phase1_regression.py", "--with-llm", "--with-chain"]):
            with patch.object(phase1_regression, "_run", side_effect=lambda command, cwd: commands.append(command)):
                exit_code = phase1_regression.main()

        self.assertEqual(exit_code, 0)
        self.assertIn(
            [sys.executable, "scripts/check_llm_channel_smoke.py", "--full"],
            commands,
        )

    def test_with_llm_only_calls_smoke_llm_only(self) -> None:
        commands: list[list[str]] = []
        with patch.object(sys, "argv", ["run_phase1_regression.py", "--with-llm"]):
            with patch.object(phase1_regression, "_run", side_effect=lambda command, cwd: commands.append(command)):
                exit_code = phase1_regression.main()

        self.assertEqual(exit_code, 0)
        self.assertIn(
            [sys.executable, "scripts/check_llm_channel_smoke.py", "--llm-only"],
            commands,
        )
        self.assertNotIn(
            [sys.executable, "scripts/check_llm_channel_smoke.py", "--full"],
            commands,
        )


if __name__ == "__main__":
    unittest.main()
