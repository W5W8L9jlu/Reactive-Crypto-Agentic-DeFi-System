from __future__ import annotations

from .errors import CallbackValidationError, MissingReactiveRuntimeSpecError, UnknownReactiveIntentError
from .models import (
    InvestmentPositionStateMachinePort,
    InvestmentStateMachineIntent,
    ReactiveExecutionPlan,
    ReactivePositionState,
    ReactiveTrigger,
    ReactiveTriggerKind,
)


class ReactiveRuntime:
    def __init__(self, *, state_machine: InvestmentPositionStateMachinePort) -> None:
        self._state_machine = state_machine
        self._registered_plans: dict[str, ReactiveExecutionPlan] = {}

    def register_execution_plan(self, execution_plan: ReactiveExecutionPlan | dict) -> ReactiveExecutionPlan:
        plan = self._coerce_execution_plan(execution_plan)
        intent_id = plan.register_payload.intent_id

        self._state_machine.register_investment_intent(
            intent_id,
            self._adapt_investment_intent(plan),
        )
        self._registered_plans[intent_id] = plan
        return plan

    def handle_trigger(self, trigger: ReactiveTrigger | dict) -> None:
        callback = self._coerce_trigger(trigger)
        if callback.intent_id not in self._registered_plans:
            raise UnknownReactiveIntentError(
                f"reactive callback received before registration for intent_id={callback.intent_id}"
            )

        current_state = self._normalize_position_state(
            self._state_machine.get_position_state(callback.intent_id)
        )
        self._validate_callback(callback=callback, current_state=current_state)
        self._state_machine.execute_reactive_trigger(
            callback.intent_id,
            callback.observed_out,
            self._runtime_exit_min_out(callback),
        )

    def _coerce_execution_plan(self, execution_plan: ReactiveExecutionPlan | dict) -> ReactiveExecutionPlan:
        if isinstance(execution_plan, ReactiveExecutionPlan):
            return execution_plan
        return ReactiveExecutionPlan.model_validate(execution_plan)

    def _coerce_trigger(self, trigger: ReactiveTrigger | dict) -> ReactiveTrigger:
        if isinstance(trigger, ReactiveTrigger):
            return trigger
        return ReactiveTrigger.model_validate(trigger)

    def _adapt_investment_intent(self, plan: ReactiveExecutionPlan) -> InvestmentStateMachineIntent:
        payload = plan.register_payload
        return InvestmentStateMachineIntent(
            owner=payload.owner,
            input_token=payload.input_token,
            output_token=payload.output_token,
            planned_entry_size=payload.planned_entry_size,
            entry_min_out=payload.entry_amount_out_minimum,
            exit_min_out_floor=payload.exit_min_out_floor,
        )

    def _normalize_position_state(self, raw_state: ReactivePositionState | str) -> ReactivePositionState:
        if isinstance(raw_state, ReactivePositionState):
            return raw_state
        try:
            return ReactivePositionState(raw_state)
        except ValueError as exc:
            raise MissingReactiveRuntimeSpecError(
                f"TODO: unsupported state machine state for reactive runtime: {raw_state!r}"
            ) from exc

    def _validate_callback(
        self,
        *,
        callback: ReactiveTrigger,
        current_state: ReactivePositionState,
    ) -> None:
        # TODO(domain): knowledge files do not define source-level callback authentication yet.
        # Phase 1 only validates the registered intent binding and state/trigger compatibility.
        if current_state == ReactivePositionState.CLOSED:
            raise CallbackValidationError("closed positions cannot receive reactive callbacks")

        if current_state == ReactivePositionState.PENDING_ENTRY:
            if callback.kind is not ReactiveTriggerKind.ENTRY:
                raise CallbackValidationError(
                    "exit trigger cannot execute while the investment state is PendingEntry"
                )
            return

        if current_state == ReactivePositionState.ACTIVE_POSITION:
            if callback.kind is ReactiveTriggerKind.ENTRY:
                raise CallbackValidationError(
                    "entry trigger cannot execute while the investment state is ActivePosition"
                )
            if callback.runtime_exit_min_out is None:
                raise CallbackValidationError(
                    "runtime_exit_min_out is required for stop-loss and take-profit callbacks"
                )
            return

        raise MissingReactiveRuntimeSpecError(
            f"TODO: reactive runtime has no callback rule for state={current_state.value}"
        )

    def _runtime_exit_min_out(self, callback: ReactiveTrigger) -> int:
        if callback.kind is ReactiveTriggerKind.ENTRY:
            return 0
        if callback.runtime_exit_min_out is None:
            raise CallbackValidationError(
                "runtime_exit_min_out is required for stop-loss and take-profit callbacks"
            )
        return callback.runtime_exit_min_out
