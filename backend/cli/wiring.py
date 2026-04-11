from __future__ import annotations

import json
import os
from decimal import Decimal
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urlparse

from backend.cli.approval.flow import approve_intent, reject_intent, show_approval
from backend.data.context_builder.models import DecisionContext
from backend.data.context_builder.models import (
    CapitalFlow,
    ExecutionState,
    LiquidityDepth,
    MarketTrend,
    OnchainFlow,
    PositionState,
    RiskState,
    StrategyConstraints,
    TrendDirection,
)
from backend.cli.errors import CLISurfaceInputError, RouteBindingMissingError
from backend.cli.models import DecisionMeta
from backend.cli.runtime_store import CLIRuntimeStore, IntentArtifactRecord
from backend.cli.views.alerts import AlertSeverity, AlertView
from backend.decision import (
    CryptoAgentsAdapter,
    CryptoAgentsRunnerDependencyError,
    CryptoAgentsStructuredOutputMissingError,
    MainChainRequest,
    MainChainService,
    ProductionCryptoAgentsRunner,
)
from backend.execution.compiler.models import ChainStateSnapshot, RegistrationContext
from backend.execution.runtime import ContractGateway, Web3InvestmentCompilerClient
from backend.export import DecisionArtifact, ExecutionRecord, export_outputs
from backend.monitor.shadow_monitor import ShadowMonitor
from backend.reactive.adapters.models import ReactiveTrigger
from backend.strategy.models import BpsRange, StrategyIntent, TradeIntent
from backend.strategy import StrategyBoundaryService, StrategyTemplate
from backend.validation.models import ExecutionPlan as ValidationExecutionPlan
from backend.validation.models import ValidationResult
from backend.validation import validate_inputs_or_raise
from backend.validation.pre_registration_check import RPCStateSnapshot

if TYPE_CHECKING:
    from backend.cli.app import CLISurfaceServices


class MainChainServicePort(Protocol):
    def run_or_raise(self, request: Any) -> Any: ...


class MainChainRequestFactoryPort(Protocol):
    def build(self, *, context_id: str) -> Any: ...


RUNTIME_MAIN_CHAIN_REQUEST_JSON_ENV = "REACTIVE_MAINCHAIN_REQUEST_JSON"
RUNTIME_CLI_DB_PATH_ENV = "REACTIVE_CLI_DB_PATH"
RUNTIME_DECISION_STRICT_ENV = "REACTIVE_DECISION_STRICT"
RUNTIME_ENV_NAME = "REACTIVE_ENV"
RUNTIME_PRODUCTION_NAME = "production"


def build_runtime_store_from_env() -> CLIRuntimeStore:
    raw_path = os.environ.get(RUNTIME_CLI_DB_PATH_ENV)
    if raw_path:
        db_path = Path(raw_path)
    else:
        db_path = Path(__file__).resolve().parents[2] / "tmp" / "cli_state.db"
    return CLIRuntimeStore(db_path=db_path)


def build_decision_run_handler(
    *,
    main_chain_service: MainChainServicePort,
    request_factory: MainChainRequestFactoryPort,
):
    def _handler(context_id: str) -> str:
        request = request_factory.build(context_id=context_id)
        result = main_chain_service.run_or_raise(request)
        payload = {
            "intent_id": _safe_get(result, "execution_plan", "register_payload", "intent_id"),
            "register_tx_hash": _safe_get(result, "register_receipt", "tx_hash"),
            "execution_status": _safe_get(result, "execution_record", "status"),
        }
        return json.dumps(payload, ensure_ascii=False)

    return _handler


def build_contract_gateway_from_web3(
    *,
    web3: Any,
    contract: Any,
    tx_sender: str,
    private_key: str | None = None,
) -> ContractGateway:
    return ContractGateway(
        client=Web3InvestmentCompilerClient(
            web3=web3,
            contract=contract,
            tx_sender=tx_sender,
            private_key=private_key,
        )
    )


def build_cryptoagents_decision_adapter(*, runner: Any | None = None) -> CryptoAgentsAdapter:
    if runner is not None:
        return CryptoAgentsAdapter(runner=runner)
    primary_runner = ProductionCryptoAgentsRunner()
    if _decision_strict_enabled():
        return CryptoAgentsAdapter(runner=primary_runner)
    return CryptoAgentsAdapter(
        runner=_ResilientCryptoAgentsRunner(
            primary=primary_runner,
            fallback=_DeterministicFallbackRunner(),
        )
    )


class _ResilientCryptoAgentsRunner:
    def __init__(self, *, primary: Any, fallback: Any) -> None:
        self._primary = primary
        self._fallback = fallback

    def run(self, context: DecisionContext) -> dict[str, Any]:
        try:
            return self._primary.run(context)
        except (
            CryptoAgentsRunnerDependencyError,
            CryptoAgentsStructuredOutputMissingError,
            ImportError,
            ModuleNotFoundError,
        ):
            return self._fallback.run(context)


