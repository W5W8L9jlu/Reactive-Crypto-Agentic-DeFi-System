from __future__ import annotations

from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
import os
from typing import Any, Protocol

from pydantic import ValidationError

try:
    from .errors import (
        ExecutionAdapterError,
        ExecutionPlanError,
        ReceiptConsistencyError,
        RuntimeGateError,
        RuntimeTriggerError,
    )
    from .models import ChainReceipt, ExecutionRecord, RuntimeTrigger
except ImportError:  # pragma: no cover - support direct script-style imports in local tests.
    def _load_local_module(module_name: str) -> Any:
        module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
        spec = spec_from_file_location(f"execution_runtime_{module_name}", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load local module: {module_name}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    _errors = _load_local_module("errors")
    _models = _load_local_module("models")

    ExecutionAdapterError = _errors.ExecutionAdapterError
    ExecutionPlanError = _errors.ExecutionPlanError
    ReceiptConsistencyError = _errors.ReceiptConsistencyError
    RuntimeGateError = _errors.RuntimeGateError
    RuntimeTriggerError = _errors.RuntimeTriggerError
    ChainReceipt = _models.ChainReceipt
    ExecutionRecord = _models.ExecutionRecord
    RuntimeTrigger = _models.RuntimeTrigger


class RegisterPayloadLike(Protocol):
    intent_id: str


class CompiledExecutionPlan(Protocol):
    trade_intent_id: str
    register_payload: RegisterPayloadLike


class ReactiveExecutionPort(Protocol):
    def execute_reactive_trigger(
        self,
        *,
        execution_plan: CompiledExecutionPlan,
        runtime_trigger: RuntimeTrigger,
    ) -> ChainReceipt | dict[str, Any]: ...


def execute_runtime_trigger(
    *,
    execution_plan: CompiledExecutionPlan,
    runtime_trigger: RuntimeTrigger,
    executor: ReactiveExecutionPort,
    executed_at: datetime | None = None,
) -> ExecutionRecord:
    _ensure_plan_shape(execution_plan)
    _ensure_runtime_gate_passed(runtime_trigger)
    _ensure_trigger_matches_plan(execution_plan=execution_plan, runtime_trigger=runtime_trigger)
    execution_callable = getattr(executor, "execute_reactive_trigger", None)
    if not callable(execution_callable):
        raise ExecutionAdapterError(
            "Executor must expose a callable execute_reactive_trigger method.",
            context={"executor_type": type(executor).__name__},
        )

    raw_receipt = execution_callable(
        execution_plan=execution_plan,
        runtime_trigger=runtime_trigger,
    )
    receipt = _coerce_receipt(raw_receipt)

    return ExecutionRecord(
        trade_intent_id=execution_plan.trade_intent_id,
        intent_id=execution_plan.register_payload.intent_id,
        trigger_id=runtime_trigger.trigger_id,
        trigger_source=runtime_trigger.trigger_source,
        triggered_at=runtime_trigger.triggered_at,
        executed_at=executed_at or datetime.now(tz=timezone.utc),
        execution_status="succeeded" if receipt.status == 1 else "failed",
        receipt=receipt,
    )


def _ensure_runtime_gate_passed(runtime_trigger: RuntimeTrigger) -> None:
    if runtime_trigger.onchain_checks_passed:
        return

    raise RuntimeGateError(
        "Reactive trigger did not pass on-chain runtime checks.",
        context={
            "trigger_id": runtime_trigger.trigger_id,
            "trade_intent_id": runtime_trigger.trade_intent_id,
        },
    )


def _ensure_trigger_matches_plan(
    *,
    execution_plan: CompiledExecutionPlan,
    runtime_trigger: RuntimeTrigger,
) -> None:
    if execution_plan.trade_intent_id == runtime_trigger.trade_intent_id:
        return

    raise RuntimeTriggerError(
        "Runtime trigger trade_intent_id does not match compiled execution plan.",
        context={
            "plan_trade_intent_id": execution_plan.trade_intent_id,
            "trigger_trade_intent_id": runtime_trigger.trade_intent_id,
        },
    )


def _coerce_receipt(raw_receipt: ChainReceipt | dict[str, Any]) -> ChainReceipt:
    if isinstance(raw_receipt, ChainReceipt):
        return raw_receipt

    try:
        return ChainReceipt.model_validate(raw_receipt)
    except ValidationError as exc:
        raise ReceiptConsistencyError(
            "Chain execution returned a receipt that cannot be represented as ChainReceipt.",
            context={"errors": exc.errors()},
        ) from exc


def _ensure_plan_shape(execution_plan: CompiledExecutionPlan) -> None:
    if not hasattr(execution_plan, "trade_intent_id"):
        raise ExecutionPlanError("Compiled execution plan is missing trade_intent_id.")

    register_payload = getattr(execution_plan, "register_payload", None)
    if register_payload is None or not hasattr(register_payload, "intent_id"):
        raise ExecutionPlanError(
            "Compiled execution plan is missing register_payload.intent_id.",
            context={"plan_type": type(execution_plan).__name__},
        )


__all__ = [
    "ChainReceipt",
    "CompiledExecutionPlan",
    "ExecutionRecord",
    "ExecutionAdapterError",
    "ExecutionPlanError",
    "ReceiptConsistencyError",
    "ReactiveExecutionPort",
    "RuntimeGateError",
    "RuntimeTrigger",
    "RuntimeTriggerError",
    "execute_runtime_trigger",
]
