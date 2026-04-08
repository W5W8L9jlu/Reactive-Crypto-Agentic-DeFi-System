from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True)


class InvestmentPositionState(str, Enum):
    PENDING_ENTRY = "PendingEntry"
    ACTIVE_POSITION = "ActivePosition"
    CLOSED = "Closed"


class ReactiveTriggerType(str, Enum):
    ENTRY = "entry"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class ReactiveCallbackType(str, Enum):
    ENTRY = "entry_callback"
    EXIT_STOP_LOSS = "exit_stop_loss_callback"
    EXIT_TAKE_PROFIT = "exit_take_profit_callback"


class RegisteredInvestmentIntent(BaseModel):
    model_config = _frozen_config()

    intent_id: str = Field(min_length=1)
    trade_intent_id: str | None = Field(default=None, min_length=1)


class ReactiveTrigger(BaseModel):
    model_config = _frozen_config()

    trigger_type: ReactiveTriggerType
    intent_id: str = Field(min_length=1)
    trade_intent_id: str | None = Field(default=None, min_length=1)
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class CallbackExecutionResult(BaseModel):
    model_config = _frozen_config()

    callback_type: ReactiveCallbackType
    is_executed: bool
    state_after: InvestmentPositionState
    callback_ref: str | None = Field(default=None, min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_callback_reference(self) -> "CallbackExecutionResult":
        if self.is_executed and self.callback_ref is None:
            raise ValueError("callback_ref must be set when is_executed=True")
        return self


class RuntimeAbortReason(BaseModel):
    model_config = _frozen_config()

    code: str
    message: str
    field_path: str | None = None


class ReactiveRuntimeResult(BaseModel):
    model_config = _frozen_config()

    is_executed: bool
    callback_verified: bool
    intent_id: str | None = None
    trade_intent_id: str | None = None
    trigger_type: ReactiveTriggerType | None = None
    callback_type: ReactiveCallbackType | None = None
    state_before: InvestmentPositionState | None = None
    state_after: InvestmentPositionState | None = None
    callback_ref: str | None = None
    abort_reason: RuntimeAbortReason | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "ReactiveRuntimeResult":
        if self.is_executed:
            if self.abort_reason is not None:
                raise ValueError("abort_reason must be empty when is_executed=True")
            if not self.callback_verified:
                raise ValueError("callback_verified must be True when is_executed=True")
        else:
            if self.abort_reason is None:
                raise ValueError("abort_reason must be set when is_executed=False")
        return self
