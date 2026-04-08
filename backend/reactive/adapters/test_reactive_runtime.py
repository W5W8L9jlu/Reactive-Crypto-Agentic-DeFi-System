from __future__ import annotations

from datetime import datetime, timezone
import unittest

from backend.reactive.adapters.errors import CallbackVerificationError, StateMachineInvariantError
from backend.reactive.adapters.models import (
    CallbackExecutionResult,
    InvestmentPositionState,
    ReactiveCallbackType,
    ReactiveTrigger,
    ReactiveTriggerType,
    RegisteredInvestmentIntent,
)
from backend.reactive.adapters.runtime import run_reactive_runtime_or_raise


def _registered_intent() -> RegisteredInvestmentIntent:
    return RegisteredInvestmentIntent(
        intent_id="intent-001",
        trade_intent_id="ti-001",
    )


def _trigger(trigger_type: ReactiveTriggerType) -> ReactiveTrigger:
    return ReactiveTrigger(
        trigger_type=trigger_type,
        intent_id="intent-001",
        trade_intent_id="ti-001",
        triggered_at=datetime.now(tz=timezone.utc),
    )


class _FakeStateMachine:
    def __init__(
        self,
        *,
        state: InvestmentPositionState,
        entry_result: CallbackExecutionResult | None = None,
        exit_result: CallbackExecutionResult | None = None,
    ) -> None:
        self.state = state
        self.entry_result = entry_result
        self.exit_result = exit_result
        self.entry_calls = 0
        self.exit_calls = 0

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState:
        self._last_intent_id = intent_id
        return self.state

    def execute_entry_callback(
        self,
        *,
        intent: RegisteredInvestmentIntent,
        trigger: ReactiveTrigger,
    ) -> CallbackExecutionResult:
        self.entry_calls += 1
        if self.entry_result is not None:
            return self.entry_result
        return CallbackExecutionResult(
            callback_type=ReactiveCallbackType.ENTRY,
            is_executed=True,
            state_after=InvestmentPositionState.ACTIVE_POSITION,
            callback_ref="tx-entry-001",
        )

    def execute_exit_callback(
        self,
        *,
        intent: RegisteredInvestmentIntent,
        trigger: ReactiveTrigger,
    ) -> CallbackExecutionResult:
        self.exit_calls += 1
        if self.exit_result is not None:
            return self.exit_result
        callback_type = (
            ReactiveCallbackType.EXIT_STOP_LOSS
            if trigger.trigger_type is ReactiveTriggerType.STOP_LOSS
            else ReactiveCallbackType.EXIT_TAKE_PROFIT
        )
        return CallbackExecutionResult(
            callback_type=callback_type,
            is_executed=True,
            state_after=InvestmentPositionState.CLOSED,
            callback_ref="tx-exit-001",
        )


class ReactiveRuntimeTestCase(unittest.TestCase):
    def test_entry_trigger_executes_entry_callback_from_pending_entry(self) -> None:
        runtime_result = run_reactive_runtime_or_raise(
            registered_intent=_registered_intent(),
            reactive_trigger=_trigger(ReactiveTriggerType.ENTRY),
            state_machine=_FakeStateMachine(state=InvestmentPositionState.PENDING_ENTRY),
        )

        self.assertTrue(runtime_result.callback_verified)
        self.assertEqual(runtime_result.callback_type, ReactiveCallbackType.ENTRY)
        self.assertEqual(runtime_result.state_before, InvestmentPositionState.PENDING_ENTRY)
        self.assertEqual(runtime_result.state_after, InvestmentPositionState.ACTIVE_POSITION)

    def test_stop_loss_trigger_executes_exit_callback_from_active_position(self) -> None:
        runtime_result = run_reactive_runtime_or_raise(
            registered_intent=_registered_intent(),
            reactive_trigger=_trigger(ReactiveTriggerType.STOP_LOSS),
            state_machine=_FakeStateMachine(state=InvestmentPositionState.ACTIVE_POSITION),
        )

        self.assertTrue(runtime_result.callback_verified)
        self.assertEqual(runtime_result.callback_type, ReactiveCallbackType.EXIT_STOP_LOSS)
        self.assertEqual(runtime_result.state_before, InvestmentPositionState.ACTIVE_POSITION)
        self.assertEqual(runtime_result.state_after, InvestmentPositionState.CLOSED)

    def test_take_profit_trigger_executes_exit_callback_from_active_position(self) -> None:
        runtime_result = run_reactive_runtime_or_raise(
            registered_intent=_registered_intent(),
            reactive_trigger=_trigger(ReactiveTriggerType.TAKE_PROFIT),
            state_machine=_FakeStateMachine(state=InvestmentPositionState.ACTIVE_POSITION),
        )

        self.assertTrue(runtime_result.callback_verified)
        self.assertEqual(runtime_result.callback_type, ReactiveCallbackType.EXIT_TAKE_PROFIT)
        self.assertEqual(runtime_result.state_before, InvestmentPositionState.ACTIVE_POSITION)
        self.assertEqual(runtime_result.state_after, InvestmentPositionState.CLOSED)

    def test_callback_verification_fails_when_state_machine_does_not_transition_state(self) -> None:
        fake_state_machine = _FakeStateMachine(
            state=InvestmentPositionState.PENDING_ENTRY,
            entry_result=CallbackExecutionResult(
                callback_type=ReactiveCallbackType.ENTRY,
                is_executed=True,
                state_after=InvestmentPositionState.PENDING_ENTRY,
                callback_ref="tx-entry-001",
            ),
        )
        with self.assertRaises(CallbackVerificationError):
            run_reactive_runtime_or_raise(
                registered_intent=_registered_intent(),
                reactive_trigger=_trigger(ReactiveTriggerType.ENTRY),
                state_machine=fake_state_machine,
            )

    def test_stop_loss_trigger_is_blocked_when_position_not_active(self) -> None:
        with self.assertRaises(StateMachineInvariantError):
            run_reactive_runtime_or_raise(
                registered_intent=_registered_intent(),
                reactive_trigger=_trigger(ReactiveTriggerType.STOP_LOSS),
                state_machine=_FakeStateMachine(state=InvestmentPositionState.PENDING_ENTRY),
            )


if __name__ == "__main__":
    unittest.main()
