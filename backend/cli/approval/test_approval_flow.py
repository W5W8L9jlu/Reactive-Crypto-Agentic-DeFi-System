from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from backend.cli.models import ApprovalAction, DecisionMeta
from backend.cli.approval.flow import (
    ApprovalExpiredError,
    ApprovalRejectedResult,
    ApprovalResult,
    approve_intent,
    build_approval_battle_card,
    reject_intent,
    show_approval,
)
from backend.execution.compiler.models import RegisterPayload
from backend.strategy.models import TradeIntent
from backend.validation.models import ExecutionHardConstraints, ExecutionPlan, ValidationResult


class ApprovalFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.created_at = datetime(2026, 4, 3, 10, 0, tzinfo=timezone.utc)
        self.entry_valid_until = self.created_at + timedelta(minutes=4)

        self.trade_intent = TradeIntent(
            trade_intent_id="trade-001",
            strategy_intent_id="strategy-001",
            pair="ETH/USDC",
            dex="uniswap-v3",
            position_usd=Decimal("1500"),
            max_slippage_bps=100,
            stop_loss_bps=300,
            take_profit_bps=800,
            entry_conditions=["price <= 2500"],
            ttl_seconds=300,
        )
        self.execution_plan = ExecutionPlan(
            trade_intent_id="trade-001",
            register_payload=RegisterPayload(
                intentId="intent-001",
                owner="0xabc",
                inputToken="0xinput",
                outputToken="0xoutput",
                plannedEntrySize=600000000,
                entryAmountOutMinimum=1450000000,
                entryValidUntil=int(self.entry_valid_until.timestamp()),
                maxGasPriceGwei=55,
                stopLossSlippageBps=300,
                takeProfitSlippageBps=800,
            ),
            hard_constraints=ExecutionHardConstraints(
                max_slippage_bps=100,
                ttl_seconds=300,
                stop_loss_bps=300,
                take_profit_bps=800,
            ),
            compiled_at=self.created_at,
            compiler_version="1.0.0",
        )
        self.validation_result = ValidationResult(
            is_valid=True,
            validated_objects=("trade_intent", "execution_plan"),
        )
        self.decision_meta = DecisionMeta(
            trade_intent_id="trade-001",
            created_at=self.created_at,
            ttl_seconds=300,
        )
        self.machine_truth_json = (
            '{"decision_artifact":{"trade_intent_id":"trade-001"},'
            '"execution_record":{"register_payload":{"intentId":"intent-001"}}}'
        )

    def test_show_default_renders_human_battle_card_without_raw_json(self) -> None:
        rendered = show_approval(
            trade_intent=self.trade_intent,
            execution_plan=self.execution_plan,
            validation_result=self.validation_result,
            decision_meta=self.decision_meta,
            machine_truth_json=self.machine_truth_json,
            now=self.created_at + timedelta(minutes=1),
        )

        self.assertIn("Approval Battle Card", rendered)
        self.assertIn("TTL Remaining: 4m 0s", rendered)
        self.assertIn("Approve: allowed", rendered)
        self.assertNotIn(self.machine_truth_json, rendered)
        self.assertNotIn('"decision_artifact"', rendered)

    def test_show_raw_returns_machine_truth_verbatim(self) -> None:
        rendered = show_approval(
            trade_intent=self.trade_intent,
            execution_plan=self.execution_plan,
            validation_result=self.validation_result,
            decision_meta=self.decision_meta,
            machine_truth_json=self.machine_truth_json,
            raw=True,
            now=self.created_at,
        )

        self.assertEqual(rendered, self.machine_truth_json)

    def test_build_battle_card_maps_numeric_fields_from_structured_models(self) -> None:
        card = build_approval_battle_card(
            trade_intent=self.trade_intent,
            execution_plan=self.execution_plan,
            validation_result=self.validation_result,
            decision_meta=self.decision_meta,
            now=self.created_at,
        )

        self.assertEqual(card.position_usd, Decimal("1500"))
        self.assertEqual(card.position_usd_display, "$1.5k")
        self.assertEqual(card.max_slippage_display, "1.0%")
        self.assertEqual(card.stop_loss_display, "3.0%")
        self.assertEqual(card.take_profit_display, "8.0%")
        self.assertEqual(card.entry_amount_out_minimum, "1450000000")
        self.assertEqual(card.entry_valid_until, self.entry_valid_until)
        self.assertEqual(card.ttl_remaining_display, "5m 0s")

    def test_approve_blocks_expired_intent(self) -> None:
        with self.assertRaises(ApprovalExpiredError):
            approve_intent(
                trade_intent=self.trade_intent,
                execution_plan=self.execution_plan,
                validation_result=self.validation_result,
                decision_meta=self.decision_meta,
                now=self.created_at + timedelta(minutes=6),
            )

    def test_reject_returns_explicit_rejected_result(self) -> None:
        result = reject_intent(
            trade_intent=self.trade_intent,
            decision_meta=self.decision_meta,
            reason="operator rejected after review",
            now=self.created_at + timedelta(minutes=6),
        )

        self.assertIsInstance(result, ApprovalRejectedResult)
        self.assertIsInstance(result, ApprovalResult)
        self.assertEqual(result.action, ApprovalAction.REJECT)
        self.assertEqual(result.trade_intent_id, "trade-001")
        self.assertEqual(result.reason, "operator rejected after review")


if __name__ == "__main__":
    unittest.main()
