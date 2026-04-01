import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from backend.reactive.adapters import (
        CallbackValidationError,
        ReactiveExecutionHardConstraints,
        ReactiveExecutionPlan,
        ReactivePositionState,
        ReactiveRegisterPayload,
        ReactiveRuntime,
        ReactiveTrigger,
        ReactiveTriggerKind,
    )
except ImportError:
    CallbackValidationError = None
    ReactiveExecutionHardConstraints = None
    ReactiveExecutionPlan = None
    ReactivePositionState = None
    ReactiveRegisterPayload = None
    ReactiveRuntime = None
    ReactiveTrigger = None
    ReactiveTriggerKind = None


def _build_execution_plan(*, intent_id: str = "0x" + "1" * 64):
    return ReactiveExecutionPlan(
        trade_intent_id=f"trade-{intent_id[-4:]}",
        register_payload=ReactiveRegisterPayload(
            intent_id=intent_id,
            owner="0x1111111111111111111111111111111111111111",
            input_token="0x2222222222222222222222222222222222222222",
            output_token="0x3333333333333333333333333333333333333333",
            planned_entry_size=1_000,
            entry_amount_out_minimum=950,
            entry_valid_until=1_900_000_000,
            max_gas_price_gwei=200,
            stop_loss_slippage_bps=250,
            take_profit_slippage_bps=400,
            exit_min_out_floor=700,
        ),
        hard_constraints=ReactiveExecutionHardConstraints(
            max_slippage_bps=30,
            ttl_seconds=3_600,
            stop_loss_bps=250,
            take_profit_bps=400,
        ),
    )


class FakeStateMachineGateway:
    def __init__(self) -> None:
        self.register_calls: list[tuple[str, object]] = []
        self.execute_calls: list[tuple[str, int, int]] = []
        self.states: dict[str, object] = {}

    def register_investment_intent(self, intent_id: str, intent: object) -> None:
        self.register_calls.append((intent_id, intent))
        self.states[intent_id] = ReactivePositionState.PENDING_ENTRY

    def execute_reactive_trigger(
        self,
        intent_id: str,
        observed_out: int,
        runtime_exit_min_out: int,
    ) -> None:
        self.execute_calls.append((intent_id, observed_out, runtime_exit_min_out))
        current_state = self.states[intent_id]
        if current_state == ReactivePositionState.PENDING_ENTRY:
            self.states[intent_id] = ReactivePositionState.ACTIVE_POSITION
        elif current_state == ReactivePositionState.ACTIVE_POSITION:
            self.states[intent_id] = ReactivePositionState.CLOSED

    def get_position_state(self, intent_id: str) -> object:
        return self.states[intent_id]


class ReactiveRuntimeTestCase(unittest.TestCase):
    def _require_runtime(self) -> None:
        if ReactiveRuntime is None:
            self.fail("TODO: backend.reactive.adapters runtime is not implemented")

    def test_entry_trigger_executes_via_state_machine(self):
        self._require_runtime()
        gateway = FakeStateMachineGateway()
        runtime = ReactiveRuntime(state_machine=gateway)
        plan = _build_execution_plan()

        runtime.register_execution_plan(plan)
        runtime.handle_trigger(
            ReactiveTrigger(
                intent_id=plan.register_payload.intent_id,
                kind=ReactiveTriggerKind.ENTRY,
                observed_out=980,
            )
        )

        self.assertEqual(len(gateway.register_calls), 1)
        self.assertEqual(
            gateway.execute_calls,
            [(plan.register_payload.intent_id, 980, 0)],
        )
        self.assertEqual(
            gateway.get_position_state(plan.register_payload.intent_id),
            ReactivePositionState.ACTIVE_POSITION,
        )

    def test_stop_and_take_profit_triggers_execute_via_state_machine(self):
        self._require_runtime()
        gateway = FakeStateMachineGateway()
        runtime = ReactiveRuntime(state_machine=gateway)

        stop_plan = _build_execution_plan(intent_id="0x" + "2" * 64)
        runtime.register_execution_plan(stop_plan)
        gateway.states[stop_plan.register_payload.intent_id] = ReactivePositionState.ACTIVE_POSITION
        runtime.handle_trigger(
            ReactiveTrigger(
                intent_id=stop_plan.register_payload.intent_id,
                kind=ReactiveTriggerKind.STOP_LOSS,
                observed_out=820,
                runtime_exit_min_out=780,
            )
        )

        take_plan = _build_execution_plan(intent_id="0x" + "3" * 64)
        runtime.register_execution_plan(take_plan)
        gateway.states[take_plan.register_payload.intent_id] = ReactivePositionState.ACTIVE_POSITION
        runtime.handle_trigger(
            ReactiveTrigger(
                intent_id=take_plan.register_payload.intent_id,
                kind=ReactiveTriggerKind.TAKE_PROFIT,
                observed_out=1_250,
                runtime_exit_min_out=1_100,
            )
        )

        self.assertEqual(
            gateway.execute_calls,
            [
                (stop_plan.register_payload.intent_id, 820, 780),
                (take_plan.register_payload.intent_id, 1_250, 1_100),
            ],
        )
        self.assertEqual(
            gateway.get_position_state(stop_plan.register_payload.intent_id),
            ReactivePositionState.CLOSED,
        )
        self.assertEqual(
            gateway.get_position_state(take_plan.register_payload.intent_id),
            ReactivePositionState.CLOSED,
        )

    def test_callback_validation_rejects_exit_trigger_before_entry(self):
        self._require_runtime()
        gateway = FakeStateMachineGateway()
        runtime = ReactiveRuntime(state_machine=gateway)
        plan = _build_execution_plan(intent_id="0x" + "4" * 64)

        runtime.register_execution_plan(plan)

        with self.assertRaises(CallbackValidationError):
            runtime.handle_trigger(
                ReactiveTrigger(
                    intent_id=plan.register_payload.intent_id,
                    kind=ReactiveTriggerKind.STOP_LOSS,
                    observed_out=800,
                    runtime_exit_min_out=750,
                )
            )

        self.assertEqual(gateway.execute_calls, [])


if __name__ == "__main__":
    unittest.main()
