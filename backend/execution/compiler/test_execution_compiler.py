from __future__ import annotations

from decimal import Decimal
import unittest

from backend.execution.compiler import (
    ChainStateSnapshot,
    CompilationContext,
    RegistrationContext,
    compile_execution_plan,
    freeze_contract_call_inputs,
)
from backend.strategy.models import StrategyIntent, TradeIntent


def _strategy_intent() -> StrategyIntent:
    return StrategyIntent(
        strategy_intent_id="si-001",
        template_id="tpl-eth-swing",
        template_version=1,
        execution_mode="conditional",
        projected_daily_trade_count=1,
    )


def _trade_intent() -> TradeIntent:
    return TradeIntent(
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


def _chain_state() -> ChainStateSnapshot:
    return ChainStateSnapshot(
        base_fee_gwei=20,
        max_priority_fee_gwei=2,
        block_number=20_000_000,
        block_timestamp=1_710_000_000,
        input_token_decimals=6,
        output_token_decimals=18,
        input_output_price=Decimal("0.0005"),
        input_token_usd_price=Decimal("1"),
    )


def _registration_context() -> RegistrationContext:
    return RegistrationContext(
        intent_id="0x" + "1" * 64,
        owner="0x0000000000000000000000000000000000000001",
        input_token="0x0000000000000000000000000000000000000002",
        output_token="0x0000000000000000000000000000000000000003",
    )


class ExecutionCompilerTestCase(unittest.TestCase):
    def test_compile_execution_plan_freezes_expected_register_payload(self) -> None:
        plan = compile_execution_plan(
            CompilationContext(
                strategy_intent=_strategy_intent(),
                trade_intent=_trade_intent(),
                chain_state=_chain_state(),
                registration_context=_registration_context(),
            )
        )

        payload = plan.register_payload
        self.assertEqual(plan.trade_intent_id, "ti-001")
        self.assertEqual(plan.hard_constraints.max_slippage_bps, 10)
        self.assertEqual(plan.hard_constraints.ttl_seconds, 3540)
        self.assertEqual(payload.intent_id, "0x" + "1" * 64)
        self.assertEqual(payload.planned_entry_size, 1200000000)
        self.assertEqual(payload.entry_amount_out_minimum, 599400000000000000)
        self.assertEqual(payload.entry_valid_until, 1710003540)
        self.assertEqual(payload.max_gas_price_gwei, 27)
        self.assertEqual(payload.exit_min_out_floor, 594005400000000000)

    def test_freeze_contract_call_inputs_maps_to_contract_shape(self) -> None:
        plan = compile_execution_plan(
            CompilationContext(
                strategy_intent=_strategy_intent(),
                trade_intent=_trade_intent(),
                chain_state=_chain_state(),
                registration_context=_registration_context(),
            )
        )
        frozen = freeze_contract_call_inputs(plan).model_dump(mode="python", by_alias=True)

        self.assertEqual(frozen["intentId"], "0x" + "1" * 64)
        self.assertEqual(
            frozen["intent"],
            {
                "owner": "0x0000000000000000000000000000000000000001",
                "inputToken": "0x0000000000000000000000000000000000000002",
                "outputToken": "0x0000000000000000000000000000000000000003",
                "plannedEntrySize": 1200000000,
                "entryMinOut": 599400000000000000,
                "exitMinOutFloor": 594005400000000000,
            },
        )


if __name__ == "__main__":
    unittest.main()
