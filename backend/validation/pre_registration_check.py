from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError, model_validator

from backend.strategy.models import StrategyIntent, TradeIntent

from .errors import ValidationEngineDomainError


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True)


class PreRegistrationCheckDomainError(ValidationEngineDomainError):
    """Base domain error for registration-time feasibility checks."""


class MissingPreRegistrationSpecError(PreRegistrationCheckDomainError):
    """Raised when current knowledge files do not define a required rule clearly enough."""


class StrategyIntentBindingError(PreRegistrationCheckDomainError):
    """Raised when StrategyIntent and TradeIntent do not belong to the same decision."""


class GasTooHighError(PreRegistrationCheckDomainError):
    """Raised when current RPC gas price exceeds the allowed registration cap."""


class SlippageExceededError(PreRegistrationCheckDomainError):
    """Raised when reserve-derived slippage exceeds the trade intent bound."""


class ExpiredIntentError(PreRegistrationCheckDomainError):
    """Raised when no TTL budget remains after applying the registration buffer."""


class InsufficientBalanceError(PreRegistrationCheckDomainError):
    """Raised when wallet balance cannot fund the required input amount."""


class InsufficientAllowanceError(PreRegistrationCheckDomainError):
    """Raised when wallet allowance cannot fund the required input amount."""


class UnprofitableRegistrationError(PreRegistrationCheckDomainError):
    """Raised when expected profit does not cover the estimated gas cost."""


class HealthFactorTooLowError(PreRegistrationCheckDomainError):
    """Raised when an optional health factor requirement is violated."""


class RPCStateSnapshot(BaseModel):
    """RPC-backed snapshot required to decide if a registration is still feasible."""

    model_config = _frozen_config()

    block_number: PositiveInt
    block_timestamp: PositiveInt
    input_token_usd_price: Decimal = Field(gt=0)
    input_token_reserve: Decimal = Field(gt=0)
    output_token_reserve: Decimal = Field(gt=0)
    wallet_input_balance: Decimal = Field(ge=0)
    wallet_input_allowance: Decimal = Field(ge=0)
    base_fee_gwei: int = Field(ge=0)
    max_priority_fee_gwei: int = Field(ge=0)
    max_gas_price_gwei: int = Field(ge=0)
    estimated_gas_used: PositiveInt
    native_token_usd_price: Decimal = Field(gt=0)
    expected_profit_usd: Decimal = Field(ge=0)
    ttl_buffer_seconds: int = Field(default=0, ge=0)
    health_factor: Decimal | None = Field(default=None, gt=0)
    minimum_health_factor: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_health_factor_requirements(self) -> "RPCStateSnapshot":
        if self.minimum_health_factor is not None and self.health_factor is None:
            raise MissingPreRegistrationSpecError(
                "minimum_health_factor is set but health_factor is missing from the RPC snapshot"
            )
        return self


class PreRegistrationInput(BaseModel):
    """Strongly typed input bundle for registration-time feasibility checks."""

    model_config = _frozen_config()

    strategy_intent: StrategyIntent
    trade_intent: TradeIntent
    rpc_state_snapshot: RPCStateSnapshot

    @model_validator(mode="after")
    def validate_strategy_binding(self) -> "PreRegistrationInput":
        if self.trade_intent.strategy_intent_id != self.strategy_intent.strategy_intent_id:
            raise StrategyIntentBindingError(
                "trade_intent.strategy_intent_id must match strategy_intent.strategy_intent_id"
            )
        return self


class AbortReason(BaseModel):
    model_config = _frozen_config()

    code: str
    message: str
    field_path: str | None = None


