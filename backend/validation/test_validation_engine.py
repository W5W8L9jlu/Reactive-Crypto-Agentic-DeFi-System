from __future__ import annotations

import os
import sys
import unittest
from copy import deepcopy

from pydantic import ValidationError

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.validation import MissingValidationSpecError, validate_inputs, validate_inputs_or_raise


def _valid_payloads():
    strategy_template = {
        "template_id": "tpl-eth-swing",
        "version": 1,
        "auto_allowed_pairs": ["ETH/USDC"],
        "manual_allowed_pairs": ["WBTC/USDC"],
        "auto_allowed_dexes": ["uniswap_v3"],
        "manual_allowed_dexes": ["curve"],
        "auto_max_position_usd": "5000",
        "hard_max_position_usd": "10000",
        "auto_max_slippage_bps": 30,
        "hard_max_slippage_bps": 80,
        "auto_stop_loss_bps_range": {"min_bps": 50, "max_bps": 200},
        "manual_stop_loss_bps_range": {"min_bps": 10, "max_bps": 400},
        "auto_take_profit_bps_range": {"min_bps": 100, "max_bps": 500},
        "manual_take_profit_bps_range": {"min_bps": 50, "max_bps": 1000},
        "auto_daily_trade_limit": 2,
        "hard_daily_trade_limit": 8,
        "execution_mode": "conditional",
    }
    strategy_intent = {
        "strategy_intent_id": "si-001",
        "template_id": "tpl-eth-swing",
        "template_version": 1,
        "execution_mode": "conditional",
        "projected_daily_trade_count": 1,
    }
    trade_intent = {
        "trade_intent_id": "ti-001",
        "strategy_intent_id": "si-001",
        "pair": "ETH/USDC",
        "dex": "uniswap_v3",
        "position_usd": "1200",
        "max_slippage_bps": 20,
        "stop_loss_bps": 90,
        "take_profit_bps": 250,
        "entry_conditions": ["price_below:3000"],
        "ttl_seconds": 3600,
    }
    execution_plan = {
        "trade_intent_id": "ti-001",
        "register_payload": {
            "intentId": "0x" + "1" * 64,
            "owner": "0x0000000000000000000000000000000000000001",
            "inputToken": "0x0000000000000000000000000000000000000002",
            "outputToken": "0x0000000000000000000000000000000000000003",
            "plannedEntrySize": 1200000000,
            "entryAmountOutMinimum": 599400000000000000,
            "entryValidUntil": 1710003540,
            "maxGasPriceGwei": 27,
            "stopLossSlippageBps": 90,
            "takeProfitSlippageBps": 250,
        },
        "hard_constraints": {
            "max_slippage_bps": 10,
            "ttl_seconds": 3540,
            "stop_loss_bps": 90,
            "take_profit_bps": 250,
        },
    }
    return strategy_template, strategy_intent, trade_intent, execution_plan


