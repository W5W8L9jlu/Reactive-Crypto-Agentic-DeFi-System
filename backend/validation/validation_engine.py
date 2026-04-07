from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.strategy.models import StrategyIntent, StrategyTemplate, TradeIntent

from .errors import MissingValidationSpecError, ValidationEngineDomainError
from .models import ContractBinding, ExecutionPlan, ValidationInput, ValidationResult


def validate_inputs_or_raise(
    *,
    strategy_template: StrategyTemplate | dict[str, Any],
    strategy_intent: StrategyIntent | dict[str, Any],
    trade_intent: TradeIntent | dict[str, Any],
    execution_plan: ExecutionPlan | dict[str, Any] | None = None,
) -> ValidationResult:
    parsed_models = _parse_core_models(
        strategy_template=strategy_template,
        strategy_intent=strategy_intent,
        trade_intent=trade_intent,
        execution_plan=execution_plan,
    )
    _assert_known_boundary_spec(parsed_models["strategy_template"])
    validated_input = _build_validation_input(parsed_models)
    return ValidationResult(
        is_valid=True,
        validated_objects=_resolve_validated_objects(execution_plan=validated_input.execution_plan),
        contract_bindings=_build_contract_bindings(validated_input),
    )


def validate_inputs(
    *,
    strategy_template: StrategyTemplate | dict[str, Any],
    strategy_intent: StrategyIntent | dict[str, Any],
    trade_intent: TradeIntent | dict[str, Any],
    execution_plan: ExecutionPlan | dict[str, Any] | None = None,
) -> ValidationResult:
    try:
        return validate_inputs_or_raise(
            strategy_template=strategy_template,
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            execution_plan=execution_plan,
        )
    except (ValidationError, ValidationEngineDomainError) as exc:
        return ValidationResult.from_exception(
            exc=exc,
            validated_objects=_resolve_validated_objects(execution_plan=execution_plan),
        )


def _parse_core_models(
    *,
    strategy_template: StrategyTemplate | dict[str, Any],
    strategy_intent: StrategyIntent | dict[str, Any],
    trade_intent: TradeIntent | dict[str, Any],
    execution_plan: ExecutionPlan | dict[str, Any] | None,
) -> dict[str, Any]:
    parsed_execution_plan = None
    if execution_plan is not None:
        parsed_execution_plan = ExecutionPlan.model_validate(execution_plan)

    return {
        "strategy_template": StrategyTemplate.model_validate(strategy_template),
        "strategy_intent": StrategyIntent.model_validate(strategy_intent),
        "trade_intent": TradeIntent.model_validate(trade_intent),
        "execution_plan": parsed_execution_plan,
    }


def _build_validation_input(parsed_models: dict[str, Any]) -> ValidationInput:
    return ValidationInput.model_validate(parsed_models)


def _assert_known_boundary_spec(template: StrategyTemplate) -> None:
    if not template.auto_allowed_pairs and not template.manual_allowed_pairs:
        raise MissingValidationSpecError(
            "TODO: docs/knowledge/03_strategy_validation/02_validation_engine.md "
            "未定义空 allowed_pairs 的处理规则。"
        )
    if not template.auto_allowed_dexes and not template.manual_allowed_dexes:
        raise MissingValidationSpecError(
            "TODO: docs/knowledge/03_strategy_validation/02_validation_engine.md "
            "未定义空 allowed_dexes 的处理规则。"
        )


def _resolve_validated_objects(
    *,
    execution_plan: ExecutionPlan | dict[str, Any] | None,
) -> tuple[str, ...]:
    if execution_plan is None:
        return ("StrategyTemplate", "StrategyIntent", "TradeIntent")
    return ("StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan")


def _build_contract_bindings(validated_input: ValidationInput) -> tuple[ContractBinding, ...]:
    bindings: list[ContractBinding] = [
        ContractBinding(
            source_field="strategy_template.template_id",
            target_field="strategy_intent.template_id",
            unit="identity",
        ),
        ContractBinding(
            source_field="strategy_template.version",
            target_field="strategy_intent.template_version",
            unit="identity",
        ),
        ContractBinding(
            source_field="strategy_template.execution_mode",
            target_field="strategy_intent.execution_mode",
            unit="identity",
        ),
    ]
    if validated_input.execution_plan is None:
        return tuple(bindings)

    bindings.extend(
        [
            ContractBinding(
                source_field="trade_intent.trade_intent_id",
                target_field="execution_plan.trade_intent_id",
                unit="identity",
            ),
            ContractBinding(
                source_field="trade_intent.max_slippage_bps",
                target_field="execution_plan.hard_constraints.max_slippage_bps",
                unit="bps",
            ),
            ContractBinding(
                source_field="trade_intent.ttl_seconds",
                target_field="execution_plan.hard_constraints.ttl_seconds",
                unit="seconds",
            ),
            ContractBinding(
                source_field="trade_intent.stop_loss_bps",
                target_field="execution_plan.hard_constraints.stop_loss_bps",
                unit="bps",
            ),
            ContractBinding(
                source_field="trade_intent.take_profit_bps",
                target_field="execution_plan.hard_constraints.take_profit_bps",
                unit="bps",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.intentId",
                target_field="register_call.intentId",
                unit="identity",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.owner",
                target_field="investment_intent.owner",
                unit="identity",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.inputToken",
                target_field="investment_intent.inputToken",
                unit="identity",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.outputToken",
                target_field="investment_intent.outputToken",
                unit="identity",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.plannedEntrySize",
                target_field="investment_intent.plannedEntrySize",
                unit="identity",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.entryAmountOutMinimum",
                target_field="investment_intent.entryMinOut",
                unit="identity",
            ),
            ContractBinding(
                source_field="execution_plan.register_payload.exitMinOutFloor",
                target_field="investment_intent.exitMinOutFloor",
                unit="identity",
            ),
        ]
    )
    return tuple(bindings)