class _DeterministicFallbackRunner:
    def run(self, context: DecisionContext) -> dict[str, Any]:
        pair = context.strategy_constraints.pair
        dex = context.strategy_constraints.dex
        return {
            "pair": pair,
            "dex": dex,
            "position_usd": str(context.strategy_constraints.max_position_usd),
            "max_slippage_bps": context.strategy_constraints.max_slippage_bps,
            "stop_loss_bps": context.strategy_constraints.stop_loss_bps,
            "take_profit_bps": context.strategy_constraints.take_profit_bps,
            "entry_conditions": ["price_below:3000"],
            "ttl_seconds": context.strategy_constraints.ttl_seconds,
            "projected_daily_trade_count": min(1, context.strategy_constraints.daily_trade_limit),
            "investment_thesis": "Fallback runner generated conditional intent from strategy constraints.",
            "confidence_score": "0.5",
            "agent_trace_steps": [
                {
                    "agent": "fallback_runner",
                    "summary": "Generated deterministic output because production runner was unavailable.",
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }
            ],
        }


def _decision_strict_enabled() -> bool:
    raw = os.environ.get(RUNTIME_DECISION_STRICT_ENV, "").strip().lower()
    if raw in {"", "0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    raise RouteBindingMissingError(
        f"{RUNTIME_DECISION_STRICT_ENV} must be one of 1/0/true/false/yes/no/on/off"
    )


def build_decision_run_handler_from_runtime_env(
    *,
    contract_gateway: ContractGateway,
    runtime_store: CLIRuntimeStore,
    decision_adapter: CryptoAgentsAdapter | None = None,
):
    adapter = decision_adapter or build_cryptoagents_decision_adapter()

    def _handler(strategy_id: str) -> str:
        request = _build_main_chain_request_for_strategy(
            strategy_id=strategy_id,
            runtime_store=runtime_store,
            contract_gateway=contract_gateway,
        )
        service = MainChainService(
            decision_adapter=adapter,
            boundary_service=StrategyBoundaryService([request.strategy_template]),
            contract_gateway=contract_gateway,
        )
        result = service.run_or_raise(request)
        _persist_intent_artifact(
            strategy_id=strategy_id,
            result=result,
            runtime_store=runtime_store,
        )
        payload = {
            "intent_id": _safe_get(result, "execution_plan", "register_payload", "intent_id"),
            "register_tx_hash": _safe_get(result, "register_receipt", "tx_hash"),
            "execution_status": _safe_get(result, "execution_record", "status"),
        }
        return json.dumps(payload, ensure_ascii=False)

    return _handler


def build_decision_dry_run_handler_from_runtime_env(
    *,
    runtime_store: CLIRuntimeStore,
    contract_gateway: ContractGateway | None = None,
    decision_adapter: CryptoAgentsAdapter | None = None,
):
    adapter = decision_adapter or build_cryptoagents_decision_adapter()

    def _handler(strategy_id: str) -> str:
        request = _build_main_chain_request_for_strategy(
            strategy_id=strategy_id,
            runtime_store=runtime_store,
            contract_gateway=contract_gateway,
            dry_run=True,
        )
        decision = adapter.build_decision_or_raise(
            decision_context=request.decision_context,
            strategy_template=request.strategy_template,
        )
        payload = {
            "strategy_id": strategy_id,
            "strategy_intent": decision.strategy_intent.model_dump(mode="json"),
            "trade_intent": decision.trade_intent.model_dump(mode="json"),
            "decision_meta": decision.decision_meta.model_dump(mode="json"),
            "agent_trace": decision.agent_trace.model_dump(mode="json"),
        }
        return json.dumps(payload, ensure_ascii=False)

    return _handler


def build_contract_gateway_from_runtime_env() -> ContractGateway:
    try:
        from web3 import Web3
    except ImportError as exc:
        raise RouteBindingMissingError("web3 is required for execution.force-close runtime wiring") from exc

    rpc_url = os.environ.get("SEPOLIA_RPC_URL") or os.environ.get("BASE_SEPOLIA_RPC_URL")
    private_key = os.environ.get("SEPOLIA_PRIVATE_KEY")
    contract_address = os.environ.get("REACTIVE_INVESTMENT_COMPILER_ADDRESS")
    artifact_path = os.environ.get("REACTIVE_INVESTMENT_COMPILER_ARTIFACT") or str(
        Path(__file__).resolve().parents[2]
        / "backend"
        / "contracts"
        / "out"
        / "ReactiveInvestmentCompiler.sol"
        / "ReactiveInvestmentCompiler.json"
    )

    missing_envs: list[str] = []
    if not rpc_url:
        missing_envs.append("SEPOLIA_RPC_URL (or BASE_SEPOLIA_RPC_URL)")
    if not private_key:
        missing_envs.append("SEPOLIA_PRIVATE_KEY")
    if not contract_address:
        missing_envs.append("REACTIVE_INVESTMENT_COMPILER_ADDRESS")
    if missing_envs:
        raise RouteBindingMissingError(
            "execution.force-close missing env: " + ", ".join(missing_envs)
        )

    artifact_file = Path(artifact_path)
    if not artifact_file.exists():
        raise RouteBindingMissingError(
            f"execution.force-close missing contract artifact: {artifact_file}"
        )
    abi = _load_contract_abi(artifact_file)

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise RouteBindingMissingError(f"execution.force-close cannot connect rpc: {rpc_url}")
    contract = web3.eth.contract(address=contract_address, abi=abi)
    sender = web3.eth.account.from_key(private_key).address
    return build_contract_gateway_from_web3(
        web3=web3,
        contract=contract,
        tx_sender=sender,
        private_key=private_key,
    )


