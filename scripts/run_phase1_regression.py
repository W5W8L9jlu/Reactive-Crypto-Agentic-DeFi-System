from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def _run(command: list[str], *, cwd: Path) -> None:
    rendered = " ".join(shlex.quote(part) for part in command)
    print(f"\n$ {rendered}")
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase-1 regression checks.")
    parser.add_argument(
        "--with-chain",
        action="store_true",
        help="Include anvil/web3 integration checks.",
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="Include LLM channel doctor-smoke check using current OPENAI/proxy env.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    python = sys.executable

    _run(
        [python, "-m", "unittest", "discover", "-s", "backend", "-p", "test*.py", "-v"],
        cwd=repo_root,
    )
    if args.with_chain:
        _run(
            [
                python,
                "-m",
                "pytest",
                "backend/execution/runtime/test_web3_contract_gateway_integration.py",
                "-q",
            ],
            cwd=repo_root,
        )
        _run(
            [python, "-m", "unittest", "backend.cli.test_force_close_integration", "-v"],
            cwd=repo_root,
        )
    if args.with_llm:
        _run(
            [python, "scripts/check_llm_channel_smoke.py", "--llm-only"],
            cwd=repo_root,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
