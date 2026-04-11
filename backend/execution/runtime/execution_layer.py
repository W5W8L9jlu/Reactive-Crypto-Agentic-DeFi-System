from __future__ import annotations

from typing import Any, Protocol

from pydantic import ValidationError

from backend.execution.compiler.models import ExecutionPlan as CompiledExecutionPlan
from backend.reactive.adapters.models import ReactiveRuntimeResult

from .errors import InvalidRuntimeTransitionError, MissingExecutionReceiptError
from .models import ChainReceipt, ExecutionRecord


class ChainReceiptReaderPort(Protocol):
    def get_transaction_receipt(self, *, tx_hash: str) -> dict[str, Any] | None: ...


def execute_runtime_transition_or_raise(
    *,
    execution_plan: CompiledExecutionPlan | dict[str, Any],
    runtime_result: ReactiveRuntimeResult | dict[str, Any],
    receipt_reader: ChainReceiptReaderPort,
) -> ExecutionRecord:
    parsed_plan = CompiledExecutionPlan.model_validate(execution_plan)
    parsed_runtime = ReactiveRuntimeResult.model_validate(runtime_result)

    if not parsed_runtime.is_executed:
        raise InvalidRuntimeTransitionError("runtime_result.is_executed must be True before execution recording")
    if not parsed_runtime.callback_ref:
        raise InvalidRuntimeTransitionError("runtime_result.callback_ref is required for receipt lookup")
    if not parsed_runtime.trade_intent_id:
        raise InvalidRuntimeTransitionError("runtime_result.trade_intent_id is required for execution record")
    if not parsed_runtime.intent_id:
        raise InvalidRuntimeTransitionError("runtime_result.intent_id is required for execution record")
    if parsed_runtime.trigger_type is None:
        raise InvalidRuntimeTransitionError("runtime_result.trigger_type is required for execution record")
    if parsed_runtime.callback_type is None:
        raise InvalidRuntimeTransitionError("runtime_result.callback_type is required for execution record")
    if parsed_runtime.state_before is None or parsed_runtime.state_after is None:
        raise InvalidRuntimeTransitionError("runtime_result.state_before/state_after are required for execution record")

    raw_receipt = receipt_reader.get_transaction_receipt(tx_hash=parsed_runtime.callback_ref)
    if raw_receipt is None:
        raise MissingExecutionReceiptError(
            f"missing chain receipt for callback_ref={parsed_runtime.callback_ref}"
        )
    try:
        chain_receipt = ChainReceipt.model_validate(raw_receipt)
    except ValidationError as exc:
        raise MissingExecutionReceiptError(str(exc)) from exc

    return ExecutionRecord(
        trade_intent_id=parsed_runtime.trade_intent_id,
        intent_id=parsed_runtime.intent_id,
        status="executed",
        trigger_type=parsed_runtime.trigger_type.value,
        callback_type=parsed_runtime.callback_type.value,
        state_before=parsed_runtime.state_before.value,
        state_after=parsed_runtime.state_after.value,
        callback_ref=parsed_runtime.callback_ref,
        chain_receipt=chain_receipt,
        execution_plan=parsed_plan.model_dump(mode="python", by_alias=True),
    )


__all__ = [
    "ChainReceiptReaderPort",
    "execute_runtime_transition_or_raise",
]
