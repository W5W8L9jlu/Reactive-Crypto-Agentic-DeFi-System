from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True)


class ChainReceipt(BaseModel):
    model_config = _frozen_config()

    tx_hash: str = Field(min_length=1)
    status: Literal["success", "reverted"]
    block_number: int = Field(ge=0)
    gas_used: int = Field(ge=0)
    logs: tuple[dict[str, Any], ...] = ()


class ExecutionRecord(BaseModel):
    model_config = _frozen_config()

    trade_intent_id: str = Field(min_length=1)
    intent_id: str = Field(min_length=1)
    status: Literal["executed"]
    trigger_type: str = Field(min_length=1)
    callback_type: str = Field(min_length=1)
    state_before: str = Field(min_length=1)
    state_after: str = Field(min_length=1)
    callback_ref: str = Field(min_length=1)
    chain_receipt: ChainReceipt
    execution_plan: dict[str, Any]
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @model_validator(mode="after")
    def validate_execution_reference(self) -> "ExecutionRecord":
        if self.callback_ref != self.chain_receipt.tx_hash:
            raise ValueError("callback_ref must equal chain_receipt.tx_hash")
        return self
