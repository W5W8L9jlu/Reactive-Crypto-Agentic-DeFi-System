from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from backend.decision.schemas.cryptoagents_adapter import CryptoAgentsDecision
from backend.execution.compiler import (
    ChainStateSnapshot,
    CompilationContext,
    RegistrationContext,
    compile_execution_plan,
    freeze_contract_call_inputs,
)
from backend.execution.runtime.execution_layer import execute_runtime_transition_or_raise
from backend.export import DecisionArtifact, ExecutionRecord, ExportOutputs, export_outputs
from backend.reactive.adapters import (
    CallbackExecutionResult,
    InvestmentPositionState,
    InvestmentStateMachinePort,
    ReactiveCallbackType,
    ReactiveTrigger,
    ReactiveTriggerType,
    RegisteredInvestmentIntent,
    run_reactive_runtime_or_raise,
)
from backend.strategy import BoundaryDecision, BoundaryDecisionResult, StrategyBoundaryService, StrategyTemplate
from backend.validation import ValidationResult, validate_inputs_or_raise
from backend.validation.models import ExecutionPlan as ValidationExecutionPlan
from backend.validation.pre_registration_check import (
    PreRegistrationCheckResult,
    RPCStateSnapshot,
    run_pre_registration_check_or_raise,
)


class MainChainDomainError(ValueError):
    """Base domain error for end-to-end main-chain orchestration."""


class MainChainBoundaryBlockedError(MainChainDomainError):
    """Raised when boundary decision is not auto-register and cannot continue main path."""


class MainChainRuntimeInputError(MainChainDomainError):
    """Raised when reactive trigger metadata cannot drive executeReactiveTrigger."""


class DecisionAdapterPort(Protocol):
    def build_decision_or_raise(
        self,
        *,
        decision_context: Any,
        strategy_template: StrategyTemplate,
    ) -> CryptoAgentsDecision: ...


