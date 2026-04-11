from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from web3 import Web3

REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from backend.execution.compiler import (
    ChainStateSnapshot,
    CompilationContext,
    RegistrationContext,
    compile_execution_plan,
    freeze_contract_call_inputs,
)
from backend.execution.runtime import ContractGateway, Web3InvestmentCompilerClient
from backend.monitor.shadow_monitor import (
    ActivePositionIntent,
    BackupRPCSnapshot,
    BreachOperator,
    BreachRule,
    PositionState as ShadowPositionState,
    ShadowMonitor,
)
from backend.reactive.adapters.models import InvestmentPositionState, ReactiveTriggerType
from backend.strategy.models import BpsRange, StrategyIntent, StrategyTemplate, TradeIntent
from backend.strategy.models import BoundaryDecision
from backend.strategy.strategy_boundary_service import StrategyBoundaryService
from backend.validation import validate_inputs_or_raise
from backend.validation.models import ExecutionPlan as ValidationExecutionPlan
from backend.export.export_outputs import DecisionArtifact, ExecutionRecord, export_outputs


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required env: {name}")
    return value


def _resolve_rpc_url() -> str:
    return os.environ.get("SEPOLIA_RPC_URL") or _require_env("BASE_SEPOLIA_RPC_URL")


def _resolve_artifact_path() -> Path:
    raw = os.environ.get("REACTIVE_INVESTMENT_COMPILER_ARTIFACT")
    if raw:
        path = Path(raw)
    else:
        path = (
            REPO_ROOT
            / "backend"
            / "contracts"
            / "out"
            / "ReactiveInvestmentCompiler.sol"
            / "ReactiveInvestmentCompiler.json"
        )
    if not path.exists():
        raise RuntimeError(f"contract artifact not found: {path}")
    return path


def _build_strategy_template() -> StrategyTemplate:
    return StrategyTemplate(
        template_id="sepolia-smoke-template",
        version=1,
        auto_allowed_pairs=frozenset(),
        manual_allowed_pairs=frozenset({"ETH/USDC"}),
        auto_allowed_dexes=frozenset(),
        manual_allowed_dexes=frozenset({"uniswap_v3"}),
        auto_max_position_usd=Decimal("5000"),
        hard_max_position_usd=Decimal("10000"),
        auto_max_slippage_bps=30,
        hard_max_slippage_bps=80,
        auto_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=200),
        manual_stop_loss_bps_range=BpsRange(min_bps=10, max_bps=400),
        auto_take_profit_bps_range=BpsRange(min_bps=100, max_bps=500),
        manual_take_profit_bps_range=BpsRange(min_bps=50, max_bps=1000),
        auto_daily_trade_limit=2,
        hard_daily_trade_limit=8,
        auto_max_daily_loss_pct_nav=Decimal("0.03"),
        hard_max_daily_loss_pct_nav=Decimal("0.05"),
        auto_max_consecutive_loss_count=2,
        hard_max_consecutive_loss_count=3,
        execution_mode="conditional",
    )


def _to_json_ready(value):
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if isinstance(value, bytearray):
        return "0x" + bytes(value).hex()
    if isinstance(value, dict):
        return {str(k): _to_json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_ready(item) for item in value]
    return value


