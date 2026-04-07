from __future__ import annotations

from typing import Iterable

from .errors import IntentLinkError, MissingBoundaryRuleError, TemplateNotFoundError
from .models import (
    BoundaryDecision,
    BoundaryDecisionResult,
    ContractBindingHint,
    RuleDecision,
    RuleEvaluationTrace,
    StrategyIntent,
    StrategyTemplate,
    TradeIntent,
)


DECISION_PRIORITY = {
    RuleDecision.AUTO: 0,
    RuleDecision.MANUAL: 1,
    RuleDecision.REJECT: 2,
}


class StrategyBoundaryService:
    """Template version and rule boundary service for strategy/trade intent triage."""

    def __init__(self, templates: Iterable[StrategyTemplate] | None = None) -> None:
        self._templates: dict[tuple[str, int], StrategyTemplate] = {}
        self._latest_version_by_template_id: dict[str, int] = {}
        for template in templates or []:
            self.register_template(template)

    def register_template(self, template: StrategyTemplate) -> None:
        key = (template.template_id, int(template.version))
        self._templates[key] = template
        current_latest = self._latest_version_by_template_id.get(template.template_id, 0)
        if int(template.version) > current_latest:
            self._latest_version_by_template_id[template.template_id] = int(template.version)

    def get_template(self, template_id: str, version: int) -> StrategyTemplate:
        template = self._templates.get((template_id, version))
        if template is None:
            raise TemplateNotFoundError(f"Template not found: template_id={template_id}, version={version}")
        return template

    def get_latest_version(self, template_id: str) -> int:
        latest = self._latest_version_by_template_id.get(template_id)
        if latest is None:
            raise TemplateNotFoundError(f"Template ID not found: template_id={template_id}")
        return latest

    def evaluate(self, strategy_intent: StrategyIntent, trade_intent: TradeIntent) -> BoundaryDecisionResult:
        self._validate_intent_link(strategy_intent, trade_intent)

        template = self.get_template(strategy_intent.template_id, int(strategy_intent.template_version))
        self._validate_required_boundary_rules(template)

        traces: list[RuleEvaluationTrace] = []

        latest_version = self.get_latest_version(strategy_intent.template_id)
        traces.append(self._evaluate_version_boundary(strategy_intent.template_version, latest_version))
        traces.append(
            self._evaluate_exact_match(
                rule_name="execution_mode",
                observed=strategy_intent.execution_mode,
                expected=template.execution_mode,
            )
        )
        traces.append(
            self._evaluate_allowlist(
                rule_name="pair",
                observed=trade_intent.pair,
                auto_values=template.auto_allowed_pairs,
                manual_values=template.manual_allowed_pairs,
            )
        )
        traces.append(
            self._evaluate_allowlist(
                rule_name="dex",
                observed=trade_intent.dex,
                auto_values=template.auto_allowed_dexes,
                manual_values=template.manual_allowed_dexes,
            )
        )
        traces.append(
            self._evaluate_auto_manual_reject_by_max(
                rule_name="position_usd",
                observed=trade_intent.position_usd,
                auto_max=template.auto_max_position_usd,
                hard_max=template.hard_max_position_usd,
            )
        )
        traces.append(
            self._evaluate_auto_manual_reject_by_max(
                rule_name="max_slippage_bps",
                observed=trade_intent.max_slippage_bps,
                auto_max=template.auto_max_slippage_bps,
                hard_max=template.hard_max_slippage_bps,
            )
        )
        traces.append(
            self._evaluate_range(
                rule_name="stop_loss_bps",
                observed=trade_intent.stop_loss_bps,
                auto_range=template.auto_stop_loss_bps_range,
                manual_range=template.manual_stop_loss_bps_range,
            )
        )
        traces.append(
            self._evaluate_range(
                rule_name="take_profit_bps",
                observed=trade_intent.take_profit_bps,
                auto_range=template.auto_take_profit_bps_range,
                manual_range=template.manual_take_profit_bps_range,
            )
        )
        traces.append(
            self._evaluate_auto_manual_reject_by_max(
                rule_name="projected_daily_trade_count",
                observed=strategy_intent.projected_daily_trade_count,
                auto_max=template.auto_daily_trade_limit,
                hard_max=template.hard_daily_trade_limit,
            )
        )

        boundary_decision = self._collapse_to_boundary_decision(traces)

        return BoundaryDecisionResult(
            strategy_intent_id=strategy_intent.strategy_intent_id,
            trade_intent_id=trade_intent.trade_intent_id,
            template_id=template.template_id,
            template_version=int(template.version),
            boundary_decision=boundary_decision,
            trace=traces,
            contract_binding_hints=self._build_contract_binding_hints(),
        )

    @staticmethod
    def _build_contract_binding_hints() -> tuple[ContractBindingHint, ...]:
        return (
            ContractBindingHint(
                source_field="trade_intent.position_usd",
                target_field="investment_intent.plannedEntrySize",
                binding_kind="compiler_derived",
                unit="usd_notional",
                owner="execution_compiler",
                note="Execution compiler must derive plannedEntrySize from position_usd at registration time.",
            ),
            ContractBindingHint(
                source_field="trade_intent.max_slippage_bps",
                target_field="investment_intent.entryMinOut",
                binding_kind="compiler_derived",
                unit="bps",
                owner="execution_compiler",
                note="Execution compiler must derive entryMinOut from registration-time quotes plus max_slippage_bps.",
            ),
            ContractBindingHint(
                source_field="trade_intent.stop_loss_bps",
                target_field="runtime_exit_policy.stop_loss_bps",
                binding_kind="runtime_derived",
                unit="bps",
                owner="reactive_runtime",
                note="Runtime exit policy must consume stop_loss_bps without moving execution decisions into this module.",
            ),
            ContractBindingHint(
                source_field="trade_intent.take_profit_bps",
                target_field="runtime_exit_policy.take_profit_bps",
                binding_kind="runtime_derived",
                unit="bps",
                owner="reactive_runtime",
                note="Runtime exit policy must consume take_profit_bps without moving execution decisions into this module.",
            ),
            ContractBindingHint(
                source_field="trade_intent.ttl_seconds",
                target_field="execution_plan.hard_constraints.ttl_seconds",
                binding_kind="compiler_derived",
                unit="seconds",
                owner="execution_compiler",
                note="TTL stays in seconds and must be enforced by the registration-time execution plan.",
            ),
        )

    @staticmethod
    def _validate_intent_link(strategy_intent: StrategyIntent, trade_intent: TradeIntent) -> None:
        if strategy_intent.strategy_intent_id != trade_intent.strategy_intent_id:
            raise IntentLinkError(
                "StrategyIntent and TradeIntent are not linkable by strategy_intent_id"
            )

    @staticmethod
    def _validate_required_boundary_rules(template: StrategyTemplate) -> None:
        if not template.auto_allowed_pairs and not template.manual_allowed_pairs:
            raise MissingBoundaryRuleError("TODO: pair boundary rule is not defined in template")
        if not template.auto_allowed_dexes and not template.manual_allowed_dexes:
            raise MissingBoundaryRuleError("TODO: dex boundary rule is not defined in template")

    @staticmethod
    def _evaluate_version_boundary(intent_version: int, latest_version: int) -> RuleEvaluationTrace:
        if intent_version == latest_version:
            return RuleEvaluationTrace(
                rule_name="template_version_boundary",
                decision=RuleDecision.AUTO,
                observed={"intent_version": intent_version, "latest_version": latest_version},
                note="intent uses the latest template version",
            )
        return RuleEvaluationTrace(
            rule_name="template_version_boundary",
            decision=RuleDecision.MANUAL,
            observed={"intent_version": intent_version, "latest_version": latest_version},
            note="intent uses a non-latest but existing template version",
        )

    @staticmethod
    def _evaluate_exact_match(rule_name: str, observed: str, expected: str) -> RuleEvaluationTrace:
        if observed == expected:
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.AUTO,
                observed=observed,
                note=f"matches expected value: {expected}",
            )
        return RuleEvaluationTrace(
            rule_name=rule_name,
            decision=RuleDecision.REJECT,
            observed=observed,
            note=f"value does not match expected: {expected}",
        )

    @staticmethod
    def _evaluate_allowlist(
        rule_name: str,
        observed: str,
        auto_values: set[str] | frozenset[str],
        manual_values: set[str] | frozenset[str],
    ) -> RuleEvaluationTrace:
        if observed in auto_values:
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.AUTO,
                observed=observed,
                note="value is inside auto boundary",
            )
        if observed in manual_values:
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.MANUAL,
                observed=observed,
                note="value is outside auto boundary but inside manual boundary",
            )
        return RuleEvaluationTrace(
            rule_name=rule_name,
            decision=RuleDecision.REJECT,
            observed=observed,
            note="value is outside template boundary",
        )

    @staticmethod
    def _evaluate_auto_manual_reject_by_max(
        rule_name: str,
        observed: int | float | str,
        auto_max: int | float | str,
        hard_max: int | float | str,
    ) -> RuleEvaluationTrace:
        if observed <= auto_max:
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.AUTO,
                observed=observed,
                note=f"value <= auto boundary ({auto_max})",
            )
        if observed <= hard_max:
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.MANUAL,
                observed=observed,
                note=f"value > auto boundary ({auto_max}) but <= hard boundary ({hard_max})",
            )
        return RuleEvaluationTrace(
            rule_name=rule_name,
            decision=RuleDecision.REJECT,
            observed=observed,
            note=f"value > hard boundary ({hard_max})",
        )

    @staticmethod
    def _evaluate_range(rule_name: str, observed: int, auto_range, manual_range) -> RuleEvaluationTrace:
        if auto_range.contains(observed):
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.AUTO,
                observed=observed,
                note=f"value in auto range [{auto_range.min_bps}, {auto_range.max_bps}]",
            )
        if manual_range.contains(observed):
            return RuleEvaluationTrace(
                rule_name=rule_name,
                decision=RuleDecision.MANUAL,
                observed=observed,
                note=(
                    f"value in manual range [{manual_range.min_bps}, {manual_range.max_bps}] "
                    f"but outside auto range"
                ),
            )
        return RuleEvaluationTrace(
            rule_name=rule_name,
            decision=RuleDecision.REJECT,
            observed=observed,
            note=(
                f"value outside manual range [{manual_range.min_bps}, {manual_range.max_bps}] "
                "and outside auto range"
            ),
        )

    @staticmethod
    def _collapse_to_boundary_decision(trace: list[RuleEvaluationTrace]) -> BoundaryDecision:
        highest = RuleDecision.AUTO
        for rule_trace in trace:
            if DECISION_PRIORITY[rule_trace.decision] > DECISION_PRIORITY[highest]:
                highest = rule_trace.decision

        if highest == RuleDecision.REJECT:
            return BoundaryDecision.REJECT
        if highest == RuleDecision.MANUAL:
            return BoundaryDecision.MANUAL_APPROVAL
        return BoundaryDecision.AUTO_REGISTER
