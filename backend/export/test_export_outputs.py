import json
import os
import re
import sys
import unittest
from decimal import Decimal

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.dirname(__file__))

from backend.execution.compiler import compile_execution_plan, freeze_contract_call_inputs
from backend.execution.compiler.models import ChainStateSnapshot, CompilationContext, RegistrationContext
from backend.strategy.models import BpsRange, StrategyIntent, StrategyTemplate, TradeIntent
from backend.strategy.strategy_boundary_service import StrategyBoundaryService
from backend.validation import validate_inputs_or_raise
from backend.validation.models import ExecutionPlan
from export_outputs import (
    DecisionArtifact,
    ExecutionRecord,
    ExportDomainError,
    export_outputs,
)


def _flatten_json_leaves(value, pointer=""):
    if isinstance(value, dict):
        if not value:
            return {pointer or "/": {}}
        out = {}
        for key in sorted(value.keys()):
            child_pointer = f"{pointer}/{key}"
            out.update(_flatten_json_leaves(value[key], child_pointer))
        return out
    if isinstance(value, list):
        if not value:
            return {pointer or "/": []}
        out = {}
        for idx, item in enumerate(value):
            child_pointer = f"{pointer}/{idx}"
            out.update(_flatten_json_leaves(item, child_pointer))
        return out
    return {pointer or "/": value}


def _read_audit_excerpt(markdown):
    match = re.search(r"```machine-truth-excerpt\n(.*?)\n```", markdown, flags=re.S)
    assert match, "Audit markdown must contain machine-truth-excerpt code block."
    excerpt = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        pointer, raw_json = line.split("\t", maxsplit=1)
        excerpt[pointer] = json.loads(raw_json)
    return excerpt


def _resolve_pointer(document, pointer):
    current = document
    segments = [seg for seg in pointer.split("/") if seg]
    for seg in segments:
        if isinstance(current, list):
            current = current[int(seg)]
        else:
            current = current[seg]
    return current