def run_smoke(*, include_force_close: bool) -> dict[str, object]:
    rpc_url = _resolve_rpc_url()
    private_key = _require_env("SEPOLIA_PRIVATE_KEY")
    contract_address = _require_env("REACTIVE_INVESTMENT_COMPILER_ADDRESS")
    artifact_path = _resolve_artifact_path()

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise RuntimeError(f"rpc not connected: {rpc_url}")
    if int(web3.eth.chain_id) != 11155111:
        raise RuntimeError(f"unexpected chain id: {web3.eth.chain_id}")

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    abi = artifact["abi"]
    account = web3.eth.account.from_key(private_key)
    sender = account.address
    contract = web3.eth.contract(address=contract_address, abi=abi)
    gateway = ContractGateway(
        client=Web3InvestmentCompilerClient(
            web3=web3,
            contract=contract,
            tx_sender=sender,
            private_key=private_key,
        )
    )

    now = datetime.now(tz=timezone.utc)
    suffix = now.strftime("%Y%m%d%H%M%S")
    strategy_intent_id = f"si-sepolia-{suffix}"
    trade_intent_id = f"ti-sepolia-{suffix}"
    intent_id = web3.keccak(text=f"{trade_intent_id}:{int(now.timestamp())}").hex()
    if not intent_id.startswith("0x"):
        intent_id = f"0x{intent_id}"

    strategy_template = _build_strategy_template()
    strategy_intent = StrategyIntent(
        strategy_intent_id=strategy_intent_id,
        template_id=strategy_template.template_id,
        template_version=1,
        execution_mode="conditional",
        projected_daily_trade_count=1,
        projected_daily_loss_pct_nav=Decimal("0.01"),
        projected_consecutive_loss_count=1,
    )
    trade_intent = TradeIntent(
        trade_intent_id=trade_intent_id,
        strategy_intent_id=strategy_intent_id,
        pair="ETH/USDC",
        dex="uniswap_v3",
        position_usd=Decimal("1200"),
        max_slippage_bps=20,
        stop_loss_bps=90,
        take_profit_bps=250,
        entry_conditions=["price_below:3000"],
        ttl_seconds=3600,
    )

    boundary_result = StrategyBoundaryService([strategy_template]).evaluate(strategy_intent, trade_intent)
    if boundary_result.boundary_decision is BoundaryDecision.REJECT:
        raise RuntimeError("dry-run rejected by strategy boundary")
    approval_action = "approved"
    if boundary_result.boundary_decision is BoundaryDecision.AUTO_REGISTER:
        approval_action = "not_required"

    validation_pre = validate_inputs_or_raise(
        strategy_template=strategy_template,
        strategy_intent=strategy_intent,
        trade_intent=trade_intent,
    )

    latest_block = web3.eth.get_block("latest")
    base_fee_wei = int(latest_block.get("baseFeePerGas", 0) or 0)
    base_fee_gwei = max(1, int(web3.from_wei(base_fee_wei, "gwei")))
    chain_state = ChainStateSnapshot(
        base_fee_gwei=base_fee_gwei,
        max_priority_fee_gwei=2,
        block_number=int(latest_block["number"]),
        block_timestamp=int(latest_block["timestamp"]),
        input_token_decimals=6,
        output_token_decimals=18,
        input_output_price=Decimal("0.0005"),
        input_token_usd_price=Decimal("1"),
    )
    registration_context = RegistrationContext(
        intent_id=intent_id,
        owner=sender,
        input_token="0x0000000000000000000000000000000000000001",
        output_token="0x0000000000000000000000000000000000000002",
    )
    execution_plan = compile_execution_plan(
        CompilationContext(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            chain_state=chain_state,
            registration_context=registration_context,
        )
    )
    validation_plan = ValidationExecutionPlan.model_validate(execution_plan.model_dump(mode="python", by_alias=True))
    validation_post = validate_inputs_or_raise(
        strategy_template=strategy_template,
        strategy_intent=strategy_intent,
        trade_intent=trade_intent,
        execution_plan=validation_plan,
    )

    call_inputs = freeze_contract_call_inputs(execution_plan)
    register_receipt = gateway.register_investment_intent(call_inputs=call_inputs)
    entry_receipt = gateway.execute_reactive_trigger(
        intent_id=call_inputs.intent_id,
        trigger_type=ReactiveTriggerType.ENTRY,
        observed_out=int(call_inputs.intent.entry_min_out),
    )
    register_receipt_safe = _to_json_ready(register_receipt)
    entry_receipt_safe = _to_json_ready(entry_receipt)
    entry_state = gateway.get_position_state(intent_id=call_inputs.intent_id)
    if entry_state is not InvestmentPositionState.ACTIVE_POSITION:
        raise RuntimeError(f"entry trigger failed to reach active position: {entry_state}")

    decision_artifact = DecisionArtifact.model_validate(
        {
            "strategy_intent": strategy_intent.model_dump(mode="python"),
            "trade_intent": trade_intent.model_dump(mode="python"),
            "boundary_result": boundary_result.model_dump(mode="python"),
            "validation_result_pre": validation_pre.model_dump(mode="python"),
            "validation_result_post": validation_post.model_dump(mode="python"),
            "register_receipt": register_receipt_safe,
            "entry_receipt": entry_receipt_safe,
        }
    )
    execution_record = ExecutionRecord.model_validate(
        {
            "status": "executed",
            "intent_id": call_inputs.intent_id,
            "register_tx_hash": register_receipt_safe["tx_hash"],
            "entry_tx_hash": entry_receipt_safe["tx_hash"],
            "register_block": register_receipt_safe["block_number"],
            "entry_block": entry_receipt_safe["block_number"],
            "execution_plan": execution_plan.model_dump(mode="python", by_alias=True),
            "contract_call_inputs": _to_json_ready(call_inputs.model_dump(mode="python", by_alias=True)),
        }
    )
    export_bundle = export_outputs(
        decision_artifact=decision_artifact,
        execution_record=execution_record,
        memo_brief="Sepolia smoke run for runtime execution and emergency control.",
    )

    monitor = ShadowMonitor(grace_period_seconds=0)
    monitor_result = monitor.reconcile_positions(
        active_positions=[
            ActivePositionIntent(
                intent_id=call_inputs.intent_id,
                trade_intent_id=trade_intent.trade_intent_id,
                position_state=ShadowPositionState.ACTIVE_POSITION,
                quantity=Decimal("1"),
                breach_rules=[
                    BreachRule(
                        rule_id="stop-loss",
                        threshold_price=Decimal("2950"),
                        operator=BreachOperator.LTE,
                        reason_code="STOP_LOSS_BREACH",
                    )
                ],
            )
        ],
        snapshots=[
            BackupRPCSnapshot(
                intent_id=call_inputs.intent_id,
                position_state=ShadowPositionState.ACTIVE_POSITION,
                mark_price=Decimal("2910"),
                observed_at=datetime.now(tz=timezone.utc),
            )
        ],
    )

    emergency_receipt: dict[str, object] | None = None
    final_state = entry_state
    if include_force_close:
        if not monitor_result.force_close_recommendations:
            raise RuntimeError("shadow monitor produced no force-close recommendation")
        emergency_receipt = gateway.emergency_force_close_from_recommendation(
            recommendation=monitor_result.force_close_recommendations[0].model_dump(mode="python"),
            max_slippage_bps=900,
        )
        emergency_receipt = _to_json_ready(emergency_receipt)
        final_state = gateway.get_position_state(intent_id=call_inputs.intent_id)
        if final_state is not InvestmentPositionState.CLOSED:
            raise RuntimeError(f"force-close failed to close position: {final_state}")

    output = {
        "network": "sepolia",
        "chain_id": int(web3.eth.chain_id),
        "account": sender,
        "contract_address": contract_address,
        "dry_run_boundary_decision": boundary_result.boundary_decision.value,
        "approval_action": approval_action,
        "intent_id": call_inputs.intent_id,
        "strategy_intent_id": strategy_intent_id,
        "trade_intent_id": trade_intent_id,
        "register_receipt": register_receipt_safe,
        "entry_receipt": entry_receipt_safe,
        "monitor_alert_count": len(monitor_result.alerts),
        "force_close_recommendation_count": len(monitor_result.force_close_recommendations),
        "emergency_receipt": emergency_receipt,
        "final_state": final_state.value,
        "machine_truth_json": export_bundle.machine_truth_json,
        "audit_markdown": export_bundle.audit_markdown,
        "investment_memo": export_bundle.investment_memo,
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sepolia smoke with real chain receipts.")
    parser.add_argument(
        "--skip-force-close",
        action="store_true",
        help="Skip the final emergency force-close step.",
    )
    args = parser.parse_args()

    output = run_smoke(include_force_close=not args.skip_force_close)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = REPO_ROOT / "docs" / "acceptance" / "threads" / "wave5" / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"sepolia_smoke_{ts}.json"
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"artifact: {out_file}")
    print(f"register_tx: {output['register_receipt']['tx_hash']}")
    print(f"entry_tx: {output['entry_receipt']['tx_hash']}")
    emergency = output.get("emergency_receipt")
    if isinstance(emergency, dict):
        print(f"force_close_tx: {emergency['tx_hash']}")
    print(f"final_state: {output['final_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
