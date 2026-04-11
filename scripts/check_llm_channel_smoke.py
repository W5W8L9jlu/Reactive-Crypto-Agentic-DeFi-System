from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from backend.cli.errors import RouteBindingMissingError
from backend.cli.wiring import (
    build_contract_gateway_from_runtime_env,
    build_production_services,
    build_runtime_store_from_env,
)


def _build_services(*, llm_only: bool):
    runtime_store = build_runtime_store_from_env()
    contract_gateway = None
    force_close_missing_reason = None
    decision_missing_reason = None
    if not llm_only:
        try:
            contract_gateway = build_contract_gateway_from_runtime_env()
        except RouteBindingMissingError as exc:
            force_close_missing_reason = str(exc)
            decision_missing_reason = str(exc)
    return build_production_services(
        contract_gateway=contract_gateway,
        runtime_store=runtime_store,
        force_close_missing_reason=force_close_missing_reason,
        decision_missing_reason=decision_missing_reason,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM channel smoke check based on CLI doctor contract.")
    parser.add_argument(
        "--llm-only",
        action="store_true",
        help="Only validate LLM config/proxy/connectivity contract.",
    )
    args = parser.parse_args()

    services = _build_services(llm_only=args.llm_only)
    payload = json.loads(services.doctor_check())
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.llm_only:
        passed = bool(
            payload.get("proxy_policy_ok")
            and payload.get("decision_llm_ready")
            and payload.get("llm_connectivity_ok")
        )
    else:
        passed = payload.get("status") == "ok"
    if passed:
        print("llm_smoke: OK")
        return 0
    print("llm_smoke: BLOCKED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