def build_execution_force_close_handler(
    *,
    contract_gateway: ContractGateway,
    max_slippage_bps: int,
    runtime_store: CLIRuntimeStore | None = None,
):
    if isinstance(max_slippage_bps, bool) or not isinstance(max_slippage_bps, int):
        raise ValueError("max_slippage_bps must be int")
    if max_slippage_bps < 0 or max_slippage_bps > 10_000:
        raise ValueError("max_slippage_bps must be in [0, 10000]")

    def _handler(intent_id: str) -> str:
        try:
            receipt = contract_gateway.emergency_force_close(
                intent_id=intent_id,
                max_slippage_bps=max_slippage_bps,
            )
        except ValueError as exc:
            raise CLISurfaceInputError(str(exc)) from exc
        if runtime_store is not None:
            _merge_force_close_receipt(
                runtime_store=runtime_store,
                intent_id=intent_id,
                receipt=receipt,
            )
        return json.dumps(
            {
                "intent_id": intent_id,
                "max_slippage_bps": max_slippage_bps,
                "tx_hash": _safe_get(receipt, "tx_hash"),
                "status": _safe_get(receipt, "status"),
                "block_number": _safe_get(receipt, "block_number"),
            },
            ensure_ascii=False,
        )

    return _handler


def _build_main_chain_request_for_strategy(
    *,
    strategy_id: str,
    runtime_store: CLIRuntimeStore,
    contract_gateway: ContractGateway | None,
    dry_run: bool = False,
) -> MainChainRequest:
    if os.environ.get(RUNTIME_MAIN_CHAIN_REQUEST_JSON_ENV):
        return _load_main_chain_request_from_runtime_env(context_id=strategy_id)

    try:
        strategy_record = runtime_store.get_strategy(strategy_id)
    except KeyError as exc:
        raise CLISurfaceInputError(str(exc)) from exc

    strategy_template = StrategyTemplate.model_validate(strategy_record.template)
    constraints = StrategyConstraints.model_validate(strategy_record.constraints)
    intent_id = _build_intent_id(strategy_id=strategy_id)
    trade_intent_id = f"ti-{strategy_id}-{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"

    chain_state = _build_chain_state(contract_gateway=contract_gateway)
    rpc_snapshot = _build_rpc_snapshot(chain_state=chain_state)
    registration_context = _build_registration_context(
        strategy_record=strategy_record,
        intent_id=intent_id,
        contract_gateway=contract_gateway,
    )

    return MainChainRequest(
        decision_context=_build_decision_context(
            strategy_id=strategy_id,
            constraints=constraints,
        ),
        strategy_template=strategy_template,
        rpc_state_snapshot=rpc_snapshot,
        chain_state=chain_state,
        registration_context=registration_context,
        reactive_trigger=ReactiveTrigger(
            trigger_type="entry",
            intent_id=intent_id,
            trade_intent_id=trade_intent_id,
            metadata={"observed_out": _resolve_observed_out(dry_run=dry_run)},
        ),
        memo_brief=strategy_record.memo_brief,
    )


def _persist_intent_artifact(
    *,
    strategy_id: str,
    result: Any,
    runtime_store: CLIRuntimeStore,
) -> None:
    trade_intent = result.decision.trade_intent
    execution_plan = result.execution_plan
    validation_result = result.validation_result_post
    cli_decision_meta = DecisionMeta(
        trade_intent_id=trade_intent.trade_intent_id,
        created_at=result.decision.decision_meta.generated_at,
        ttl_seconds=trade_intent.ttl_seconds,
    )
    validation_plan = ValidationExecutionPlan.model_validate(
        execution_plan.model_dump(mode="python", by_alias=True)
    )
    monitor_alerts: list[dict[str, Any]] = []
    monitor_status = {"status": "healthy", "checked_at": datetime.now(tz=timezone.utc).isoformat()}
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    runtime_store.save_intent_artifact(
        IntentArtifactRecord(
            intent_id=execution_plan.register_payload.intent_id,
            strategy_id=strategy_id,
            trade_intent_id=trade_intent.trade_intent_id,
            approval_status="pending",
            approval_payload={
                "trade_intent": _to_jsonable(trade_intent.model_dump(mode="python")),
                "execution_plan": _to_jsonable(validation_plan.model_dump(mode="python")),
                "validation_result": _to_jsonable(validation_result.model_dump(mode="python")),
                "decision_meta": _to_jsonable(cli_decision_meta.model_dump(mode="python")),
            },
            machine_truth_json=result.export_outputs.machine_truth_json,
            execution_record=_to_jsonable(result.execution_record.model_dump(mode="python")),
            export_markdown=result.export_outputs.audit_markdown,
            export_memo=result.export_outputs.investment_memo,
            monitor_alerts=monitor_alerts,
            monitor_status=monitor_status,
            created_at=now_iso,
            updated_at=now_iso,
        )
    )


