from __future__ import annotations

import json
import os
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone

CURRENT_DIR = os.path.dirname(__file__)
EXPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "export"))

sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, EXPORT_DIR)

from execution_layer import ChainReceipt, RuntimeGateError, RuntimeTrigger, execute_runtime_trigger
from export_outputs import DecisionArtifact, ExecutionRecord as ExportExecutionRecord, export_outputs


@dataclass(frozen=True)
class StubRegisterPayload:
    intent_id: str


@dataclass(frozen=True)
class StubExecutionPlan:
    trade_intent_id: str
    register_payload: StubRegisterPayload


class RecordingExecutor:
    def __init__(self, receipt: ChainReceipt) -> None:
        self.receipt = receipt
        self.calls: list[tuple[StubExecutionPlan, RuntimeTrigger]] = []

    def execute_reactive_trigger(
        self,
        *,
        execution_plan: StubExecutionPlan,
        runtime_trigger: RuntimeTrigger,
    ) -> ChainReceipt:
        self.calls.append((execution_plan, runtime_trigger))
        return self.receipt


def _make_execution_plan() -> StubExecutionPlan:
    return StubExecutionPlan(
        trade_intent_id="trade-intent-001",
        register_payload=StubRegisterPayload(
            intent_id="0xintent001",
        ),
    )


def _make_runtime_trigger(*, checks_passed: bool = True) -> RuntimeTrigger:
    return RuntimeTrigger(
        trigger_id="trigger-001",
        trade_intent_id="trade-intent-001",
        trigger_source="reactive.runtime",
        triggered_at=datetime(2026, 4, 1, 9, 5, tzinfo=timezone.utc),
        onchain_checks_passed=checks_passed,
        metadata={"condition": "take_profit"},
    )


class ExecutionLayerTestCase(unittest.TestCase):
    def test_success_receipt_produces_execution_record(self) -> None:
        execution_plan = _make_execution_plan()
        runtime_trigger = _make_runtime_trigger()
        receipt = ChainReceipt(
            transaction_hash="0xtx-success",
            block_number=22_222_222,
            gas_used=210_000,
            status=1,
            logs=[{"address": "0xpool", "topics": ["0xabc"], "data": "0x01"}],
            effective_gas_price_wei=12_000_000_000,
        )
        executor = RecordingExecutor(receipt)

        record = execute_runtime_trigger(
            execution_plan=execution_plan,
            runtime_trigger=runtime_trigger,
            executor=executor,
        )

        self.assertEqual(record.execution_status, "succeeded")
        self.assertEqual(record.trade_intent_id, execution_plan.trade_intent_id)
        self.assertEqual(record.intent_id, execution_plan.register_payload.intent_id)
        self.assertEqual(record.trigger_id, runtime_trigger.trigger_id)
        self.assertEqual(record.receipt.transaction_hash, receipt.transaction_hash)
        self.assertEqual(record.receipt.block_number, receipt.block_number)
        self.assertEqual(record.receipt.gas_used, receipt.gas_used)
        self.assertEqual(record.receipt.logs, receipt.logs)
        self.assertEqual(len(executor.calls), 1)

    def test_failed_receipt_is_recorded_without_guessing_success(self) -> None:
        execution_plan = _make_execution_plan()
        runtime_trigger = _make_runtime_trigger()
        receipt = ChainReceipt(
            transaction_hash="0xtx-failed",
            block_number=22_222_223,
            gas_used=190_000,
            status=0,
            logs=[],
            effective_gas_price_wei=11_000_000_000,
            revert_reason="SLIPPAGE_EXCEEDED",
        )
        executor = RecordingExecutor(receipt)

        record = execute_runtime_trigger(
            execution_plan=execution_plan,
            runtime_trigger=runtime_trigger,
            executor=executor,
        )

        self.assertEqual(record.execution_status, "failed")
        self.assertEqual(record.receipt.status, 0)
        self.assertEqual(record.receipt.revert_reason, "SLIPPAGE_EXCEEDED")
        self.assertEqual(len(executor.calls), 1)

    def test_runtime_checks_must_pass_before_any_chain_call(self) -> None:
        execution_plan = _make_execution_plan()
        runtime_trigger = _make_runtime_trigger(checks_passed=False)
        receipt = ChainReceipt(
            transaction_hash="0xshould-not-send",
            block_number=1,
            gas_used=1,
            status=1,
            logs=[],
        )
        executor = RecordingExecutor(receipt)

        with self.assertRaisesRegex(RuntimeGateError, "on-chain runtime checks"):
            execute_runtime_trigger(
                execution_plan=execution_plan,
                runtime_trigger=runtime_trigger,
                executor=executor,
            )

        self.assertEqual(executor.calls, [])

    def test_execution_record_json_dump_is_export_compatible(self) -> None:
        execution_plan = _make_execution_plan()
        runtime_trigger = _make_runtime_trigger()
        receipt = ChainReceipt(
            transaction_hash="0xtx-export",
            block_number=22_222_224,
            gas_used=205_000,
            status=1,
            logs=[{"address": "0xpool", "topics": [], "data": "0x02"}],
        )
        executor = RecordingExecutor(receipt)

        record = execute_runtime_trigger(
            execution_plan=execution_plan,
            runtime_trigger=runtime_trigger,
            executor=executor,
        )
        exportable_record = record.model_dump(mode="json")

        outputs = export_outputs(
            decision_artifact=DecisionArtifact.model_validate({"conclusion": "WAIT_FOR_TRIGGER"}),
            execution_record=ExportExecutionRecord.model_validate(exportable_record),
        )

        machine_truth_doc = json.loads(outputs.machine_truth_json)

        self.assertEqual(machine_truth_doc["execution_record"], exportable_record)


if __name__ == "__main__":
    unittest.main()
