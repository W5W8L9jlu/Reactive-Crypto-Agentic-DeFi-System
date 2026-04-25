from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import unittest
from decimal import Decimal
from pathlib import Path

from backend.cli.wiring import build_contract_gateway_from_web3
from backend.execution.compiler import (
    ChainStateSnapshot,
    CompilationContext,
    RegistrationContext,
    compile_execution_plan,
    freeze_contract_call_inputs,
)
from backend.reactive.adapters.models import InvestmentPositionState, ReactiveTriggerType
from backend.strategy.models import StrategyIntent, TradeIntent

try:
    from web3 import Web3
except ImportError:  # pragma: no cover - environment dependency
    Web3 = None  # type: ignore[assignment]


ANVIL_ACCOUNT_0_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _resolve_binary(*, env_key: str, binary: str) -> str | None:
    env_path = os.environ.get(env_key)
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return str(candidate)
    discovered = shutil.which(binary)
    if discovered:
        return discovered
    fallback = Path("D:/Foundry/bin") / f"{binary}.exe"
    if fallback.exists():
        return str(fallback)
    return None


class InvestmentStateMachineContractEmergencyForceCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if Web3 is None:
            raise unittest.SkipTest("web3 is not installed")

        anvil_bin = _resolve_binary(env_key="ANVIL_BIN", binary="anvil")
        if anvil_bin is None:
            raise unittest.SkipTest("anvil is not installed")
        forge_bin = _resolve_binary(env_key="FORGE_BIN", binary="forge")
        if forge_bin is None:
            raise unittest.SkipTest("forge is not installed")

        cls._repo_root = Path(__file__).resolve().parents[3]
        cls._contracts_root = cls._repo_root / "backend" / "contracts"
        subprocess.run(
            [forge_bin, "build", "--root", ".", "--contracts", "core", "--silent"],
            cwd=cls._contracts_root,
            check=True,
            capture_output=True,
        )

        cls._rpc_port = _find_free_port()
        cls._anvil_proc = subprocess.Popen(
            [
                anvil_bin,
                "--host",
                "127.0.0.1",
                "--port",
                str(cls._rpc_port),
                "--chain-id",
                "31337",
                "--silent",
            ],
            cwd=cls._contracts_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls._web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{cls._rpc_port}"))
        for _ in range(50):
            if cls._web3.is_connected():
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("anvil rpc did not become ready in time")

        artifact_path = cls._contracts_root / "out" / "ReactiveInvestmentCompiler.sol" / "ReactiveInvestmentCompiler.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        contract = cls._web3.eth.contract(
            abi=artifact["abi"],
            bytecode=artifact["bytecode"]["object"],
        )
        cls._sender = cls._web3.eth.account.from_key(ANVIL_ACCOUNT_0_PRIVATE_KEY).address
        deploy_tx = contract.constructor().transact({"from": cls._sender})
        deploy_receipt = cls._web3.eth.wait_for_transaction_receipt(deploy_tx)
        cls._deployed_contract = cls._web3.eth.contract(address=deploy_receipt.contractAddress, abi=artifact["abi"])
        cls._gateway = build_contract_gateway_from_web3(
            web3=cls._web3,
            contract=cls._deployed_contract,
            tx_sender=cls._sender,
            private_key=ANVIL_ACCOUNT_0_PRIVATE_KEY,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        proc = getattr(cls, "_anvil_proc", None)
        if proc is None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    def test_pending_entry_advances_to_active_then_emergency_force_close_closes_position(self) -> None:
        call_inputs = self._prepare_active_position(intent_suffix="7")
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.ACTIVE_POSITION,
        )

        emergency_exit_min_out = self._gateway.emergency_force_close(
            intent_id=call_inputs.intent_id,
            max_slippage_bps=300,
        )

        self.assertIsInstance(emergency_exit_min_out, dict)
        self.assertIn("tx_hash", emergency_exit_min_out)
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.CLOSED,
        )

    def _prepare_active_position(self, *, intent_suffix: str):
        current_block_timestamp = int(self._web3.eth.get_block("latest")["timestamp"])
        plan = compile_execution_plan(
            CompilationContext(
                strategy_intent=StrategyIntent(
                    strategy_intent_id="si-contract-force-close",
                    template_id="tpl-eth-swing",
                    template_version=1,
                    execution_mode="conditional",
                    projected_daily_trade_count=1,
                ),
                trade_intent=TradeIntent(
                    trade_intent_id="ti-contract-force-close",
                    strategy_intent_id="si-contract-force-close",
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
                    block_timestamp=current_block_timestamp,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + intent_suffix * 64,
                    owner=self._sender,
                    input_token=self._web3.eth.accounts[1],
                    output_token=self._web3.eth.accounts[2],
                ),
            )
        )
        call_inputs = freeze_contract_call_inputs(plan)
        self._gateway.register_investment_intent(call_inputs=call_inputs)
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.PENDING_ENTRY,
        )
        self._gateway.execute_reactive_trigger(
            intent_id=call_inputs.intent_id,
            trigger_type=ReactiveTriggerType.ENTRY,
            observed_out=int(call_inputs.intent.entry_min_out),
        )
        return call_inputs


if __name__ == "__main__":
    unittest.main()