class PreRegistrationCheckObservations(BaseModel):
    model_config = _frozen_config()

    required_input_amount: Decimal = Field(gt=0)
    quoted_output_amount: Decimal = Field(gt=0)
    spot_output_amount: Decimal = Field(gt=0)
    observed_slippage_bps: Decimal = Field(ge=0)
    input_token_reserve: Decimal = Field(gt=0)
    output_token_reserve: Decimal = Field(gt=0)
    wallet_input_balance: Decimal = Field(ge=0)
    wallet_input_allowance: Decimal = Field(ge=0)
    current_gas_price_gwei: int = Field(ge=0)
    max_gas_price_gwei: int = Field(ge=0)
    estimated_gas_cost_usd: Decimal = Field(ge=0)
    expected_profit_usd: Decimal = Field(ge=0)
    profit_to_gas_ratio: Decimal | None = None
    ttl_seconds: PositiveInt
    ttl_buffer_seconds: int = Field(ge=0)
    remaining_ttl_seconds: int
    health_factor: Decimal | None = Field(default=None, gt=0)


class PreRegistrationCheckResult(BaseModel):
    model_config = _frozen_config()

    is_allowed: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    strategy_intent_id: str | None = None
    trade_intent_id: str | None = None
    checked_objects: tuple[str, ...] = ("StrategyIntent", "TradeIntent", "RPCStateSnapshot")
    observations: PreRegistrationCheckObservations | None = None
    abort_reason: AbortReason | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "PreRegistrationCheckResult":
        if self.is_allowed and self.abort_reason is not None:
            raise ValueError("abort_reason must be empty when is_allowed=True")
        if not self.is_allowed and self.abort_reason is None:
            raise ValueError("abort_reason must be set when is_allowed=False")
        return self

    @classmethod
    def from_exception(
        cls,
        *,
        exc: Exception,
        strategy_intent: StrategyIntent | dict[str, Any],
        trade_intent: TradeIntent | dict[str, Any],
    ) -> "PreRegistrationCheckResult":
        if isinstance(exc, ValidationError):
            detail = exc.errors()[0]
            abort_reason = AbortReason(
                code=str(detail["type"]),
                message=str(detail["msg"]),
                field_path=".".join(str(item) for item in detail["loc"]),
            )
        else:
            abort_reason = AbortReason(
                code=exc.__class__.__name__,
                message=str(exc),
                field_path=None,
            )
        return cls(
            is_allowed=False,
            strategy_intent_id=_extract_identifier(strategy_intent, "strategy_intent_id"),
            trade_intent_id=_extract_identifier(trade_intent, "trade_intent_id"),
            abort_reason=abort_reason,
        )


def run_pre_registration_check_or_raise(
    *,
    strategy_intent: StrategyIntent | dict[str, Any],
    trade_intent: TradeIntent | dict[str, Any],
    rpc_state_snapshot: RPCStateSnapshot | dict[str, Any],
) -> PreRegistrationCheckResult:
    parsed_input = _parse_input(
        strategy_intent=strategy_intent,
        trade_intent=trade_intent,
        rpc_state_snapshot=rpc_state_snapshot,
    )
    observations = _build_observations(parsed_input)
    _assert_ttl_is_live(observations)
    _assert_wallet_can_fund(observations)
    _assert_gas_is_acceptable(observations)
    _assert_slippage_is_acceptable(
        observed_slippage_bps=observations.observed_slippage_bps,
        max_slippage_bps=parsed_input.trade_intent.max_slippage_bps,
    )
    _assert_registration_is_profitable(observations)
    _assert_health_factor_is_safe(
        health_factor=observations.health_factor,
        minimum_health_factor=parsed_input.rpc_state_snapshot.minimum_health_factor,
    )
    return PreRegistrationCheckResult(
        is_allowed=True,
        strategy_intent_id=parsed_input.strategy_intent.strategy_intent_id,
        trade_intent_id=parsed_input.trade_intent.trade_intent_id,
        observations=observations,
    )


