from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from backend.execution.compiler.models import ContractRegisterCallInputs
from backend.reactive.adapters.models import InvestmentPositionState, ReactiveTriggerType

from .errors import EmergencyForceCloseInputError


@dataclass(frozen=True)
class EmergencyForceCloseCall:
    intent_id: str
    max_slippage_bps: int
    reason_code: str


class InvestmentCompilerContractClient(Protocol):
    def register_investment_intent(self, *, intent_id: str, intent: dict[str, Any]) -> dict[str, Any]: ...

    def execute_reactive_trigger(
        self,
        *,
        intent_id: str,
        trigger_type: ReactiveTriggerType | str,
        observed_out: int,
    ) -> dict[str, Any]: ...

    def emergency_force_close(self, *, intent_id: str, max_slippage_bps: int) -> dict[str, Any]: ...

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState: ...

    def get_transaction_receipt(self, *, tx_hash: str) -> dict[str, Any] | None: ...


class ContractGateway:
    """Application-facing gateway for register/trigger/receipt operations."""

    def __init__(self, *, client: InvestmentCompilerContractClient) -> None:
        self._client = client

    def register_investment_intent(self, *, call_inputs: ContractRegisterCallInputs) -> dict[str, Any]:
        return self._client.register_investment_intent(
            intent_id=call_inputs.intent_id,
            intent=call_inputs.intent.model_dump(mode="python", by_alias=True),
        )

    def execute_reactive_trigger(
        self,
        *,
        intent_id: str,
        trigger_type: ReactiveTriggerType | str,
        observed_out: int,
    ) -> dict[str, Any]:
        return self._client.execute_reactive_trigger(
            intent_id=intent_id,
            trigger_type=trigger_type,
            observed_out=observed_out,
        )

    def emergency_force_close(
        self,
        *,
        intent_id: str,
        max_slippage_bps: int,
    ) -> dict[str, Any]:
        return self._client.emergency_force_close(
            intent_id=intent_id,
            max_slippage_bps=max_slippage_bps,
        )

    def emergency_force_close_from_recommendation(
        self,
        *,
        recommendation: dict[str, Any],
        max_slippage_bps: int,
    ) -> dict[str, Any]:
        call = build_emergency_force_close_call(
            recommendation=recommendation,
            max_slippage_bps=max_slippage_bps,
        )
        return self.emergency_force_close(
            intent_id=call.intent_id,
            max_slippage_bps=call.max_slippage_bps,
        )

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState:
        return self._client.get_position_state(intent_id=intent_id)

    def get_transaction_receipt(self, *, tx_hash: str) -> dict[str, Any] | None:
        return self._client.get_transaction_receipt(tx_hash=tx_hash)