class ExportOutputsTestCase(unittest.TestCase):
    def test_export_outputs_accepts_canonical_wave1_happy_path_artifacts(self):
        strategy_template = StrategyTemplate(
            template_id="tpl-eth-swing",
            version=1,
            auto_allowed_pairs=frozenset({"ETH/USDC"}),
            manual_allowed_pairs=frozenset({"WBTC/USDC"}),
            auto_allowed_dexes=frozenset({"uniswap_v3"}),
            manual_allowed_dexes=frozenset({"curve"}),
            auto_max_position_usd=Decimal("5000"),
            hard_max_position_usd=Decimal("10000"),
            auto_max_slippage_bps=30,
            hard_max_slippage_bps=80,
            auto_stop_loss_bps_range=BpsRange(min_bps=50, max_bps=200),
            manual_stop_loss_bps_range=BpsRange(min_bps=10, max_bps=400),
            auto_take_profit_bps_range=BpsRange(min_bps=100, max_bps=500),
            manual_take_profit_bps_range=BpsRange(min_bps=50, max_bps=1000),
            auto_daily_trade_limit=2,
            hard_daily_trade_limit=8,
            execution_mode="conditional",
        )
        strategy_intent = StrategyIntent(
            strategy_intent_id="si-001",
            template_id="tpl-eth-swing",
            template_version=1,
            execution_mode="conditional",
            projected_daily_trade_count=1,
        )
        trade_intent = TradeIntent(
            trade_intent_id="ti-001",
            strategy_intent_id="si-001",
            pair="ETH/USDC",
            dex="uniswap_v3",
            position_usd=Decimal("1200"),
            max_slippage_bps=20,
            stop_loss_bps=90,
            take_profit_bps=250,
            entry_conditions=["price_below:3000"],
            ttl_seconds=3600,
        )
        boundary_result = StrategyBoundaryService([strategy_template]).evaluate(strategy_intent, trade_intent)
        execution_plan_model = compile_execution_plan(
            CompilationContext(
                strategy_intent=strategy_intent,
                trade_intent=trade_intent,
                chain_state=ChainStateSnapshot(
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    block_number=20_000_000,
                    block_timestamp=1_710_000_000,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "1" * 64,
                    owner="0x0000000000000000000000000000000000000001",
                    input_token="0x0000000000000000000000000000000000000002",
                    output_token="0x0000000000000000000000000000000000000003",
                ),
            )
        )
        execution_plan = ExecutionPlan.model_validate(execution_plan_model.model_dump(mode="python", by_alias=True))
        validation_result = validate_inputs_or_raise(
            strategy_template=strategy_template.model_dump(mode="python"),
            strategy_intent=strategy_intent.model_dump(mode="python"),
            trade_intent=trade_intent.model_dump(mode="python"),
            execution_plan=execution_plan.model_dump(mode="python"),
        )

        outputs = export_outputs(
            decision_artifact=DecisionArtifact.model_validate(
                {
                    "boundary_result": boundary_result.model_dump(mode="python"),
                    "validation_result": validation_result.model_dump(mode="python"),
                }
            ),
            execution_record=ExecutionRecord.model_validate(
                {
                    "execution_plan": execution_plan.model_dump(mode="python"),
                    "contract_call_inputs": freeze_contract_call_inputs(execution_plan_model).model_dump(
                        mode="python",
                        by_alias=True,
                    ),
                    "status": "validated",
                }
            ),
        )

        machine_truth_doc = json.loads(outputs.machine_truth_json)

        self.assertEqual(
            machine_truth_doc["decision_artifact"]["validation_result"]["validated_objects"],
            ["StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan"],
        )
        self.assertEqual(
            machine_truth_doc["execution_record"]["execution_plan"]["hard_constraints"]["ttl_seconds"],
            3540,
        )
        self.assertEqual(
            machine_truth_doc["execution_record"]["contract_call_inputs"],
            {
                "intentId": "0x" + "1" * 64,
                "intent": {
                    "owner": "0x0000000000000000000000000000000000000001",
                    "inputToken": "0x0000000000000000000000000000000000000002",
                    "outputToken": "0x0000000000000000000000000000000000000003",
                    "plannedEntrySize": 1200000000,
                    "entryMinOut": 599400000000000000,
                    "exitMinOutFloor": 594005400000000000,
                },
            },
        )

    def test_audit_excerpt_is_1_to_1_traceable_to_machine_truth_json(self):
        decision_artifact = DecisionArtifact.model_validate(
            {
                "strategy_intent": {"thesis": "accumulate", "risk_label": "medium"},
                "conclusion": "WAIT_FOR_TRIGGER",
                "agent_trace": [{"step": "analyze", "score": 0.78}],
            }
        )
        execution_record = ExecutionRecord.model_validate(
            {
                "status": "registered",
                "plan_id": "plan-001",
                "constraints": {"max_slippage_bps": 30, "ttl_minutes": 120},
            }
        )

        outputs = export_outputs(
            decision_artifact=decision_artifact,
            execution_record=execution_record,
        )

        machine_truth_doc = json.loads(outputs.machine_truth_json)
        audit_excerpt = _read_audit_excerpt(outputs.audit_markdown)
        expected_excerpt = _flatten_json_leaves(machine_truth_doc)

        self.assertEqual(audit_excerpt, expected_excerpt)
        self.assertEqual(
            _resolve_pointer(machine_truth_doc, "/decision_artifact/conclusion"),
            "WAIT_FOR_TRIGGER",
        )
        self.assertIn('"WAIT_FOR_TRIGGER"', outputs.audit_markdown)

    def test_investment_memo_must_not_pollute_machine_truth(self):
        raw_decision = {"conclusion": "NO_TRADE"}
        raw_execution = {"status": "skipped"}
        decision_artifact = DecisionArtifact.model_validate(raw_decision)
        execution_record = ExecutionRecord.model_validate(raw_execution)

        outputs = export_outputs(
            decision_artifact=decision_artifact,
            execution_record=execution_record,
            memo_brief="仅用于投研讨论，不可执行。",
        )

        machine_truth_doc = json.loads(outputs.machine_truth_json)

        self.assertNotIn("investment_memo", machine_truth_doc)
        self.assertNotIn("memo", machine_truth_doc)
        self.assertEqual(decision_artifact.root, raw_decision)
        self.assertEqual(execution_record.root, raw_execution)
        self.assertTrue(outputs.investment_memo.startswith("# Investment Memo"))

    def test_missing_exportable_fields_raises_domain_error_instead_of_guessing(self):
        decision_artifact = DecisionArtifact.model_validate({})
        execution_record = ExecutionRecord.model_validate({})

        with self.assertRaisesRegex(ExportDomainError, "TODO"):
            export_outputs(
                decision_artifact=decision_artifact,
                execution_record=execution_record,
            )


if __name__ == "__main__":
    unittest.main()
