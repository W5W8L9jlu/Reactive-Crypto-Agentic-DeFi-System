import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

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
