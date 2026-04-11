from __future__ import annotations

import unittest
from decimal import Decimal

from backend.execution.compiler import ChainStateSnapshot, CompilationContext, RegistrationContext, compile_execution_plan
from backend.execution.runtime.execution_layer import execute_runtime_transition_or_raise
from backend.reactive.adapters.models import (
    InvestmentPositionState,
    ReactiveCallbackType,
    ReactiveRuntimeResult,
    ReactiveTriggerType,
)
from backend.strategy.models import StrategyIntent, TradeIntent


class _FakeReceiptReader:
    def get_transaction_receipt(self, *, tx_hash: str):
        return {
            "tx_hash": tx_hash,
            "status": "success",
            "block_number": 20_000_123,
            "gas_used": 212345,
            "logs": [{"event": "InvestmentStateAdvanced"}],
        }


def _execution_plan():
    return compile_execution_plan(
        CompilationContext(
            strategy_intent=StrategyIntent(
                strategy_intent_id="si-001",
                template_id="tpl-eth-swing",
                template_version=1,
                execution_mode="conditional",
                projected_daily_trade_count=1,
            ),
            trade_intent=TradeIntent(
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
            ),
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


class ExecutionLayerTestCase(unittest.TestCase):
    def test_execute_runtime_transition_builds_execution_record(self) -> None:
        runtime_result = ReactiveRuntimeResult(
            is_executed=True,
            callback_verified=True,
            intent_id="0x" + "1" * 64,
            trade_intent_id="ti-001",
            trigger_type=ReactiveTriggerType.ENTRY,
            callback_type=ReactiveCallbackType.ENTRY,
            state_before=InvestmentPositionState.PENDING_ENTRY,
            state_after=InvestmentPositionState.ACTIVE_POSITION,
            callback_ref="0x" + "2" * 64,
        )

        record = execute_runtime_transition_or_raise(
            execution_plan=_execution_plan(),
            runtime_result=runtime_result,
            receipt_reader=_FakeReceiptReader(),
        )

        self.assertEqual(record.status, "executed")
        self.assertEqual(record.trade_intent_id, "ti-001")
        self.assertEqual(record.intent_id, "0x" + "1" * 64)
        self.assertEqual(record.chain_receipt.tx_hash, "0x" + "2" * 64)
        self.assertEqual(record.chain_receipt.block_number, 20_000_123)


if __name__ == "__main__":
    unittest.main()
