from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

try:
    from web3 import Web3
except ImportError:  # pragma: no cover - environment dependency
    Web3 = None  # type: ignore[assignment]

from backend.execution.compiler import (
    ChainStateSnapshot,
    CompilationContext,
    RegistrationContext,
    compile_execution_plan,
    freeze_contract_call_inputs,
)
from backend.execution.runtime.contract_gateway import ContractGateway, Web3InvestmentCompilerClient
from backend.monitor.shadow_monitor import (
    ActivePositionIntent,
    BackupRPCSnapshot,
    BreachOperator,
    BreachRule,
    PositionState as ShadowPositionState,
    ShadowMonitor,
)
from backend.reactive.adapters.models import InvestmentPositionState, ReactiveTriggerType
from backend.strategy.models import StrategyIntent, TradeIntent


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


class Web3ContractGatewayIntegrationTestCase(unittest.TestCase):
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
        abi = artifact["abi"]
        bytecode = artifact["bytecode"]["object"]

        sender = cls._web3.eth.accounts[0]
        factory = cls._web3.eth.contract(abi=abi, bytecode=bytecode)
        deploy_tx = factory.constructor().transact({"from": sender})
        deploy_receipt = cls._web3.eth.wait_for_transaction_receipt(deploy_tx)
        contract = cls._web3.eth.contract(address=deploy_receipt.contractAddress, abi=abi)

        cls._sender = sender
        cls._gateway = ContractGateway(
            client=Web3InvestmentCompilerClient(
                web3=cls._web3,
                contract=contract,
                tx_sender=sender,
            )
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

    def test_register_investment_intent_returns_real_chain_receipt(self) -> None:
        current_block_timestamp = int(self._web3.eth.get_block("latest")["timestamp"])
        plan = compile_execution_plan(
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
                    block_timestamp=current_block_timestamp,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "1" * 64,
                    owner=self._sender,
                    input_token=self._web3.eth.accounts[1],
                    output_token=self._web3.eth.accounts[2],
                ),
            )
        )
        call_inputs = freeze_contract_call_inputs(plan)

        receipt = self._gateway.register_investment_intent(call_inputs=call_inputs)

        self.assertEqual(receipt["status"], "success")
        self.assertTrue(str(receipt["tx_hash"]).startswith("0x"))
        self.assertGreater(receipt["block_number"], 0)
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.PENDING_ENTRY,
        )

    def test_emergency_force_close_moves_active_position_to_closed(self) -> None:
        current_block_timestamp = int(self._web3.eth.get_block("latest")["timestamp"])
        plan = compile_execution_plan(
            CompilationContext(
                strategy_intent=StrategyIntent(
                    strategy_intent_id="si-002",
                    template_id="tpl-eth-swing",
                    template_version=1,
                    execution_mode="conditional",
                    projected_daily_trade_count=1,
                ),
                trade_intent=TradeIntent(
                    trade_intent_id="ti-002",
                    strategy_intent_id="si-002",
                    pair="ETH/USDC",
                    dex="uniswap_v3",
                    position_usd=Decimal("1300"),
                    max_slippage_bps=25,
                    stop_loss_bps=120,
                    take_profit_bps=260,
                    entry_conditions=["price_below:3000"],
                    ttl_seconds=3600,
                ),
                chain_state=ChainStateSnapshot(
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    block_number=20_000_100,
                    block_timestamp=current_block_timestamp,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "2" * 64,
                    owner=self._sender,
                    input_token=self._web3.eth.accounts[1],
                    output_token=self._web3.eth.accounts[2],
                ),
            )
        )
        call_inputs = freeze_contract_call_inputs(plan)
        self._gateway.register_investment_intent(call_inputs=call_inputs)
        self._gateway.execute_reactive_trigger(
            intent_id=call_inputs.intent_id,
            trigger_type=ReactiveTriggerType.ENTRY,
            observed_out=int(call_inputs.intent.entry_min_out),
        )
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.ACTIVE_POSITION,
        )

        receipt = self._gateway.emergency_force_close(
            intent_id=call_inputs.intent_id,
            max_slippage_bps=800,
        )

        self.assertEqual(receipt["status"], "success")
        self.assertTrue(str(receipt["tx_hash"]).startswith("0x"))
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.CLOSED,
        )

    def test_shadow_monitor_recommendation_drives_emergency_force_close(self) -> None:
        current_block_timestamp = int(self._web3.eth.get_block("latest")["timestamp"])
        plan = compile_execution_plan(
            CompilationContext(
                strategy_intent=StrategyIntent(
                    strategy_intent_id="si-003",
                    template_id="tpl-eth-swing",
                    template_version=1,
                    execution_mode="conditional",
                    projected_daily_trade_count=1,
                ),
                trade_intent=TradeIntent(
                    trade_intent_id="ti-003",
                    strategy_intent_id="si-003",
                    pair="ETH/USDC",
                    dex="uniswap_v3",
                    position_usd=Decimal("1400"),
                    max_slippage_bps=25,
                    stop_loss_bps=120,
                    take_profit_bps=260,
                    entry_conditions=["price_below:3000"],
                    ttl_seconds=3600,
                ),
                chain_state=ChainStateSnapshot(
                    base_fee_gwei=20,
                    max_priority_fee_gwei=2,
                    block_number=20_000_200,
                    block_timestamp=current_block_timestamp,
                    input_token_decimals=6,
                    output_token_decimals=18,
                    input_output_price=Decimal("0.0005"),
                    input_token_usd_price=Decimal("1"),
                ),
                registration_context=RegistrationContext(
                    intent_id="0x" + "3" * 64,
                    owner=self._sender,
                    input_token=self._web3.eth.accounts[1],
                    output_token=self._web3.eth.accounts[2],
                ),
            )
        )
        call_inputs = freeze_contract_call_inputs(plan)
        self._gateway.register_investment_intent(call_inputs=call_inputs)
        self._gateway.execute_reactive_trigger(
            intent_id=call_inputs.intent_id,
            trigger_type=ReactiveTriggerType.ENTRY,
            observed_out=int(call_inputs.intent.entry_min_out),
        )
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.ACTIVE_POSITION,
        )

        monitor = ShadowMonitor(grace_period_seconds=0)
        monitor_result = monitor.reconcile_positions(
            active_positions=[
                ActivePositionIntent(
                    intent_id=call_inputs.intent_id,
                    trade_intent_id="ti-003",
                    position_state=ShadowPositionState.ACTIVE_POSITION,
                    quantity=Decimal("1"),
                    breach_rules=[
                        BreachRule(
                            rule_id="stop-loss",
                            threshold_price=Decimal("2950"),
                            operator=BreachOperator.LTE,
                            reason_code="STOP_LOSS_BREACH",
                        )
                    ],
                )
            ],
            snapshots=[
                BackupRPCSnapshot(
                    intent_id=call_inputs.intent_id,
                    position_state=ShadowPositionState.ACTIVE_POSITION,
                    mark_price=Decimal("2910"),
                    observed_at=datetime.now(tz=timezone.utc),
                )
            ],
        )
        self.assertEqual(len(monitor_result.force_close_recommendations), 1)

        receipt = self._gateway.emergency_force_close_from_recommendation(
            recommendation=monitor_result.force_close_recommendations[0].model_dump(mode="python"),
            max_slippage_bps=900,
        )

        self.assertEqual(receipt["status"], "success")
        self.assertEqual(
            self._gateway.get_position_state(intent_id=call_inputs.intent_id),
            InvestmentPositionState.CLOSED,
        )


if __name__ == "__main__":
    unittest.main()
