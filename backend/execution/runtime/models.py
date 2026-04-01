from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator


def _require_timezone_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc)


class RuntimeTrigger(BaseModel):
    """
    Reactive 运行时触发结果。

    TODO: docs 目前未定义更细粒度 trigger schema，当前仅保留执行层闭环所需字段。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    trigger_id: str = Field(min_length=1)
    trade_intent_id: str = Field(min_length=1)
    trigger_source: str = Field(min_length=1)
    triggered_at: datetime
    onchain_checks_passed: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    _validate_triggered_at = field_validator("triggered_at")(_require_timezone_aware)


class ChainReceipt(BaseModel):
    """
    执行层消费并落库的最小链上回执。

    字段仅保留链上可证明的 receipt 数据，不脑补业务语义。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_hash: str = Field(min_length=1)
    block_number: PositiveInt
    gas_used: int = Field(ge=0)
    status: int = Field(ge=0, le=1)
    logs: list[dict[str, Any]] = Field(default_factory=list)
    effective_gas_price_wei: int | None = Field(default=None, ge=0)
    revert_reason: str | None = None


class ExecutionRecord(BaseModel):
    """
    Execution Layer 的结构化执行记录。

    TODO: Domain Models 未给出正式 ExecutionRecord schema；当前模型保持最小可追溯闭环：
    计划标识 + trigger 标识 + receipt + 成败状态。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    trade_intent_id: str = Field(min_length=1)
    intent_id: str = Field(min_length=1)
    trigger_id: str = Field(min_length=1)
    trigger_source: str = Field(min_length=1)
    triggered_at: datetime
    executed_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    execution_status: Literal["succeeded", "failed"]
    receipt: ChainReceipt

    _validate_triggered_at = field_validator("triggered_at")(_require_timezone_aware)
    _validate_executed_at = field_validator("executed_at")(_require_timezone_aware)


RuntimeTrigger.model_rebuild()
ChainReceipt.model_rebuild()
ExecutionRecord.model_rebuild()
