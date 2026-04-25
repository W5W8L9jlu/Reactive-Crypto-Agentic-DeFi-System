from __future__ import annotations

import unittest
from decimal import Decimal

from backend.strategy.models import StrategyIntent, TradeIntent
from backend.validation.pre_registration_check import (
    ExpiredIntentError,
    GasTooHighError,
    InsufficientBalanceError,
    InsufficientAllowanceError,
    RPCStateSnapshot,
    run_pre_registration_check,
)


def _valid_inputs() -> tuple[StrategyIntent, TradeIntent, RPCStateSnapshot]:
    strategy_intent = StrategyIntent(
        strategy_intent_id="si-001",
        template_id="tpl-eth-swing",
        template_version=1,
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
    snapshot = RPCStateSnapshot(
        block_number=123,
        block_timestamp=1710000000,
        input_token_usd_price=Decimal("1"),
        input_token_reserve=Decimal("1000000"),
        output_token_reserve=Decimal("500000"),
        wallet_input_balance=Decimal("5000"),
        wallet_input_allowance=Decimal("5000"),
        base_fee_gwei=10,
        max_priority_fee_gwei=2,
        max_gas_price_gwei=30,
        estimated_gas_used=100000,
        native_token_usd_price=Decimal("2000"),
        expected_profit_usd=Decimal("100"),
        ttl_buffer_seconds=60,
    )
    return strategy_intent, trade_intent, snapshot


class PreRegistrationCheckTestCase(unittest.TestCase):
    def test_happy_path_returns_allowed_result(self) -> None:
        strategy_intent, trade_intent, snapshot = _valid_inputs()

        result = run_pre_registration_check(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            rpc_state_snapshot=snapshot,
        )

        self.assertTrue(result.is_allowed)
        self.assertIsNone(result.abort_reason)
        self.assertIsNotNone(result.observations)
        self.assertEqual(result.strategy_intent_id, strategy_intent.strategy_intent_id)
        self.assertEqual(result.trade_intent_id, trade_intent.trade_intent_id)
        self.assertLessEqual(result.observations.observed_slippage_bps, Decimal("20"))

    def test_rejection_path_returns_abort_reason(self) -> None:
        strategy_intent, trade_intent, snapshot = _valid_inputs()
        snapshot = snapshot.model_copy(update={"wallet_input_balance": Decimal("1000")})

        result = run_pre_registration_check(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            rpc_state_snapshot=snapshot,
        )

        self.assertFalse(result.is_allowed)
        self.assertIsNotNone(result.abort_reason)
        self.assertIsNone(result.observations)
        self.assertEqual(result.abort_reason.code, InsufficientBalanceError.__name__)
        self.assertIn("wallet_input_balance", result.abort_reason.message)

    def test_rejects_when_allowance_is_insufficient(self) -> None:
        strategy_intent, trade_intent, snapshot = _valid_inputs()
        snapshot = snapshot.model_copy(update={"wallet_input_allowance": Decimal("1000")})

        result = run_pre_registration_check(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            rpc_state_snapshot=snapshot,
        )

        self.assertFalse(result.is_allowed)
        self.assertIsNone(result.observations)
        self.assertEqual(result.abort_reason.code, InsufficientAllowanceError.__name__)
        self.assertIn("wallet_input_allowance", result.abort_reason.message)

    def test_rejects_when_gas_is_too_high(self) -> None:
        strategy_intent, trade_intent, snapshot = _valid_inputs()
        snapshot = snapshot.model_copy(update={"max_gas_price_gwei": 5})

        result = run_pre_registration_check(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            rpc_state_snapshot=snapshot,
        )

        self.assertFalse(result.is_allowed)
        self.assertIsNone(result.observations)
        self.assertEqual(result.abort_reason.code, GasTooHighError.__name__)
        self.assertIn("current gas price", result.abort_reason.message)

    def test_rejects_when_ttl_is_expired(self) -> None:
        strategy_intent, trade_intent, snapshot = _valid_inputs()
        snapshot = snapshot.model_copy(update={"ttl_buffer_seconds": 3600})

        result = run_pre_registration_check(
            strategy_intent=strategy_intent,
            trade_intent=trade_intent,
            rpc_state_snapshot=snapshot,
        )

        self.assertFalse(result.is_allowed)
        self.assertIsNone(result.observations)
        self.assertEqual(result.abort_reason.code, ExpiredIntentError.__name__)
        self.assertIn("ttl_buffer_seconds", result.abort_reason.message)


if __name__ == "__main__":
    unittest.main()