def _merge_force_close_receipt(
    *,
    runtime_store: CLIRuntimeStore,
    intent_id: str,
    receipt: dict[str, Any],
) -> None:
    try:
        artifact = runtime_store.get_intent_artifact(intent_id)
    except KeyError:
        return
    execution_record = dict(artifact.execution_record)
    execution_record["emergency_force_close_receipt"] = _to_jsonable(receipt)
    execution_record["last_operator_action"] = "force_close"
    updated = artifact.model_copy(
        update={
            "execution_record": execution_record,
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
    )
    runtime_store.save_intent_artifact(updated)


def build_production_services(
    *,
    contract_gateway: ContractGateway | None = None,
    runtime_store: CLIRuntimeStore | None = None,
    emergency_force_close_max_slippage_bps: int = 300,
    decision_run_handler: Any | None = None,
    decision_dry_run_handler: Any | None = None,
    decision_missing_reason: str | None = None,
    force_close_missing_reason: str | None = None,
) -> "CLISurfaceServices":
    from backend.cli.app import CLISurfaceServices

    store = runtime_store or build_runtime_store_from_env()

    def strategy_create() -> str:
        strategy_id = f"strat-{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"
        strategy = store.create_strategy(
            strategy_id=strategy_id,
            template=_default_strategy_template().model_dump(mode="json"),
            constraints=_default_strategy_constraints().model_dump(mode="json"),
            registration_context=_default_registration_context(),
            memo_brief="created by cli strategy.create",
        )
        return json.dumps(
            {
                "strategy_id": strategy.strategy_id,
                "pair": strategy.constraints.get("pair"),
                "dex": strategy.constraints.get("dex"),
                "template_id": strategy.template.get("template_id"),
                "template_version": strategy.template.get("version"),
            },
            ensure_ascii=False,
        )

    def strategy_list() -> str:
        records = store.list_strategies()
        payload = [
            {
                "strategy_id": item.strategy_id,
                "pair": item.constraints.get("pair"),
                "dex": item.constraints.get("dex"),
                "template_id": item.template.get("template_id"),
                "template_version": item.template.get("version"),
                "updated_at": item.updated_at,
            }
            for item in records
        ]
        return json.dumps(payload, ensure_ascii=False)

    def strategy_show(strategy_id: str) -> str:
        try:
            record = store.get_strategy(strategy_id)
        except KeyError as exc:
            raise CLISurfaceInputError(str(exc)) from exc
        return json.dumps(
            {
                "strategy_id": record.strategy_id,
                "template": record.template,
                "constraints": record.constraints,
                "registration_context": record.registration_context,
                "memo_brief": record.memo_brief,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            },
            ensure_ascii=False,
        )

    def strategy_edit(strategy_id: str) -> str:
        try:
            current = store.get_strategy(strategy_id)
        except KeyError as exc:
            raise CLISurfaceInputError(str(exc)) from exc
        template = dict(current.template)
        template["version"] = int(template.get("version", 0)) + 1
        updated = store.update_strategy(strategy_id, template=template)
        return json.dumps(
            {
                "strategy_id": updated.strategy_id,
                "template_version": updated.template.get("version"),
                "updated_at": updated.updated_at,
            },
            ensure_ascii=False,
        )

    def approval_list() -> str:
        pending = store.list_pending_approval_intents()
        payload = [
            {
                "intent_id": item.intent_id,
                "strategy_id": item.strategy_id,
                "trade_intent_id": item.trade_intent_id,
                "created_at": item.created_at,
                "status": item.approval_status,
            }
            for item in pending
        ]
        return json.dumps(payload, ensure_ascii=False)

    def approval_show(intent_id: str, raw: bool, machine_truth_json: str | None) -> str:
        try:
            artifact = store.get_intent_artifact(intent_id)
        except KeyError as exc:
            raise CLISurfaceInputError(str(exc)) from exc
        approval_payload = artifact.approval_payload
        resolved_raw_json = machine_truth_json or artifact.machine_truth_json
        return show_approval(
            trade_intent=TradeIntent.model_validate(approval_payload["trade_intent"]),
            execution_plan=ValidationExecutionPlan.model_validate(approval_payload["execution_plan"]),
            validation_result=ValidationResult.model_validate(approval_payload["validation_result"]),
            decision_meta=DecisionMeta.model_validate(approval_payload["decision_meta"]),
            machine_truth_json=resolved_raw_json,
            raw=raw,
        )

    def approval_approve(intent_id: str) -> str:
        try:
            artifact = store.get_intent_artifact(intent_id)
        except KeyError as exc:
            raise CLISurfaceInputError(str(exc)) from exc
        approval_payload = artifact.approval_payload
        result = approve_intent(
            trade_intent=TradeIntent.model_validate(approval_payload["trade_intent"]),
            execution_plan=ValidationExecutionPlan.model_validate(approval_payload["execution_plan"]),
            validation_result=ValidationResult.model_validate(approval_payload["validation_result"]),
            decision_meta=DecisionMeta.model_validate(approval_payload["decision_meta"]),
        )
        store.set_approval_status(intent_id=intent_id, approval_status="approved")
        return json.dumps(result.model_dump(mode="json"), ensure_ascii=False)

    def approval_reject(intent_id: str, reason: str) -> str:
        try:
            artifact = store.get_intent_artifact(intent_id)
        except KeyError as exc:
            raise CLISurfaceInputError(str(exc)) from exc
        approval_payload = artifact.approval_payload
        result = reject_intent(
            trade_intent=TradeIntent.model_validate(approval_payload["trade_intent"]),
            decision_meta=DecisionMeta.model_validate(approval_payload["decision_meta"]),
            reason=reason,
        )
        store.set_approval_status(intent_id=intent_id, approval_status="rejected")
        return json.dumps(result.model_dump(mode="json"), ensure_ascii=False)

    def execution_show(intent_id: str) -> str:
        artifact = _get_artifact_or_raise(store, intent_id)
        record = artifact.execution_record
        return json.dumps(
            {
                "intent_id": intent_id,
                "trade_intent_id": artifact.trade_intent_id,
                "status": record.get("status"),
                "state_before": record.get("state_before"),
                "state_after": record.get("state_after"),
                "callback_ref": record.get("callback_ref"),
                "recorded_at": record.get("recorded_at"),
            },
            ensure_ascii=False,
        )

    def execution_logs(intent_id: str) -> str:
        artifact = _get_artifact_or_raise(store, intent_id)
        chain_receipt = artifact.execution_record.get("chain_receipt", {})
        payload = {
            "intent_id": intent_id,
            "tx_hash": chain_receipt.get("tx_hash"),
            "status": chain_receipt.get("status"),
            "block_number": chain_receipt.get("block_number"),
            "logs": chain_receipt.get("logs", []),
        }
        return json.dumps(payload, ensure_ascii=False)

    def export_json(intent_id: str) -> str:
        artifact = _get_artifact_or_raise(store, intent_id)
        return artifact.machine_truth_json

    def export_markdown(intent_id: str) -> str:
        artifact = _get_artifact_or_raise(store, intent_id)
        return artifact.export_markdown

    def export_memo(intent_id: str) -> str:
        artifact = _get_artifact_or_raise(store, intent_id)
        return artifact.export_memo

    def monitor_alerts(critical_only: bool) -> list[AlertView]:
        alerts: list[AlertView] = []
        for strategy in store.list_strategies():
            _ = strategy  # keep explicit iteration for future per-strategy monitor hooks
        for row in _list_all_artifacts(store):
            for item in row.monitor_alerts:
                severity_raw = str(item.get("severity", "warning")).lower()
                severity = AlertSeverity.CRITICAL if severity_raw == "critical" else AlertSeverity.WARNING
                alert = AlertView(
                    code=str(item.get("code", "SHADOW_MONITOR_GENERIC")),
                    severity=severity,
                    message=str(item.get("message", "shadow monitor alert")),
                    source=str(item.get("source", "shadow-monitor")),
                    escalation_required=bool(item.get("escalation_required", False)),
                    intent_id=item.get("intent_id"),
                    observed_price=_opt_str(item.get("observed_price")),
                    threshold_price=_opt_str(item.get("threshold_price")),
                    breach_blocks=item.get("breach_blocks"),
                    estimated_additional_loss_usd=_opt_str(item.get("estimated_additional_loss_usd")),
                )
                if critical_only and alert.severity is not AlertSeverity.CRITICAL:
                    continue
                alerts.append(alert)
        return alerts

    def monitor_shadow_status() -> str:
        all_artifacts = _list_all_artifacts(store)
        critical_count = sum(
            1
            for artifact in all_artifacts
            for item in artifact.monitor_alerts
            if str(item.get("severity", "")).lower() == "critical"
        )
        payload = {
            "status": "critical" if critical_count > 0 else "healthy",
            "tracked_intents": len(all_artifacts),
            "critical_alerts": critical_count,
        }
        return json.dumps(payload, ensure_ascii=False)

    def doctor_check() -> str:
        runtime_env = _resolve_runtime_env()
        openai_api_key_present = bool(os.environ.get("OPENAI_API_KEY"))
        openai_base_url_present = bool(os.environ.get("OPENAI_BASE_URL"))
        local_proxy_vars = _detect_local_proxy_vars()
        proxy_policy_ok = not (runtime_env == RUNTIME_PRODUCTION_NAME and bool(local_proxy_vars))
        llm_env_ready = openai_api_key_present and openai_base_url_present and proxy_policy_ok
        llm_connectivity_ok = False
        llm_connectivity_error = None
        if llm_env_ready:
            llm_connectivity_ok, llm_connectivity_error = _probe_openai_connectivity()
        checks: dict[str, Any] = {
            "db_path": str(store.db_path),
            "db_exists": store.db_path.exists(),
            "rpc_env_present": bool(os.environ.get("SEPOLIA_RPC_URL") or os.environ.get("BASE_SEPOLIA_RPC_URL")),
            "private_key_present": bool(os.environ.get("SEPOLIA_PRIVATE_KEY")),
            "contract_address_present": bool(os.environ.get("REACTIVE_INVESTMENT_COMPILER_ADDRESS")),
            "reactive_env": runtime_env,
            "openai_api_key_present": openai_api_key_present,
            "openai_base_url_present": openai_base_url_present,
            "local_proxy_vars": local_proxy_vars,
            "proxy_policy_ok": proxy_policy_ok,
            "decision_llm_ready": llm_env_ready,
            "llm_connectivity_ok": llm_connectivity_ok,
        }
        if llm_connectivity_error:
            checks["llm_connectivity_error"] = llm_connectivity_error
        artifact_path = os.environ.get("REACTIVE_INVESTMENT_COMPILER_ARTIFACT") or str(
            Path(__file__).resolve().parents[2]
            / "backend"
            / "contracts"
            / "out"
            / "ReactiveInvestmentCompiler.sol"
            / "ReactiveInvestmentCompiler.json"
        )
        checks["artifact_path"] = artifact_path
        checks["artifact_exists"] = Path(artifact_path).exists()
        if contract_gateway is not None:
            checks["contract_gateway_wired"] = True
            checks["rpc_connected"] = True
        else:
            checks["contract_gateway_wired"] = False
            checks["rpc_connected"] = False

        blocked_reasons: list[str] = []
        if not checks["rpc_env_present"]:
            blocked_reasons.append("missing SEPOLIA_RPC_URL or BASE_SEPOLIA_RPC_URL")
        if not checks["private_key_present"]:
            blocked_reasons.append("missing SEPOLIA_PRIVATE_KEY")
        if not checks["contract_address_present"]:
            blocked_reasons.append("missing REACTIVE_INVESTMENT_COMPILER_ADDRESS")
        if not checks["artifact_exists"]:
            blocked_reasons.append("missing contract artifact")
        if not checks["contract_gateway_wired"]:
            blocked_reasons.append("runtime ContractGateway not wired")
        if not checks["openai_api_key_present"]:
            blocked_reasons.append("missing OPENAI_API_KEY")
        if not checks["openai_base_url_present"]:
            blocked_reasons.append("missing OPENAI_BASE_URL")
        if not checks["proxy_policy_ok"]:
            blocked_reasons.append(
                "local proxy is forbidden in production (remove HTTP_PROXY/HTTPS_PROXY/ALL_PROXY localhost settings)"
            )
        if checks["decision_llm_ready"] and not checks["llm_connectivity_ok"]:
            blocked_reasons.append("OPENAI connectivity probe failed")
        checks["blocked_reasons"] = blocked_reasons
        checks["status"] = "ok" if (
            checks["rpc_env_present"]
            and checks["private_key_present"]
            and checks["contract_address_present"]
            and checks["artifact_exists"]
            and checks["contract_gateway_wired"]
            and checks["decision_llm_ready"]
            and checks["llm_connectivity_ok"]
        ) else "blocked"
        return json.dumps(checks, ensure_ascii=False)

    if contract_gateway is None:
        def execution_force_close(intent_id: str) -> str:
            raise RouteBindingMissingError(
                force_close_missing_reason or "execution.force-close requires runtime ContractGateway wiring"
            )
    else:
        execution_force_close = build_execution_force_close_handler(
            contract_gateway=contract_gateway,
            max_slippage_bps=emergency_force_close_max_slippage_bps,
            runtime_store=store,
        )

    if decision_run_handler is None:
        def decision_run(_strategy_id: str) -> str:
            raise RouteBindingMissingError(
                decision_missing_reason or "decision.run requires runtime MainChainRequest wiring"
            )
    else:
        decision_run = decision_run_handler

    if decision_dry_run_handler is None:
        def decision_dry_run(_strategy_id: str) -> str:
            raise RouteBindingMissingError(
                decision_missing_reason or "decision.dry-run requires runtime MainChainRequest wiring"
            )
    else:
        decision_dry_run = decision_dry_run_handler

    return CLISurfaceServices(
        strategy_create=strategy_create,
        strategy_list=strategy_list,
        strategy_show=strategy_show,
        strategy_edit=strategy_edit,
        decision_run=decision_run,
        decision_dry_run=decision_dry_run,
        approval_list=approval_list,
        approval_show=approval_show,
        approval_approve=approval_approve,
        approval_reject=approval_reject,
        execution_show=execution_show,
        execution_logs=execution_logs,
        execution_force_close=execution_force_close,
        execution_fork_replay=(
            lambda intent_id, from_block, to_block: (
                f"execution fork-replay: {intent_id} [{from_block}, {to_block}]"
            )
        ),
        export_json=export_json,
        export_markdown=export_markdown,
        export_memo=export_memo,
        monitor_alerts=monitor_alerts,
        monitor_shadow_status=monitor_shadow_status,
        doctor_check=doctor_check,
    )


def _load_main_chain_request_from_runtime_env(*, context_id: str) -> MainChainRequest:
    request_path = os.environ.get(RUNTIME_MAIN_CHAIN_REQUEST_JSON_ENV)
    if not request_path:
        raise RouteBindingMissingError(
            f"decision.run missing env: {RUNTIME_MAIN_CHAIN_REQUEST_JSON_ENV}"
        )

    request_file = Path(request_path)
    if not request_file.exists():
        raise RouteBindingMissingError(f"decision.run request file not found: {request_file}")

    try:
        payload = json.loads(request_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CLISurfaceInputError(f"invalid decision.run request json: {request_file}") from exc

    request = _parse_main_chain_request_payload(payload)
    if request.decision_context.context_id != context_id:
        raise CLISurfaceInputError(
            "decision.run --strategy must match request.decision_context.context_id"
        )
    return request


def _parse_main_chain_request_payload(payload: Any) -> MainChainRequest:
    if not isinstance(payload, dict):
        raise CLISurfaceInputError("decision.run request payload must be a JSON object")

    required_fields = (
        "decision_context",
        "strategy_template",
        "rpc_state_snapshot",
        "chain_state",
        "registration_context",
        "reactive_trigger",
    )
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        raise CLISurfaceInputError(
            f"decision.run request missing fields: {', '.join(missing_fields)}"
        )

    memo_brief = payload.get("memo_brief")
    if memo_brief is not None and not isinstance(memo_brief, str):
        raise CLISurfaceInputError("decision.run request field `memo_brief` must be string when provided")

    return MainChainRequest(
        decision_context=DecisionContext.model_validate(payload["decision_context"]),
        strategy_template=StrategyTemplate.model_validate(payload["strategy_template"]),
        rpc_state_snapshot=RPCStateSnapshot.model_validate(payload["rpc_state_snapshot"]),
        chain_state=ChainStateSnapshot.model_validate(payload["chain_state"]),
        registration_context=RegistrationContext.model_validate(payload["registration_context"]),
        reactive_trigger=ReactiveTrigger.model_validate(payload["reactive_trigger"]),
        memo_brief=memo_brief,
    )


def _default_strategy_template() -> StrategyTemplate:
    return StrategyTemplate(
        template_id="cli-default-template",
        version=1,
        auto_allowed_pairs=frozenset({"ETH/USDC"}),
        manual_allowed_pairs=frozenset(),
        auto_allowed_dexes=frozenset({"uniswap_v3"}),
        manual_allowed_dexes=frozenset(),
        auto_max_position_usd=Decimal("1200"),
        hard_max_position_usd=Decimal("5000"),
        auto_max_slippage_bps=30,
        hard_max_slippage_bps=100,
        auto_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=200),
        manual_stop_loss_bps_range=BpsRange(min_bps=20, max_bps=400),
        auto_take_profit_bps_range=BpsRange(min_bps=100, max_bps=400),
        manual_take_profit_bps_range=BpsRange(min_bps=50, max_bps=1200),
        auto_daily_trade_limit=2,
        hard_daily_trade_limit=8,
        execution_mode="conditional",
    )


def _default_strategy_constraints() -> StrategyConstraints:
    return StrategyConstraints(
        pair="ETH/USDC",
        dex="uniswap_v3",
        max_position_usd=Decimal("1200"),
        max_slippage_bps=20,
        stop_loss_bps=90,
        take_profit_bps=250,
        ttl_seconds=3600,
        daily_trade_limit=2,
    )


def _default_registration_context() -> dict[str, str]:
    return {
        "input_token": "0x0000000000000000000000000000000000000001",
        "output_token": "0x0000000000000000000000000000000000000002",
    }


def _build_intent_id(*, strategy_id: str) -> str:
    seed = f"{strategy_id}:{datetime.now(tz=timezone.utc).isoformat()}"
    return "0x" + sha256(seed.encode("utf-8")).hexdigest()


def _build_decision_context(*, strategy_id: str, constraints: StrategyConstraints) -> DecisionContext:
    return DecisionContext(
        market_trend=MarketTrend(
            direction=TrendDirection.UP,
            confidence_score=Decimal("0.70"),
            timeframe_minutes=240,
        ),
        capital_flow=CapitalFlow(
            net_inflow_usd=Decimal("1500000"),
            volume_24h_usd=Decimal("50000000"),
            whale_inflow_usd=Decimal("400000"),
            retail_inflow_usd=Decimal("1100000"),
        ),
        liquidity_depth=LiquidityDepth(
            pair=constraints.pair,
            dex=constraints.dex,
            depth_usd_2pct=Decimal("30000000"),
            total_tvl_usd=Decimal("700000000"),
        ),
        onchain_flow=OnchainFlow(
            active_address_delta_24h=2500,
            transaction_count_24h=1100000,
            gas_price_gwei=Decimal("20"),
        ),
        risk_state=RiskState(
            volatility_annualized=Decimal("0.42"),
            var_95_usd=Decimal("2000"),
            correlation_to_market=Decimal("0.75"),
        ),
        position_state=PositionState(
            current_position_usd=Decimal("0"),
            unrealized_pnl_usd=Decimal("0"),
        ),
        execution_state=ExecutionState(
            daily_trades_executed=0,
            daily_volume_usd=Decimal("0"),
        ),
        strategy_constraints=constraints,
        context_id=strategy_id,
    )


def _build_chain_state(*, contract_gateway: ContractGateway | None) -> ChainStateSnapshot:
    web3 = getattr(getattr(contract_gateway, "_client", None), "_web3", None)
    if web3 is not None:
        try:
            latest = web3.eth.get_block("latest")
            base_fee_wei = int(latest.get("baseFeePerGas", 0) or 0)
            base_fee_gwei = max(1, int(web3.from_wei(base_fee_wei, "gwei")))
            return ChainStateSnapshot(
                base_fee_gwei=base_fee_gwei,
                max_priority_fee_gwei=2,
                block_number=int(latest["number"]),
                block_timestamp=int(latest["timestamp"]),
                input_token_decimals=6,
                output_token_decimals=18,
                input_output_price=Decimal("0.0005"),
                input_token_usd_price=Decimal("1"),
            )
        except Exception:
            pass

    return ChainStateSnapshot(
        base_fee_gwei=20,
        max_priority_fee_gwei=2,
        block_number=20_000_000,
        block_timestamp=int(datetime.now(tz=timezone.utc).timestamp()),
        input_token_decimals=6,
        output_token_decimals=18,
        input_output_price=Decimal("0.0005"),
        input_token_usd_price=Decimal("1"),
    )


def _build_rpc_snapshot(*, chain_state: ChainStateSnapshot) -> RPCStateSnapshot:
    return RPCStateSnapshot(
        block_number=chain_state.block_number,
        block_timestamp=chain_state.block_timestamp,
        input_token_usd_price=Decimal("1"),
        input_token_reserve=Decimal("1000000"),
        output_token_reserve=Decimal("500"),
        wallet_input_balance=Decimal("10000"),
        wallet_input_allowance=Decimal("10000"),
        base_fee_gwei=chain_state.base_fee_gwei,
        max_priority_fee_gwei=chain_state.max_priority_fee_gwei,
        max_gas_price_gwei=max(chain_state.base_fee_gwei + 10, 30),
        estimated_gas_used=230000,
        native_token_usd_price=Decimal("3000"),
        expected_profit_usd=Decimal("200"),
        ttl_buffer_seconds=60,
    )


def _build_registration_context(
    *,
    strategy_record: Any,
    intent_id: str,
    contract_gateway: ContractGateway | None,
) -> RegistrationContext:
    registration_context = dict(strategy_record.registration_context)
    owner = registration_context.get("owner")
    if not owner and contract_gateway is not None:
        owner = getattr(getattr(contract_gateway, "_client", None), "_tx_sender", None)
    if not owner:
        owner = "0x0000000000000000000000000000000000000001"
    input_token = registration_context.get("input_token", "0x0000000000000000000000000000000000000001")
    output_token = registration_context.get("output_token", "0x0000000000000000000000000000000000000002")
    return RegistrationContext(
        intent_id=intent_id,
        owner=str(owner),
        input_token=str(input_token),
        output_token=str(output_token),
    )


def _resolve_observed_out(*, dry_run: bool) -> int:
    if dry_run:
        return 1_000_000_000_000_000_000
    raw = os.environ.get("REACTIVE_TRIGGER_OBSERVED_OUT")
    if raw is None:
        return 1_000_000_000_000_000_000
    try:
        value = int(raw)
    except ValueError as exc:
        raise CLISurfaceInputError("REACTIVE_TRIGGER_OBSERVED_OUT must be integer") from exc
    if value <= 0:
        raise CLISurfaceInputError("REACTIVE_TRIGGER_OBSERVED_OUT must be > 0")
    return value


def _get_artifact_or_raise(runtime_store: CLIRuntimeStore, intent_id: str) -> IntentArtifactRecord:
    try:
        return runtime_store.get_intent_artifact(intent_id)
    except KeyError as exc:
        raise CLISurfaceInputError(str(exc)) from exc


def _list_all_artifacts(runtime_store: CLIRuntimeStore) -> list[IntentArtifactRecord]:
    return runtime_store.list_intent_artifacts()


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _to_jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _safe_get(root: Any, *path: str) -> Any:
    current = root
    for key in path:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
            continue
        if is_dataclass(current):
            current = asdict(current).get(key)
            continue
        current = getattr(current, key, None)
    return current


def _load_contract_abi(artifact_path: Path) -> Any:
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    abi = artifact.get("abi")
    if not isinstance(abi, list):
        raise RouteBindingMissingError(f"invalid abi in artifact: {artifact_path}")
    return abi


def _resolve_runtime_env() -> str:
    raw = os.environ.get(RUNTIME_ENV_NAME, "").strip().lower()
    if not raw:
        return "development"
    return raw


def _detect_local_proxy_vars() -> list[str]:
    local_proxy_vars: list[str] = []
    for env_name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        raw = os.environ.get(env_name)
        if raw and _is_local_proxy_url(raw):
            local_proxy_vars.append(env_name)
    return local_proxy_vars


def _is_local_proxy_url(proxy_url: str) -> bool:
    parsed = urlparse(proxy_url)
    host = (parsed.hostname or "").strip().lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def _probe_openai_connectivity() -> tuple[bool, str | None]:
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - dependency/env dependent
        return False, f"openai import failed: {exc.__class__.__name__}"

    try:
        client = OpenAI(timeout=20.0)
        client.models.list()
        return True, None
    except Exception as exc:  # pragma: no cover - network dependent
        return False, f"{exc.__class__.__name__}: {str(exc)[:180]}"


__all__ = [
    "build_contract_gateway_from_web3",
    "build_contract_gateway_from_runtime_env",
    "build_cryptoagents_decision_adapter",
    "build_decision_dry_run_handler_from_runtime_env",
    "build_decision_run_handler",
    "build_decision_run_handler_from_runtime_env",
    "build_execution_force_close_handler",
    "build_production_services",
    "build_runtime_store_from_env",
]
