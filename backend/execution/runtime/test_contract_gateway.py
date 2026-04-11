from __future__ import annotations

import unittest

from backend.execution.runtime import ContractGateway, Web3InvestmentCompilerClient, build_emergency_force_close_call
from backend.execution.runtime.errors import EmergencyForceCloseInputError
from backend.reactive.adapters.models import InvestmentPositionState


class _FakeClient:
    def __init__(self) -> None:
        self.last_emergency_call = None

    def register_investment_intent(self, *, intent_id: str, intent: dict):  # pragma: no cover - not used in this test module
        return {"tx_hash": "0x" + "1" * 64}

    def execute_reactive_trigger(  # pragma: no cover - not used in this test module
        self,
        *,
        intent_id: str,
        trigger_type,
        observed_out: int,
    ):
        return {"tx_hash": "0x" + "1" * 64}

    def emergency_force_close(self, *, intent_id: str, max_slippage_bps: int):
        self.last_emergency_call = {
            "intent_id": intent_id,
            "max_slippage_bps": max_slippage_bps,
        }
        return {
            "tx_hash": "0x" + "2" * 64,
            "status": "success",
            "block_number": 1,
            "gas_used": 1,
            "logs": (),
        }

    def get_position_state(self, *, intent_id: str):
        return InvestmentPositionState.ACTIVE_POSITION

    def get_transaction_receipt(self, *, tx_hash: str):
        return None


class ContractGatewayEmergencyTests(unittest.TestCase):
    def test_web3_receipt_normalization_converts_binary_fields_to_hex(self) -> None:
        normalized = Web3InvestmentCompilerClient._normalize_receipt(
            {
                "status": 1,
                "transactionHash": bytes.fromhex("ab" * 32),
                "blockNumber": 123,
                "gasUsed": 456,
                "logs": [
                    {
                        "address": "0x0000000000000000000000000000000000000001",
                        "data": bytes.fromhex("abcd"),
                        "topics": [bytes.fromhex("01" * 32)],
                    }
                ],
            }
        )

        self.assertEqual(normalized["status"], "success")
        self.assertTrue(str(normalized["tx_hash"]).startswith("0x"))
        self.assertEqual(normalized["logs"][0]["data"], "0xabcd")
        self.assertEqual(
            normalized["logs"][0]["topics"][0],
            "0x" + ("01" * 32),
        )

    def test_build_emergency_force_close_call_maps_required_fields(self) -> None:
        call = build_emergency_force_close_call(
            recommendation={
                "intent_id": "0x" + "1" * 64,
                "reason_code": "STOP_LOSS_BREACH",
            },
            max_slippage_bps=700,
        )

        self.assertEqual(call.intent_id, "0x" + "1" * 64)
        self.assertEqual(call.max_slippage_bps, 700)
        self.assertEqual(call.reason_code, "STOP_LOSS_BREACH")

    def test_build_emergency_force_close_call_rejects_non_bytes32_intent_id(self) -> None:
        with self.assertRaises(EmergencyForceCloseInputError):
            build_emergency_force_close_call(
                recommendation={
                    "intent_id": "intent-001",
                    "reason_code": "STOP_LOSS_BREACH",
                },
                max_slippage_bps=700,
            )

    def test_gateway_calls_emergency_force_close_with_mapped_payload(self) -> None:
        client = _FakeClient()
        gateway = ContractGateway(client=client)

        receipt = gateway.emergency_force_close_from_recommendation(
            recommendation={
                "intent_id": "0x" + "2" * 64,
                "reason_code": "TAKE_PROFIT_BREACH",
            },
            max_slippage_bps=900,
        )

        self.assertEqual(client.last_emergency_call, {"intent_id": "0x" + "2" * 64, "max_slippage_bps": 900})
        self.assertEqual(receipt["status"], "success")


if __name__ == "__main__":
    unittest.main()