def run_pre_registration_check(
    *,
    strategy_intent: StrategyIntent | dict[str, Any],
    trade_intent: TradeIntent | dict[str, Any],
    rpc_state_snapshot: RPCStateSnapshot | dict[str, Any],
) -> PreRegistrationCheckResult:
    try:
        return run_pre_registration_check_or_raise(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            rpc_state_snapshot=rpc_state_snapshot,
        )
    except (ValidationError, PreRegistrationCheckDomainError) as exc:
        return PreRegistrationCheckResult.from_exception(
            exc=exc,
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
        )


def _parse_input(
    *,
    strategy_intent: StrategyIntent | dict[str, Any],
    trade_intent: TradeIntent | dict[str, Any],
    rpc_state_snapshot: RPCStateSnapshot | dict[str, Any],
) -> PreRegistrationInput:
    return PreRegistrationInput.model_validate(
        {
            "strategy_intent": strategy_intent,
            "trade_intent": trade_intent,
            "rpc_state_snapshot": rpc_state_snapshot,
        }
    )


def _build_observations(parsed_input: PreRegistrationInput) -> PreRegistrationCheckObservations:
    trade_intent = parsed_input.trade_intent
    snapshot = parsed_input.rpc_state_snapshot

    required_input_amount = trade_intent.position_usd / snapshot.input_token_usd_price
    quoted_output_amount = _compute_constant_product_quote(
        input_amount=required_input_amount,
        input_reserve=snapshot.input_token_reserve,
        output_reserve=snapshot.output_token_reserve,
    )
    spot_output_amount = required_input_amount * (
        snapshot.output_token_reserve / snapshot.input_token_reserve
    )
    observed_slippage_bps = _compute_slippage_bps(
        quoted_output_amount=quoted_output_amount,
        spot_output_amount=spot_output_amount,
    )
    current_gas_price_gwei = snapshot.base_fee_gwei + snapshot.max_priority_fee_gwei
    estimated_gas_cost_usd = _compute_gas_cost_usd(
        current_gas_price_gwei=current_gas_price_gwei,
        estimated_gas_used=snapshot.estimated_gas_used,
        native_token_usd_price=snapshot.native_token_usd_price,
    )
    profit_to_gas_ratio = _compute_profit_to_gas_ratio(
        expected_profit_usd=snapshot.expected_profit_usd,
        estimated_gas_cost_usd=estimated_gas_cost_usd,
    )
    remaining_ttl_seconds = int(trade_intent.ttl_seconds) - int(snapshot.ttl_buffer_seconds)

    return PreRegistrationCheckObservations(
        required_input_amount=required_input_amount,
        quoted_output_amount=quoted_output_amount,
        spot_output_amount=spot_output_amount,
        observed_slippage_bps=observed_slippage_bps,
        input_token_reserve=snapshot.input_token_reserve,
        output_token_reserve=snapshot.output_token_reserve,
        wallet_input_balance=snapshot.wallet_input_balance,
        wallet_input_allowance=snapshot.wallet_input_allowance,
        current_gas_price_gwei=current_gas_price_gwei,
        max_gas_price_gwei=snapshot.max_gas_price_gwei,
        estimated_gas_cost_usd=estimated_gas_cost_usd,
        expected_profit_usd=snapshot.expected_profit_usd,
        profit_to_gas_ratio=profit_to_gas_ratio,
        ttl_seconds=trade_intent.ttl_seconds,
        ttl_buffer_seconds=snapshot.ttl_buffer_seconds,
        remaining_ttl_seconds=remaining_ttl_seconds,
        health_factor=snapshot.health_factor,
    )


def _compute_constant_product_quote(
    *,
    input_amount: Decimal,
    input_reserve: Decimal,
    output_reserve: Decimal,
) -> Decimal:
    return (output_reserve * input_amount) / (input_reserve + input_amount)


def _compute_slippage_bps(
    *,
    quoted_output_amount: Decimal,
    spot_output_amount: Decimal,
) -> Decimal:
    if spot_output_amount <= 0:
        raise MissingPreRegistrationSpecError("spot output amount must stay positive for slippage checks")
    slippage_fraction = Decimal("1") - (quoted_output_amount / spot_output_amount)
    if slippage_fraction < 0:
        slippage_fraction = Decimal("0")
    return slippage_fraction * Decimal("10000")


