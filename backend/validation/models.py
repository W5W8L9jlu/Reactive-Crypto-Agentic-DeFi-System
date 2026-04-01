from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError, model_validator

from backend.strategy.models import StrategyIntent, StrategyTemplate, TradeIntent


class ExecutionHardConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_slippage_bps: int = Field(ge=0)
    ttl_seconds: PositiveInt
    stop_loss_bps: int = Field(ge=0)
    take_profit_bps: int = Field(ge=0)


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trade_intent_id: str
    register_payload: dict[str, Any] = Field(min_length=1)
    hard_constraints: ExecutionHardConstraints


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    field_path: str | None = None


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    is_valid: bool
    validated_objects: tuple[str, ...]
    issues: tuple[ValidationIssue, ...] = ()

    @model_validator(mode="after")
    def validate_issue_consistency(self) -> "ValidationResult":
        if self.is_valid and self.issues:
            raise ValueError("issues must be empty when is_valid=True")
        if not self.is_valid and not self.issues:
            raise ValueError("issues must not be empty when is_valid=False")
        return self

    @classmethod
    def from_exception(
        cls,
        *,
        exc: Exception,
        validated_objects: tuple[str, ...],
    ) -> "ValidationResult":
        if isinstance(exc, ValidationError):
            issues = tuple(
                ValidationIssue(
                    code=str(detail["type"]),
                    message=str(detail["msg"]),
                    field_path=".".join(str(item) for item in detail["loc"]),
                )
                for detail in exc.errors()
            )
        else:
            issues = (
                ValidationIssue(
                    code=exc.__class__.__name__,
                    message=str(exc),
                    field_path=None,
                ),
            )
        return cls(is_valid=False, validated_objects=validated_objects, issues=issues)


class ValidationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_template: StrategyTemplate
    strategy_intent: StrategyIntent
    trade_intent: TradeIntent
    execution_plan: ExecutionPlan | None = None

    @model_validator(mode="after")
    def validate_cross_object_constraints(self) -> "ValidationInput":
        if self.strategy_intent.template_id != self.strategy_template.template_id:
            raise ValueError("strategy_intent.template_id must match strategy_template.template_id")

        if self.strategy_intent.template_version != self.strategy_template.version:
            raise ValueError("strategy_intent.template_version must match strategy_template.version")

        if self.strategy_intent.execution_mode != self.strategy_template.execution_mode:
            raise ValueError("strategy_intent.execution_mode must match strategy_template.execution_mode")

        if self.trade_intent.strategy_intent_id != self.strategy_intent.strategy_intent_id:
            raise ValueError("trade_intent.strategy_intent_id must match strategy_intent.strategy_intent_id")

        self._validate_pair_and_dex_whitelist()
        self._validate_trade_hard_bounds()
        self._validate_trade_range_bounds()
        self._validate_execution_plan_binding()
        return self

    def _validate_pair_and_dex_whitelist(self) -> None:
        allowed_pairs = self.strategy_template.auto_allowed_pairs | self.strategy_template.manual_allowed_pairs
        if self.trade_intent.pair not in allowed_pairs:
            raise ValueError("trade_intent.pair is outside strategy_template allowed pairs")

        allowed_dexes = self.strategy_template.auto_allowed_dexes | self.strategy_template.manual_allowed_dexes
        if self.trade_intent.dex not in allowed_dexes:
            raise ValueError("trade_intent.dex is outside strategy_template allowed dexes")

    def _validate_trade_hard_bounds(self) -> None:
        if self.trade_intent.position_usd > self.strategy_template.hard_max_position_usd:
            raise ValueError("trade_intent.position_usd exceeds strategy_template.hard_max_position_usd")

        if self.trade_intent.max_slippage_bps > self.strategy_template.hard_max_slippage_bps:
            raise ValueError("trade_intent.max_slippage_bps exceeds strategy_template.hard_max_slippage_bps")

    def _validate_trade_range_bounds(self) -> None:
        if not self._is_in_stop_loss_range(self.trade_intent.stop_loss_bps):
            raise ValueError("trade_intent.stop_loss_bps is outside strategy_template allowed ranges")

        if not self._is_in_take_profit_range(self.trade_intent.take_profit_bps):
            raise ValueError("trade_intent.take_profit_bps is outside strategy_template allowed ranges")

    def _validate_execution_plan_binding(self) -> None:
        if self.execution_plan is None:
            return

        if self.execution_plan.trade_intent_id != self.trade_intent.trade_intent_id:
            raise ValueError("execution_plan.trade_intent_id must match trade_intent.trade_intent_id")

        if self.execution_plan.hard_constraints.max_slippage_bps > self.trade_intent.max_slippage_bps:
            raise ValueError("execution_plan.hard_constraints.max_slippage_bps cannot be looser than trade_intent")

        if self.execution_plan.hard_constraints.ttl_seconds > self.trade_intent.ttl_seconds:
            raise ValueError("execution_plan.hard_constraints.ttl_seconds cannot be looser than trade_intent")

    def _is_in_stop_loss_range(self, value: int) -> bool:
        return self.strategy_template.auto_stop_loss_bps_range.contains(
            value
        ) or self.strategy_template.manual_stop_loss_bps_range.contains(value)

    def _is_in_take_profit_range(self, value: int) -> bool:
        return self.strategy_template.auto_take_profit_bps_range.contains(
            value
        ) or self.strategy_template.manual_take_profit_bps_range.contains(value)
