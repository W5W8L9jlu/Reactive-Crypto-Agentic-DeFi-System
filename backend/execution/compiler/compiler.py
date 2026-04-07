from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_UP

from .errors import ConstraintViolationError
from .models import CompilationContext, ContractRegisterCallInputs, ExecutionHardConstraints, ExecutionPlan, RegisterPayload


def compile_execution_plan(context: CompilationContext) -> ExecutionPlan:
    trade_intent = context.trade_intent
    chain_state = context.chain_state
    registration_context = context.registration_context
    config = context.config

    tightened_max_slippage_bps = max(0, trade_intent.max_slippage_bps - config.slippage_tolerance_buffer_bps)
    tightened_ttl_seconds = max(1, trade_intent.ttl_seconds - config.ttl_buffer_seconds)

    hard_constraints = ExecutionHardConstraints(
        max_slippage_bps=tightened_max_slippage_bps,
        ttl_seconds=tightened_ttl_seconds,
        stop_loss_bps=trade_intent.stop_loss_bps,
        take_profit_bps=trade_intent.take_profit_bps,
    )

    planned_entry_size = _compute_planned_entry_size(
        position_usd=trade_intent.position_usd,
        input_token_usd_price=chain_state.input_token_usd_price,
        input_token_decimals=chain_state.input_token_decimals,
    )
    entry_amount_out_minimum = _compute_entry_amount_out_minimum(
        planned_entry_size=planned_entry_size,
        input_output_price=chain_state.input_output_price,
        input_token_decimals=chain_state.input_token_decimals,
        output_token_decimals=chain_state.output_token_decimals,
        max_slippage_bps=tightened_max_slippage_bps,
    )
    exit_min_out_floor = _apply_slippage_bps(
        amount=entry_amount_out_minimum,
        slippage_bps=trade_intent.stop_loss_bps,
    )
    entry_valid_until = int(chain_state.block_timestamp + tightened_ttl_seconds)
    max_gas_price_gwei = _compute_max_gas_price_gwei(
        base_fee_gwei=chain_state.base_fee_gwei,
        priority_fee_gwei=chain_state.max_priority_fee_gwei,
        multiplier=config.gas_buffer_multiplier,
        cap_gwei=config.max_gas_price_cap_gwei,
    )

    register_payload = RegisterPayload(
        intent_id=registration_context.intent_id,
        owner=registration_context.owner,
        input_token=registration_context.input_token,
        output_token=registration_context.output_token,
        planned_entry_size=planned_entry_size,
        entry_amount_out_minimum=entry_amount_out_minimum,
        entry_valid_until=entry_valid_until,
        max_gas_price_gwei=max_gas_price_gwei,
        stop_loss_slippage_bps=trade_intent.stop_loss_bps,
        take_profit_slippage_bps=trade_intent.take_profit_bps,
        exit_min_out_floor=exit_min_out_floor,
    )
    _assert_register_payload(register_payload)

    return ExecutionPlan(
        trade_intent_id=trade_intent.trade_intent_id,
        register_payload=register_payload,
        hard_constraints=hard_constraints,
    )


def freeze_contract_call_inputs(plan: ExecutionPlan) -> ContractRegisterCallInputs:
    return plan.register_payload.as_contract_call_inputs()


def _compute_planned_entry_size(
    *,
    position_usd: Decimal,
    input_token_usd_price: Decimal,
    input_token_decimals: int,
) -> int:
    input_token_amount = position_usd / input_token_usd_price
    scaled = input_token_amount * (Decimal(10) ** input_token_decimals)
    return int(scaled.to_integral_value(rounding=ROUND_DOWN))


def _compute_entry_amount_out_minimum(
    *,
    planned_entry_size: int,
    input_output_price: Decimal,
    input_token_decimals: int,
    output_token_decimals: int,
    max_slippage_bps: int,
) -> int:
    input_amount = Decimal(planned_entry_size) / (Decimal(10) ** input_token_decimals)
    raw_output = input_amount * input_output_price
    scaled_output = raw_output * (Decimal(10) ** output_token_decimals)
    output_amount = int(scaled_output.to_integral_value(rounding=ROUND_DOWN))
    return _apply_slippage_bps(amount=output_amount, slippage_bps=max_slippage_bps)


def _apply_slippage_bps(*, amount: int, slippage_bps: int) -> int:
    kept_ratio = Decimal(10000 - slippage_bps) / Decimal(10000)
    constrained = Decimal(amount) * kept_ratio
    return int(constrained.to_integral_value(rounding=ROUND_DOWN))


def _compute_max_gas_price_gwei(
    *,
    base_fee_gwei: int,
    priority_fee_gwei: int,
    multiplier: Decimal,
    cap_gwei: int,
) -> int:
    estimated = (Decimal(base_fee_gwei + priority_fee_gwei) * multiplier).to_integral_value(rounding=ROUND_UP)
    return int(min(estimated, Decimal(cap_gwei)))


def _assert_register_payload(payload: RegisterPayload) -> None:
    if payload.entry_amount_out_minimum <= payload.exit_min_out_floor:
        raise ConstraintViolationError(
            "exitMinOutFloor must be strictly lower than entryAmountOutMinimum",
            context={
                "entry_amount_out_minimum": payload.entry_amount_out_minimum,
                "exit_min_out_floor": payload.exit_min_out_floor,
            },
        )