class Web3InvestmentCompilerClient:
    """Thin Web3 adapter that executes register/trigger calls against the contract ABI."""

    def __init__(
        self,
        *,
        web3: Any,
        contract: Any,
        tx_sender: str,
        private_key: str | None = None,
    ) -> None:
        self._web3 = web3
        self._contract = contract
        self._private_key = private_key
        if private_key is None:
            self._tx_sender = tx_sender
            return
        account = self._web3.eth.account.from_key(private_key)
        derived_sender = account.address
        if tx_sender and tx_sender.lower() != derived_sender.lower():
            raise ValueError("tx_sender must match the address derived from private_key")
        self._tx_sender = derived_sender

    def register_investment_intent(self, *, intent_id: str, intent: dict[str, Any]) -> dict[str, Any]:
        tx_hash = self._send_transaction(
            self._contract.functions.registerInvestmentIntent(
            _hex_to_bytes32(intent_id),
            (
                intent["owner"],
                intent["inputToken"],
                intent["outputToken"],
                int(intent["plannedEntrySize"]),
                int(intent["entryMinOut"]),
                int(intent["entryValidUntil"]),
                int(intent["maxGasPriceGwei"]),
                int(intent["stopLossSlippageBps"]),
                int(intent["takeProfitSlippageBps"]),
            ),
            )
        )
        return self._normalize_receipt(self._web3.eth.wait_for_transaction_receipt(tx_hash))

    def execute_reactive_trigger(
        self,
        *,
        intent_id: str,
        trigger_type: ReactiveTriggerType | str,
        observed_out: int,
    ) -> dict[str, Any]:
        tx_hash = self._send_transaction(
            self._contract.functions.executeReactiveTrigger(
            _hex_to_bytes32(intent_id),
            _to_contract_trigger_type(trigger_type),
            int(observed_out),
            )
        )
        return self._normalize_receipt(self._web3.eth.wait_for_transaction_receipt(tx_hash))

    def emergency_force_close(self, *, intent_id: str, max_slippage_bps: int) -> dict[str, Any]:
        tx_hash = self._send_transaction(
            self._contract.functions.emergencyForceClose(
            _hex_to_bytes32(intent_id),
            int(max_slippage_bps),
            )
        )
        return self._normalize_receipt(self._web3.eth.wait_for_transaction_receipt(tx_hash))

    def get_position_state(self, *, intent_id: str) -> InvestmentPositionState:
        raw_state = int(self._contract.functions.getPositionState(_hex_to_bytes32(intent_id)).call())
        if raw_state == 0:
            return InvestmentPositionState.PENDING_ENTRY
        if raw_state == 1:
            return InvestmentPositionState.ACTIVE_POSITION
        return InvestmentPositionState.CLOSED

    def get_transaction_receipt(self, *, tx_hash: str) -> dict[str, Any] | None:
        raw_receipt = self._web3.eth.get_transaction_receipt(tx_hash)
        if raw_receipt is None:
            return None
        return self._normalize_receipt(raw_receipt)

    def _send_transaction(self, contract_function: Any) -> Any:
        if self._private_key is None:
            return contract_function.transact({"from": self._tx_sender})
        nonce = int(self._web3.eth.get_transaction_count(self._tx_sender))
        latest_block = self._web3.eth.get_block("latest")
        base_fee = int(latest_block.get("baseFeePerGas", 0) or 0)
        priority_fee = int(getattr(self._web3.eth, "max_priority_fee", self._web3.to_wei(2, "gwei")))
        max_fee_per_gas = max(base_fee * 2 + priority_fee, priority_fee)
        tx = contract_function.build_transaction(
            {
                "from": self._tx_sender,
                "nonce": nonce,
                "chainId": int(self._web3.eth.chain_id),
                "maxPriorityFeePerGas": priority_fee,
                "maxFeePerGas": max_fee_per_gas,
            }
        )
        signed = self._web3.eth.account.sign_transaction(tx, self._private_key)
        return self._web3.eth.send_raw_transaction(signed.raw_transaction)

    @staticmethod
    def _normalize_receipt(receipt: Any) -> dict[str, Any]:
        status = "success" if int(receipt["status"]) == 1 else "reverted"
        raw_tx_hash = (
            receipt["transactionHash"].hex()
            if hasattr(receipt["transactionHash"], "hex")
            else str(receipt["transactionHash"])
        )
        tx_hash = str(raw_tx_hash)
        if not tx_hash.startswith("0x"):
            tx_hash = f"0x{tx_hash}"
        return {
            "tx_hash": tx_hash,
            "status": status,
            "block_number": int(receipt["blockNumber"]),
            "gas_used": int(receipt["gasUsed"]),
            "logs": tuple(
                Web3InvestmentCompilerClient._normalize_json_value(dict(log))
                for log in receipt.get("logs", [])
            ),
        }

    @staticmethod
    def _normalize_json_value(value: Any) -> Any:
        if isinstance(value, (bytes, bytearray)):
            return "0x" + bytes(value).hex()
        if isinstance(value, dict):
            return {
                str(key): Web3InvestmentCompilerClient._normalize_json_value(inner)
                for key, inner in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [Web3InvestmentCompilerClient._normalize_json_value(item) for item in value]
        return value


def _hex_to_bytes32(value: str) -> bytes:
    hex_value = value[2:] if value.startswith("0x") else value
    raw = bytes.fromhex(hex_value)
    if len(raw) != 32:
        raise ValueError("intent_id must be a 32-byte hex string")
    return raw


def _to_contract_trigger_type(value: ReactiveTriggerType | str) -> int:
    normalized = value.value if isinstance(value, ReactiveTriggerType) else str(value).strip().lower()
    if normalized == "entry":
        return 0
    if normalized == "stop_loss":
        return 1
    if normalized == "take_profit":
        return 2
    raise ValueError(f"unsupported trigger_type: {value!r}")


def build_emergency_force_close_call(
    *,
    recommendation: dict[str, Any],
    max_slippage_bps: int,
) -> EmergencyForceCloseCall:
    intent_id = recommendation.get("intent_id")
    reason_code = recommendation.get("reason_code")
    if not isinstance(intent_id, str) or not intent_id:
        raise EmergencyForceCloseInputError("recommendation.intent_id must be non-empty str")
    if not isinstance(reason_code, str) or not reason_code:
        raise EmergencyForceCloseInputError("recommendation.reason_code must be non-empty str")
    if isinstance(max_slippage_bps, bool) or not isinstance(max_slippage_bps, int):
        raise EmergencyForceCloseInputError("max_slippage_bps must be int")
    if max_slippage_bps < 0 or max_slippage_bps > 10_000:
        raise EmergencyForceCloseInputError("max_slippage_bps must be in [0, 10000]")
    try:
        _hex_to_bytes32(intent_id)
    except ValueError as exc:  # pragma: no cover - branch covered via caller tests
        raise EmergencyForceCloseInputError(
            "recommendation.intent_id must be 32-byte hex string (0x...)"
        ) from exc
    return EmergencyForceCloseCall(
        intent_id=intent_id,
        max_slippage_bps=max_slippage_bps,
        reason_code=reason_code,
    )


__all__ = [
    "ContractGateway",
    "EmergencyForceCloseCall",
    "InvestmentCompilerContractClient",
    "Web3InvestmentCompilerClient",
    "build_emergency_force_close_call",
]
