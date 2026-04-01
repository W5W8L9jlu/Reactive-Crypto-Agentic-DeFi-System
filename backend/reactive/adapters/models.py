from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class ReactivePositionState(str, Enum):
    PENDING_ENTRY = "PendingEntry"
    ACTIVE_POSITION = "ActivePosition"
    CLOSED = "Closed"


class ReactiveTriggerKind(str, Enum):
    ENTRY = "entry"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class ReactiveRegisterPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str
    owner: str
    input_token: str
    output_token: str
    planned_entry_size: PositiveInt
    entry_amount_out_minimum: int = Field(ge=0)
    entry_valid_until: int = Field(ge=0)
    max_gas_price_gwei: int = Field(ge=0)
    stop_loss_slippage_bps: int = Field(ge=0)
    take_profit_slippage_bps: int = Field(ge=0)
    exit_min_out_floor: int = Field(ge=0)


class ReactiveExecutionHardConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_slippage_bps: int = Field(ge=0)
    ttl_seconds: PositiveInt
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)


class ReactiveExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trade_intent_id: str
    register_payload: ReactiveRegisterPayload
    hard_constraints: ReactiveExecutionHardConstraints


class InvestmentStateMachineIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner: str
    input_token: str
    output_token: str
    planned_entry_size: PositiveInt
    entry_min_out: int = Field(ge=0)
    exit_min_out_floor: int = Field(ge=0)


class ReactiveTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str
    kind: ReactiveTriggerKind
    observed_out: int = Field(ge=0)
    runtime_exit_min_out: int | None = Field(default=None, ge=0)

    @property
    def is_exit_trigger(self) -> bool:
        return self.kind in {
            ReactiveTriggerKind.STOP_LOSS,
            ReactiveTriggerKind.TAKE_PROFIT,
        }


@runtime_checkable
class InvestmentPositionStateMachinePort(Protocol):
    def register_investment_intent(self, intent_id: str, intent: InvestmentStateMachineIntent) -> None: ...

    def execute_reactive_trigger(
        self,
        intent_id: str,
        observed_out: int,
        runtime_exit_min_out: int,
    ) -> None: ...

    def get_position_state(self, intent_id: str) -> ReactivePositionState | str: ...