def _compute_gas_cost_usd(
    *,
    current_gas_price_gwei: int,
    estimated_gas_used: int,
    native_token_usd_price: Decimal,
) -> Decimal:
    gas_price_native = Decimal(current_gas_price_gwei) * Decimal("1e-9")
    return gas_price_native * Decimal(estimated_gas_used) * native_token_usd_price


def _compute_profit_to_gas_ratio(
    *,
    expected_profit_usd: Decimal,
    estimated_gas_cost_usd: Decimal,
) -> Decimal | None:
    if estimated_gas_cost_usd == 0:
        return None
    return expected_profit_usd / estimated_gas_cost_usd


def _assert_ttl_is_live(observations: PreRegistrationCheckObservations) -> None:
    if observations.remaining_ttl_seconds <= 0:
        raise ExpiredIntentError(
            "trade_intent.ttl_seconds is exhausted after applying rpc_state_snapshot.ttl_buffer_seconds"
        )


def _assert_wallet_can_fund(observations: PreRegistrationCheckObservations) -> None:
    if observations.wallet_input_balance < observations.required_input_amount:
        raise InsufficientBalanceError(
            "wallet_input_balance is below the input amount required by trade_intent.position_usd"
        )
    if observations.wallet_input_allowance < observations.required_input_amount:
        raise InsufficientAllowanceError(
            "wallet_input_allowance is below the input amount required by trade_intent.position_usd"
        )


def _assert_gas_is_acceptable(observations: PreRegistrationCheckObservations) -> None:
    if observations.current_gas_price_gwei > observations.max_gas_price_gwei:
        raise GasTooHighError(
            "current gas price exceeds rpc_state_snapshot.max_gas_price_gwei"
        )


def _assert_slippage_is_acceptable(
    *,
    observed_slippage_bps: Decimal,
    max_slippage_bps: int,
) -> None:
    if observed_slippage_bps > Decimal(max_slippage_bps):
        raise SlippageExceededError(
            "reserve-derived slippage exceeds trade_intent.max_slippage_bps"
        )


def _assert_registration_is_profitable(observations: PreRegistrationCheckObservations) -> None:
    if observations.estimated_gas_cost_usd > observations.expected_profit_usd:
        raise UnprofitableRegistrationError(
            "expected_profit_usd does not cover the estimated RPC gas cost"
        )


def _assert_health_factor_is_safe(
    *,
    health_factor: Decimal | None,
    minimum_health_factor: Decimal | None,
) -> None:
    if minimum_health_factor is None:
        return
    if health_factor is None:
        raise MissingPreRegistrationSpecError(
            "minimum_health_factor cannot be enforced without health_factor"
        )
    if health_factor < minimum_health_factor:
        raise HealthFactorTooLowError(
            "health_factor is below rpc_state_snapshot.minimum_health_factor"
        )


def _extract_identifier(model_or_dict: StrategyIntent | TradeIntent | dict[str, Any], field_name: str) -> str | None:
    if isinstance(model_or_dict, dict):
        value = model_or_dict.get(field_name)
    else:
        value = getattr(model_or_dict, field_name, None)
    if isinstance(value, str) and value:
        return value
    return None


__all__ = [
    "AbortReason",
    "ExpiredIntentError",
    "GasTooHighError",
    "HealthFactorTooLowError",
    "InsufficientAllowanceError",
    "InsufficientBalanceError",
    "MissingPreRegistrationSpecError",
    "PreRegistrationCheckDomainError",
    "PreRegistrationCheckObservations",
    "PreRegistrationCheckResult",
    "RPCStateSnapshot",
    "SlippageExceededError",
    "UnprofitableRegistrationError",
    "run_pre_registration_check",
    "run_pre_registration_check_or_raise",
]
