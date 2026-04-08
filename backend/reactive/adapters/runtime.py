from __future__ import annotations

from typing import Any, Protocol

from pydantic import ValidationError

from .errors import (
    CallbackVerificationError,
    MissingReactiveRuntimeSpecError,
    ReactiveRuntimeError,
    StateMachineInvariantError,
    TriggerBindingError,
)
from .models import (
    CallbackExecutionResult,
    InvestmentPositionState,
    ReactiveCallbackType,
    ReactiveRuntimeResult,
    ReactiveTrigger,
    ReactiveTriggerType,
    RegisteredInvestmentIntent,
    RuntimeAbortReason,
)


class InvestmentStateMachinePort(Protocol):
    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState: ...

    def execute_entry_callback(
        self,
        *,
        intent: RegisteredInvestmentIntent,
        trigger: ReactiveTrigger,
    ) -> CallbackExecutionResult: ...

    def execute_exit_callback(
        self,
        *,
        intent: RegisteredInvestmentIntent,
        trigger: ReactiveTrigger,
    ) -> CallbackExecutionResult: ...


def run_reactive_runtime_or_raise(
    *,
    registered_intent: RegisteredInvestmentIntent | dict[str, Any],
    reactive_trigger: ReactiveTrigger | dict[str, Any],
    state_machine: InvestmentStateMachinePort,
) -> ReactiveRuntimeResult:
    intent = RegisteredInvestmentIntent.model_validate(registered_intent)
    trigger = ReactiveTrigger.model_validate(reactive_trigger)
    _assert_trigger_binding(intent=intent, trigger=trigger)

    state_before = state_machine.get_position_state(intent_id=intent.intent_id)
    callback_result = _execute_callback(
        intent=intent,
        trigger=trigger,
        state_before=state_before,
        state_machine=state_machine,
    )
    _verify_callback(
        trigger_type=trigger.trigger_type,
        callback_result=callback_result,
    )
    return ReactiveRuntimeResult(
        is_executed=True,
        callback_verified=True,
        intent_id=intent.intent_id,
        trade_intent_id=intent.trade_intent_id,
        trigger_type=trigger.trigger_type,
        callback_type=callback_result.callback_type,
        state_before=state_before,
        state_after=callback_result.state_after,
        callback_ref=callback_result.callback_ref,
    )


def run_reactive_runtime(
    *,
    registered_intent: RegisteredInvestmentIntent | dict[str, Any],
    reactive_trigger: ReactiveTrigger | dict[str, Any],
    state_machine: InvestmentStateMachinePort,
) -> ReactiveRuntimeResult:
    intent_id = _extract_identifier(registered_intent, "intent_id")
    trade_intent_id = _extract_identifier(registered_intent, "trade_intent_id")
    trigger_type = _extract_trigger_type(reactive_trigger)
    try:
        return run_reactive_runtime_or_raise(
            registered_intent=registered_intent,
            reactive_trigger=reactive_trigger,
            state_machine=state_machine,
        )
    except (ValidationError, ReactiveRuntimeError) as exc:
        return ReactiveRuntimeResult(
            is_executed=False,
            callback_verified=False,
            intent_id=intent_id,
            trade_intent_id=trade_intent_id,
            trigger_type=trigger_type,
            abort_reason=_to_abort_reason(exc),
        )


def _assert_trigger_binding(
    *,
    intent: RegisteredInvestmentIntent,
    trigger: ReactiveTrigger,
) -> None:
    if trigger.intent_id != intent.intent_id:
        raise TriggerBindingError("reactive_trigger.intent_id must match registered_intent.intent_id")
    if intent.trade_intent_id is not None and trigger.trade_intent_id != intent.trade_intent_id:
        raise TriggerBindingError("reactive_trigger.trade_intent_id must match registered_intent.trade_intent_id")


def _execute_callback(
    *,
    intent: RegisteredInvestmentIntent,
    trigger: ReactiveTrigger,
    state_before: InvestmentPositionState,
    state_machine: InvestmentStateMachinePort,
) -> CallbackExecutionResult:
    if trigger.trigger_type is ReactiveTriggerType.ENTRY:
        if state_before is not InvestmentPositionState.PENDING_ENTRY:
            raise StateMachineInvariantError("entry trigger requires state=PendingEntry")
        return state_machine.execute_entry_callback(intent=intent, trigger=trigger)

    if trigger.trigger_type in (ReactiveTriggerType.STOP_LOSS, ReactiveTriggerType.TAKE_PROFIT):
        if state_before is not InvestmentPositionState.ACTIVE_POSITION:
            raise StateMachineInvariantError("stop/take trigger requires state=ActivePosition")
        return state_machine.execute_exit_callback(intent=intent, trigger=trigger)

    # TODO: if future trigger types are introduced, freeze the state transition contract in knowledge/docs first.
    raise MissingReactiveRuntimeSpecError(f"unsupported trigger type: {trigger.trigger_type!r}")


def _verify_callback(
    *,
    trigger_type: ReactiveTriggerType,
    callback_result: CallbackExecutionResult,
) -> None:
    expected_callback_type: ReactiveCallbackType
    expected_state_after: InvestmentPositionState
    if trigger_type is ReactiveTriggerType.ENTRY:
        expected_callback_type = ReactiveCallbackType.ENTRY
        expected_state_after = InvestmentPositionState.ACTIVE_POSITION
    elif trigger_type is ReactiveTriggerType.STOP_LOSS:
        expected_callback_type = ReactiveCallbackType.EXIT_STOP_LOSS
        expected_state_after = InvestmentPositionState.CLOSED
    else:
        expected_callback_type = ReactiveCallbackType.EXIT_TAKE_PROFIT
        expected_state_after = InvestmentPositionState.CLOSED

    if not callback_result.is_executed:
        raise CallbackVerificationError("state machine callback reports is_executed=False")
    if callback_result.callback_type is not expected_callback_type:
        raise CallbackVerificationError(
            f"callback_type mismatch: expected={expected_callback_type.value}, got={callback_result.callback_type.value}"
        )
    if callback_result.state_after is not expected_state_after:
        raise CallbackVerificationError(
            f"state transition mismatch: expected={expected_state_after.value}, got={callback_result.state_after.value}"
        )


def _to_abort_reason(exc: Exception) -> RuntimeAbortReason:
    if isinstance(exc, ValidationError):
        detail = exc.errors()[0]
        return RuntimeAbortReason(
            code=str(detail["type"]),
            message=str(detail["msg"]),
            field_path=".".join(str(item) for item in detail["loc"]),
        )
    return RuntimeAbortReason(
        code=exc.__class__.__name__,
        message=str(exc),
        field_path=None,
    )


def _extract_identifier(source: object, field_name: str) -> str | None:
    if isinstance(source, dict):
        value = source.get(field_name)
        return str(value) if isinstance(value, str) else None
    value = getattr(source, field_name, None)
    return str(value) if isinstance(value, str) else None


def _extract_trigger_type(source: object) -> ReactiveTriggerType | None:
    if isinstance(source, ReactiveTrigger):
        return source.trigger_type
    if isinstance(source, dict):
        raw_type = source.get("trigger_type")
        if isinstance(raw_type, str):
            try:
                return ReactiveTriggerType(raw_type)
            except ValueError:
                return None
    return None