class ValidationEngineTestCase(unittest.TestCase):
    def test_validate_inputs_happy_path_returns_valid_result(self):
        strategy_template, strategy_intent, trade_intent, execution_plan = _valid_payloads()

        result = validate_inputs(
            strategy_template=strategy_template,
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            execution_plan=execution_plan,
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, ())
        self.assertEqual(
            result.validated_objects,
            ("StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan"),
        )
        self.assertEqual(
            [binding.model_dump() for binding in result.contract_bindings],
            [
                {"source_field": "strategy_template.template_id", "target_field": "strategy_intent.template_id", "unit": "identity"},
                {"source_field": "strategy_template.version", "target_field": "strategy_intent.template_version", "unit": "identity"},
                {"source_field": "strategy_template.execution_mode", "target_field": "strategy_intent.execution_mode", "unit": "identity"},
                {"source_field": "trade_intent.trade_intent_id", "target_field": "execution_plan.trade_intent_id", "unit": "identity"},
                {"source_field": "trade_intent.max_slippage_bps", "target_field": "execution_plan.hard_constraints.max_slippage_bps", "unit": "bps"},
                {"source_field": "trade_intent.ttl_seconds", "target_field": "execution_plan.hard_constraints.ttl_seconds", "unit": "seconds"},
                {"source_field": "trade_intent.stop_loss_bps", "target_field": "execution_plan.hard_constraints.stop_loss_bps", "unit": "bps"},
                {"source_field": "trade_intent.take_profit_bps", "target_field": "execution_plan.hard_constraints.take_profit_bps", "unit": "bps"},
                {"source_field": "execution_plan.register_payload.intentId", "target_field": "register_call.intentId", "unit": "identity"},
                {"source_field": "execution_plan.register_payload.owner", "target_field": "investment_intent.owner", "unit": "identity"},
                {"source_field": "execution_plan.register_payload.inputToken", "target_field": "investment_intent.inputToken", "unit": "identity"},
                {"source_field": "execution_plan.register_payload.outputToken", "target_field": "investment_intent.outputToken", "unit": "identity"},
                {"source_field": "execution_plan.register_payload.plannedEntrySize", "target_field": "investment_intent.plannedEntrySize", "unit": "identity"},
                {"source_field": "execution_plan.register_payload.entryAmountOutMinimum", "target_field": "investment_intent.entryMinOut", "unit": "identity"},
                {"source_field": "execution_plan.register_payload.entryValidUntil", "target_field": "investment_intent.entryValidUntil", "unit": "seconds"},
                {"source_field": "execution_plan.register_payload.maxGasPriceGwei", "target_field": "investment_intent.maxGasPriceGwei", "unit": "gwei"},
                {"source_field": "execution_plan.register_payload.stopLossSlippageBps", "target_field": "investment_intent.stopLossSlippageBps", "unit": "bps"},
                {"source_field": "execution_plan.register_payload.takeProfitSlippageBps", "target_field": "investment_intent.takeProfitSlippageBps", "unit": "bps"},
            ],
        )

    def test_field_range_validation_rejects_invalid_ttl(self):
        strategy_template, strategy_intent, trade_intent, _ = _valid_payloads()
        bad_trade_intent = deepcopy(trade_intent)
        bad_trade_intent["ttl_seconds"] = 0

        result = validate_inputs(
            strategy_template=strategy_template,
            strategy_intent=strategy_intent,
            trade_intent=bad_trade_intent,
        )
        self.assertFalse(result.is_valid)
        self.assertTrue(any("greater_than" in item.code for item in result.issues))

        with self.assertRaises(ValidationError):
            validate_inputs_or_raise(
                strategy_template=strategy_template,
                strategy_intent=strategy_intent,
                trade_intent=bad_trade_intent,
            )

    def test_model_validator_rejects_template_version_mismatch(self):
        strategy_template, strategy_intent, trade_intent, _ = _valid_payloads()
        bad_strategy_intent = deepcopy(strategy_intent)
        bad_strategy_intent["template_version"] = 2

        result = validate_inputs(
            strategy_template=strategy_template,
            strategy_intent=bad_strategy_intent,
            trade_intent=trade_intent,
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("template_version" in item.message for item in result.issues))

    def test_illegal_trade_pair_is_rejected(self):
        strategy_template, strategy_intent, trade_intent, _ = _valid_payloads()
        bad_trade_intent = deepcopy(trade_intent)
        bad_trade_intent["pair"] = "ARB/USDC"

        result = validate_inputs(
            strategy_template=strategy_template,
            strategy_intent=strategy_intent,
            trade_intent=bad_trade_intent,
        )

        self.assertFalse(result.is_valid)
        self.assertTrue(any("allowed pairs" in item.message for item in result.issues))

    def test_missing_template_boundary_spec_raises_domain_error(self):
        strategy_template, strategy_intent, trade_intent, _ = _valid_payloads()
        bad_template = deepcopy(strategy_template)
        bad_template["auto_allowed_pairs"] = []
        bad_template["manual_allowed_pairs"] = []

        with self.assertRaisesRegex(MissingValidationSpecError, "TODO"):
            validate_inputs_or_raise(
                strategy_template=bad_template,
                strategy_intent=strategy_intent,
                trade_intent=trade_intent,
            )

    def test_successful_validation_requires_contract_facing_bindings(self):
        strategy_template, strategy_intent, trade_intent, _ = _valid_payloads()

        result = validate_inputs(
            strategy_template=strategy_template,
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
        )

        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.contract_bindings), 0)


if __name__ == "__main__":
    unittest.main()