class ContractGatewayPort(Protocol):
    def register_investment_intent(self, *, call_inputs: Any) -> dict[str, Any]: ...

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState: ...

    def execute_reactive_trigger(
        self,
        *,
        intent_id: str,
        trigger_type: ReactiveTriggerType | str,
        observed_out: int,
    ) -> dict[str, Any]: ...

    def get_transaction_receipt(self, *, tx_hash: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class MainChainRequest:
    decision_context: Any
    strategy_template: StrategyTemplate
    rpc_state_snapshot: RPCStateSnapshot
    chain_state: ChainStateSnapshot
    registration_context: RegistrationContext
    reactive_trigger: ReactiveTrigger
    memo_brief: str | None = None


@dataclass(frozen=True)
class MainChainResult:
    decision: CryptoAgentsDecision
    boundary_result: BoundaryDecisionResult
    validation_result_pre: ValidationResult
    pre_registration_result: PreRegistrationCheckResult
    execution_plan: Any
    validation_result_post: ValidationResult
    register_receipt: dict[str, Any]
    reactive_runtime_result: Any
    execution_record: Any
    export_outputs: ExportOutputs


class _GatewayBackedStateMachine(InvestmentStateMachinePort):
    def __init__(self, *, contract_gateway: ContractGatewayPort) -> None:
        self._contract_gateway = contract_gateway

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState:
        return self._contract_gateway.get_position_state(intent_id=intent_id)

    def execute_entry_callback(
        self,
        *,
        intent: RegisteredInvestmentIntent,
        trigger: ReactiveTrigger,
    ) -> CallbackExecutionResult:
        observed_out = _required_int(trigger.metadata, "observed_out")
        tx = self._contract_gateway.execute_reactive_trigger(
            intent_id=intent.intent_id,
            trigger_type=ReactiveTriggerType.ENTRY,
            observed_out=observed_out,
        )
        callback_ref = _required_str(tx, "tx_hash")
        state_after = self._contract_gateway.get_position_state(intent_id=intent.intent_id)
        return CallbackExecutionResult(
            callback_type=ReactiveCallbackType.ENTRY,
            is_executed=True,
            state_after=state_after,
            callback_ref=callback_ref,
        )

    def execute_exit_callback(
        self,
        *,
        intent: RegisteredInvestmentIntent,
        trigger: ReactiveTrigger,
    ) -> CallbackExecutionResult:
        observed_out = _required_int(trigger.metadata, "observed_out")
        tx = self._contract_gateway.execute_reactive_trigger(
            intent_id=intent.intent_id,
            trigger_type=trigger.trigger_type,
            observed_out=observed_out,
        )
        callback_ref = _required_str(tx, "tx_hash")
        state_after = self._contract_gateway.get_position_state(intent_id=intent.intent_id)
        callback_type = (
            ReactiveCallbackType.EXIT_STOP_LOSS
            if trigger.trigger_type is ReactiveTriggerType.STOP_LOSS
            else ReactiveCallbackType.EXIT_TAKE_PROFIT
        )
        return CallbackExecutionResult(
            callback_type=callback_type,
            is_executed=True,
            state_after=state_after,
            callback_ref=callback_ref,
        )


class MainChainService:
    def __init__(
        self,
        *,
        decision_adapter: DecisionAdapterPort,
        boundary_service: StrategyBoundaryService,
        contract_gateway: ContractGatewayPort,
    ) -> None:
        self._decision_adapter = decision_adapter
        self._boundary_service = boundary_service
        self._contract_gateway = contract_gateway

    def run_or_raise(self, request: MainChainRequest) -> MainChainResult:
        decision = self._decision_adapter.build_decision_or_raise(
            decision_context=request.decision_context,
            strategy_template=request.strategy_template,
        )
        boundary_result = self._boundary_service.evaluate(
            decision.strategy_intent,
            decision.trade_intent,
        )
        if boundary_result.boundary_decision is not BoundaryDecision.AUTO_REGISTER:
            raise MainChainBoundaryBlockedError(
                f"boundary decision is {boundary_result.boundary_decision.value}; main-chain auto-register path blocked"
            )

        validation_result_pre = validate_inputs_or_raise(
            strategy_template=request.strategy_template,
            strategy_intent=decision.strategy_intent,
            trade_intent=decision.trade_intent,
        )
        pre_registration_result = run_pre_registration_check_or_raise(
            strategy_intent=decision.strategy_intent,
            trade_intent=decision.trade_intent,
            rpc_state_snapshot=request.rpc_state_snapshot,
        )
        execution_plan = compile_execution_plan(
            context=CompilationContext(
                strategy_intent=decision.strategy_intent,
                trade_intent=decision.trade_intent,
                chain_state=request.chain_state,
                registration_context=request.registration_context,
            )
        )
        validation_plan = ValidationExecutionPlan.model_validate(
            execution_plan.model_dump(mode="python", by_alias=True)
        )
        validation_result_post = validate_inputs_or_raise(
            strategy_template=request.strategy_template,
            strategy_intent=decision.strategy_intent,
            trade_intent=decision.trade_intent,
            execution_plan=validation_plan,
        )

        register_call_inputs = freeze_contract_call_inputs(execution_plan)
        register_receipt = self._contract_gateway.register_investment_intent(
            call_inputs=register_call_inputs
        )
        runtime_trigger = request.reactive_trigger.model_copy(
            update={"trade_intent_id": decision.trade_intent.trade_intent_id}
        )
        runtime_result = run_reactive_runtime_or_raise(
            registered_intent=RegisteredInvestmentIntent(
                intent_id=register_call_inputs.intent_id,
                trade_intent_id=decision.trade_intent.trade_intent_id,
            ),
            reactive_trigger=runtime_trigger,
            state_machine=_GatewayBackedStateMachine(contract_gateway=self._contract_gateway),
        )
        execution_record = execute_runtime_transition_or_raise(
            execution_plan=execution_plan,
            runtime_result=runtime_result,
            receipt_reader=self._contract_gateway,
        )
        decision_artifact = DecisionArtifact.model_validate(
            {
                "strategy_intent": decision.strategy_intent.model_dump(mode="python"),
                "trade_intent": decision.trade_intent.model_dump(mode="python"),
                "decision_meta": decision.decision_meta.model_dump(mode="python"),
                "agent_trace": decision.agent_trace.model_dump(mode="python"),
                "boundary_result": boundary_result.model_dump(mode="python"),
                "validation_result_pre": validation_result_pre.model_dump(mode="python"),
                "pre_registration_result": pre_registration_result.model_dump(mode="python"),
                "execution_plan": execution_plan.model_dump(mode="python", by_alias=True),
                "validation_result_post": validation_result_post.model_dump(mode="python"),
                "register_receipt": register_receipt,
            }
        )
        export_bundle = export_outputs(
            decision_artifact=decision_artifact,
            execution_record=ExecutionRecord.model_validate(
                execution_record.model_dump(mode="python")
            ),
            memo_brief=request.memo_brief,
        )
        return MainChainResult(
            decision=decision,
            boundary_result=boundary_result,
            validation_result_pre=validation_result_pre,
            pre_registration_result=pre_registration_result,
            execution_plan=execution_plan,
            validation_result_post=validation_result_post,
            register_receipt=register_receipt,
            reactive_runtime_result=runtime_result,
            execution_record=execution_record,
            export_outputs=export_bundle,
        )


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MainChainRuntimeInputError(f"reactive trigger metadata `{key}` must be int")
    if value < 0:
        raise MainChainRuntimeInputError(f"reactive trigger metadata `{key}` must be >= 0")
    return value


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise MainChainRuntimeInputError(f"contract gateway response `{key}` must be non-empty str")
    return value


__all__ = [
    "MainChainBoundaryBlockedError",
    "MainChainDomainError",
    "MainChainRequest",
    "MainChainResult",
    "MainChainRuntimeInputError",
    "MainChainService",
]
