from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from backend.strategy.models import StrategyIntent, TradeIntent


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ContractInvestmentIntent(BaseModel):
    """Contract-facing `InvestmentIntent` payload."""

    model_config = _frozen_config()

    owner: str = Field(min_length=1)
    input_token: str = Field(min_length=1, alias="inputToken")
    output_token: str = Field(min_length=1, alias="outputToken")
    planned_entry_size: PositiveInt = Field(alias="plannedEntrySize")
    entry_min_out: PositiveInt = Field(alias="entryMinOut")
    entry_valid_until: PositiveInt = Field(alias="entryValidUntil")
    max_gas_price_gwei: int = Field(ge=0, alias="maxGasPriceGwei")
    stop_loss_slippage_bps: int = Field(ge=0, le=10_000, alias="stopLossSlippageBps")
    take_profit_slippage_bps: int = Field(ge=0, le=10_000, alias="takeProfitSlippageBps")


class ContractRegisterCallInputs(BaseModel):
    """Frozen inputs for `registerInvestmentIntent(intentId, intent)`."""

    model_config = _frozen_config()

    intent_id: str = Field(min_length=1, alias="intentId")
    intent: ContractInvestmentIntent


class RegisterPayload(BaseModel):
    """Registration-time payload frozen by the execution compiler."""

    model_config = _frozen_config()

    intent_id: str = Field(min_length=1, alias="intentId")
    owner: str = Field(min_length=1)
    input_token: str = Field(min_length=1, alias="inputToken")
    output_token: str = Field(min_length=1, alias="outputToken")
    planned_entry_size: PositiveInt = Field(alias="plannedEntrySize")
    entry_amount_out_minimum: PositiveInt = Field(alias="entryAmountOutMinimum")
    entry_valid_until: PositiveInt = Field(alias="entryValidUntil")
    max_gas_price_gwei: int = Field(ge=0, alias="maxGasPriceGwei")
    stop_loss_slippage_bps: int = Field(ge=0, le=10_000, alias="stopLossSlippageBps")
    take_profit_slippage_bps: int = Field(ge=0, le=10_000, alias="takeProfitSlippageBps")

    def as_contract_call_inputs(self) -> ContractRegisterCallInputs:
        return ContractRegisterCallInputs(
            intent_id=self.intent_id,
            intent=ContractInvestmentIntent(
                owner=self.owner,
                input_token=self.input_token,
                output_token=self.output_token,
                planned_entry_size=self.planned_entry_size,
                entry_min_out=self.entry_amount_out_minimum,
                entry_valid_until=self.entry_valid_until,
                max_gas_price_gwei=self.max_gas_price_gwei,
                stop_loss_slippage_bps=self.stop_loss_slippage_bps,
                take_profit_slippage_bps=self.take_profit_slippage_bps,
            ),
        )


class ExecutionHardConstraints(BaseModel):
    model_config = _frozen_config()

    max_slippage_bps: int = Field(ge=0)
    ttl_seconds: PositiveInt
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)


class ExecutionPlan(BaseModel):
    model_config = _frozen_config()

    trade_intent_id: str
    register_payload: RegisterPayload
    hard_constraints: ExecutionHardConstraints
    compiled_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    compiler_version: str = Field(default="1.0.0")


class ChainStateSnapshot(BaseModel):
    model_config = _frozen_config()

    base_fee_gwei: int = Field(ge=0)
    max_priority_fee_gwei: int = Field(ge=0)
    block_number: PositiveInt
    block_timestamp: PositiveInt
    input_token_decimals: int = Field(ge=0, le=18)
    output_token_decimals: int = Field(ge=0, le=18)
    input_output_price: Decimal = Field(gt=0)
    input_token_usd_price: Decimal = Field(gt=0)


class CompilerConfig(BaseModel):
    model_config = _frozen_config()

    gas_buffer_multiplier: Decimal = Field(default=Decimal("1.2"), gt=1)
    max_gas_price_cap_gwei: int = Field(default=500, ge=0)
    ttl_buffer_seconds: int = Field(default=60, ge=0)
    slippage_tolerance_buffer_bps: int = Field(default=10, ge=0)


class RegistrationContext(BaseModel):
    """Explicit registration metadata that upstream strategy artifacts do not own."""

    model_config = _frozen_config()

    intent_id: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    input_token: str = Field(min_length=1)
    output_token: str = Field(min_length=1)


class CompilationContext(BaseModel):
    model_config = _frozen_config()

    strategy_intent: StrategyIntent
    trade_intent: TradeIntent
    chain_state: ChainStateSnapshot
    registration_context: RegistrationContext
    config: CompilerConfig = Field(default_factory=CompilerConfig)
