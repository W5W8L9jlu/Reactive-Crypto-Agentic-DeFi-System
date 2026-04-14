from __future__ import annotations

import json
import os
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from backend.cli import wiring as wiring_module
from backend.cli.errors import CLISurfaceInputError, RouteBindingMissingError
from backend.cli.app import create_cli_app, create_default_cli_app
from backend.cli.runtime_store import CLIRuntimeStore, IntentArtifactRecord
from backend.cli.wiring import (
    build_contract_gateway_from_web3,
    build_contract_gateway_from_runtime_env,
    build_cryptoagents_decision_adapter,
    build_decision_dry_run_handler_from_runtime_env,
    build_decision_run_handler,
    build_execution_force_close_handler,
    build_production_services,
)
from backend.decision.schemas import AgentTrace, AgentTraceStep, CryptoAgentsDecision, DecisionMeta
from backend.execution.runtime import ContractGateway
from backend.strategy.models import StrategyIntent, TradeIntent


class _FakeMainChainService:
    def __init__(self) -> None:
        self.last_request = None

    def run_or_raise(self, request):
        self.last_request = request
        return SimpleNamespace(
            execution_plan=SimpleNamespace(
                register_payload=SimpleNamespace(intent_id="0x" + "1" * 64),
            ),
            register_receipt={"tx_hash": "0x" + "2" * 64},
            execution_record=SimpleNamespace(status="executed"),
        )


class _FakeRequestFactory:
    def __init__(self) -> None:
        self.last_context_id = None

    def build(self, *, context_id: str):
        self.last_context_id = context_id
        return {"context_id": context_id}


class _FakeForceCloseGateway:
    def __init__(self) -> None:
        self.calls = []

    def emergency_force_close(self, *, intent_id: str, max_slippage_bps: int):
        self.calls.append((intent_id, max_slippage_bps))
        return {
            "tx_hash": "0x" + "4" * 64,
            "status": "success",
            "block_number": 123,
        }


class _FakeDecisionAdapterForDryRun:
    def build_decision_or_raise(self, *, decision_context, strategy_template):
        return CryptoAgentsDecision(
            strategy_intent=StrategyIntent(
                strategy_intent_id="si-ctx-001",
                template_id=strategy_template.template_id,
                template_version=strategy_template.version,
                execution_mode="conditional",
                projected_daily_trade_count=1,
            ),
            trade_intent=TradeIntent(
                trade_intent_id="ti-ctx-001",
                strategy_intent_id="si-ctx-001",
                pair=decision_context.strategy_constraints.pair,
                dex=decision_context.strategy_constraints.dex,
                position_usd=Decimal("1200"),
                max_slippage_bps=20,
                stop_loss_bps=90,
                take_profit_bps=250,
                entry_conditions=["price_below:3000"],
                ttl_seconds=3600,
            ),
            decision_meta=DecisionMeta(
                investment_thesis="test thesis",
                confidence_score=Decimal("0.8"),
                generated_at=datetime.now(tz=timezone.utc),
            ),
            agent_trace=AgentTrace(
                steps=(
                    AgentTraceStep(
                        agent="portfolio_manager",
                        summary="test trace",
                        timestamp=datetime.now(tz=timezone.utc),
                    ),
                )
            ),
        )


class CLIWiringTests(unittest.TestCase):
    def _new_store(self) -> CLIRuntimeStore:
        tmp_dir = TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        return CLIRuntimeStore(db_path=Path(tmp_dir.name) / "cli_state.db")

    def test_build_decision_run_handler_returns_summary_json(self) -> None:
        service = _FakeMainChainService()
        request_factory = _FakeRequestFactory()
        handler = build_decision_run_handler(
            main_chain_service=service,
            request_factory=request_factory,
        )

        payload = json.loads(handler("ctx-001"))

        self.assertEqual(request_factory.last_context_id, "ctx-001")
        self.assertEqual(service.last_request, {"context_id": "ctx-001"})
        self.assertEqual(payload["intent_id"], "0x" + "1" * 64)
        self.assertEqual(payload["register_tx_hash"], "0x" + "2" * 64)
        self.assertEqual(payload["execution_status"], "executed")

    def test_build_production_services_binds_all_cli_routes(self) -> None:
        gateway = _FakeForceCloseGateway()
        store = self._new_store()
        store.create_strategy(
            strategy_id="strat-001",
            template={"template_id": "tpl-001", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
        )
        now = datetime.now(tz=timezone.utc).isoformat()
        store.save_intent_artifact(
            IntentArtifactRecord(
                intent_id="intent-001",
                strategy_id="strat-001",
                trade_intent_id="ti-001",
                approval_status="pending",
                approval_payload={
                    "trade_intent": {
                        "trade_intent_id": "ti-001",
                        "strategy_intent_id": "si-001",
                        "pair": "ETH/USDC",
                        "dex": "uniswap_v3",
                        "position_usd": "1000",
                        "max_slippage_bps": 20,
                        "stop_loss_bps": 100,
                        "take_profit_bps": 250,
                        "entry_conditions": ["price_below:3000"],
                        "ttl_seconds": 3600,
                    },
                    "execution_plan": {
                        "trade_intent_id": "ti-001",
                        "register_payload": {
                            "intentId": "0x" + "1" * 64,
                            "owner": "0x0000000000000000000000000000000000000001",
                            "inputToken": "0x0000000000000000000000000000000000000002",
                            "outputToken": "0x0000000000000000000000000000000000000003",
                            "plannedEntrySize": 1000,
                            "entryAmountOutMinimum": 1,
                            "entryValidUntil": 4102444800,
                            "maxGasPriceGwei": 50,
                            "stopLossSlippageBps": 100,
                            "takeProfitSlippageBps": 250,
                        },
                        "hard_constraints": {
                            "max_slippage_bps": 20,
                            "ttl_seconds": 3600,
                            "stop_loss_bps": 100,
                            "take_profit_bps": 250,
                        },
                    },
                    "validation_result": {
                        "is_valid": True,
                        "validated_objects": ["StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan"],
                        "issues": [],
                        "contract_bindings": [],
                    },
                    "decision_meta": {
                        "trade_intent_id": "ti-001",
                        "created_at": now,
                        "ttl_seconds": 3600,
                        "ttl_source": "trade_intent.ttl_seconds",
                    },
                },
                machine_truth_json='{"decision_artifact":{},"execution_record":{}}',
                execution_record={
                    "status": "executed",
                    "chain_receipt": {"tx_hash": "0x" + "2" * 64, "status": "success", "block_number": 1, "logs": []},
                },
                export_markdown="# Audit",
                export_memo="# Memo",
                monitor_alerts=[],
                monitor_status={"status": "healthy"},
                created_at=now,
                updated_at=now,
            )
        )
        services = build_production_services(
            contract_gateway=gateway,
            runtime_store=store,
            emergency_force_close_max_slippage_bps=250,
            decision_run_handler=lambda strategy_id: f"decision run wired: {strategy_id}",
            decision_dry_run_handler=lambda strategy_id: f"decision dry-run wired: {strategy_id}",
            monitor_alerts_handler=lambda _critical_only: [],
            monitor_shadow_status_handler=lambda: json.dumps(
                {"status": "healthy", "tracked_intents": 1, "critical_alerts": 0},
                ensure_ascii=False,
            ),
        )

        checks = [
            lambda: services.strategy_create(),
            lambda: services.strategy_list(),
            lambda: services.strategy_show("strat-001"),
            lambda: services.strategy_edit("strat-001"),
            lambda: services.decision_run("strat-001"),
            lambda: services.decision_dry_run("strat-001"),
            lambda: services.approval_list(),
            lambda: services.approval_show("intent-001", False, None),
            lambda: services.approval_approve("intent-001"),
            lambda: services.execution_show("intent-001"),
            lambda: services.execution_logs("intent-001"),
            lambda: services.execution_force_close("intent-001"),
            lambda: services.execution_fork_replay("intent-001", 100, 120),
            lambda: services.export_json("intent-001"),
            lambda: services.export_markdown("intent-001"),
            lambda: services.export_memo("intent-001"),
            lambda: services.monitor_alerts(False),
            lambda: services.monitor_shadow_status(),
        ]
        for fn in checks:
            fn()

        self.assertEqual(gateway.calls, [("intent-001", 250)])

    def test_build_production_services_requires_gateway_for_force_close(self) -> None:
        services = build_production_services(runtime_store=self._new_store())

        with self.assertRaises(RouteBindingMissingError):
            services.execution_force_close("0x" + "1" * 64)

    def test_build_production_services_requires_runtime_wiring_for_decision_routes(self) -> None:
        services = build_production_services(runtime_store=self._new_store())

        with self.assertRaises(RouteBindingMissingError):
            services.decision_run("ctx-001")
        with self.assertRaises(RouteBindingMissingError):
            services.decision_dry_run("ctx-001")

    def test_build_production_services_can_be_wired_into_cli_app(self) -> None:
        app = create_cli_app(services=build_production_services(runtime_store=self._new_store()))
        runner = CliRunner()

        result = runner.invoke(app, ["strategy", "list"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("strategy", result.stdout.lower())

    def test_build_contract_gateway_from_web3_creates_web3_backed_gateway(self) -> None:
        gateway = build_contract_gateway_from_web3(
            web3=object(),
            contract=object(),
            tx_sender="0x0000000000000000000000000000000000000001",
        )

        self.assertIsInstance(gateway, ContractGateway)

    def test_build_cryptoagents_decision_adapter_supports_explicit_runner_injection(self) -> None:
        fake_runner = object()
        adapter = build_cryptoagents_decision_adapter(runner=fake_runner)

        self.assertIs(getattr(adapter, "_runner"), fake_runner)

    def test_build_cryptoagents_decision_adapter_uses_production_runner_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            adapter = build_cryptoagents_decision_adapter()

        self.assertEqual(getattr(adapter, "_runner").__class__.__name__, "ProductionCryptoAgentsRunner")

    def test_build_cryptoagents_decision_adapter_uses_strict_runner_when_flag_is_set(self) -> None:
        with patch.dict(os.environ, {"REACTIVE_DECISION_STRICT": "true"}, clear=False):
            adapter = build_cryptoagents_decision_adapter()

        self.assertEqual(getattr(adapter, "_runner").__class__.__name__, "ProductionCryptoAgentsRunner")

    def test_build_cryptoagents_decision_adapter_rejects_invalid_strict_flag(self) -> None:
        with patch.dict(os.environ, {"REACTIVE_DECISION_STRICT": "maybe"}, clear=False):
            with self.assertRaises(RouteBindingMissingError):
                build_cryptoagents_decision_adapter()

    def test_build_execution_force_close_handler_calls_runtime_gateway(self) -> None:
        gateway = _FakeForceCloseGateway()
        handler = build_execution_force_close_handler(
            contract_gateway=gateway,
            max_slippage_bps=300,
        )

        result = json.loads(handler("0x" + "1" * 64))

        self.assertEqual(gateway.calls, [("0x" + "1" * 64, 300)])
        self.assertEqual(result["tx_hash"], "0x" + "4" * 64)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["block_number"], 123)

    def test_build_contract_gateway_from_runtime_env_requires_private_key_and_contract_address(self) -> None:
        env = {"SEPOLIA_RPC_URL": "http://127.0.0.1:8545"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RouteBindingMissingError):
                build_contract_gateway_from_runtime_env()

    def test_build_contract_gateway_from_runtime_env_rejects_invalid_artifact_json(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            artifact_path = Path(tmp_dir) / "artifact.json"
            artifact_path.write_text("{invalid-json", encoding="utf-8")
            env = {
                "SEPOLIA_RPC_URL": "http://127.0.0.1:8545",
                "SEPOLIA_PRIVATE_KEY": "0x" + "1" * 64,
                "REACTIVE_INVESTMENT_COMPILER_ADDRESS": "0x" + "2" * 40,
                "REACTIVE_INVESTMENT_COMPILER_ARTIFACT": str(artifact_path),
            }
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(RouteBindingMissingError):
                    build_contract_gateway_from_runtime_env()

    def test_build_chain_state_raises_when_rpc_fetch_fails_and_fallback_is_disabled(self) -> None:
        class _FailingEth:
            @staticmethod
            def get_block(_identifier):
                raise RuntimeError("rpc unavailable")

        class _FailingWeb3:
            eth = _FailingEth()

        gateway = SimpleNamespace(_client=SimpleNamespace(_web3=_FailingWeb3()))
        with self.assertRaises(CLISurfaceInputError):
            wiring_module._build_chain_state(contract_gateway=gateway, allow_fallback=False)

    def test_build_chain_state_falls_back_when_rpc_fetch_fails_in_fallback_mode(self) -> None:
        class _FailingEth:
            @staticmethod
            def get_block(_identifier):
                raise RuntimeError("rpc unavailable")

        class _FailingWeb3:
            eth = _FailingEth()

        gateway = SimpleNamespace(_client=SimpleNamespace(_web3=_FailingWeb3()))
        snapshot = wiring_module._build_chain_state(contract_gateway=gateway, allow_fallback=True)
        self.assertGreater(snapshot.block_number, 0)

    def test_build_registration_context_raises_when_required_fields_missing(self) -> None:
        strategy_record = SimpleNamespace(registration_context={})
        with self.assertRaises(CLISurfaceInputError):
            wiring_module._build_registration_context(
                strategy_record=strategy_record,
                intent_id="0x" + "1" * 64,
                contract_gateway=None,
            )

    def test_build_main_chain_request_requires_runtime_request_json_when_not_injected(self) -> None:
        store = self._new_store()
        store.create_strategy(
            strategy_id="strat-ctx-001",
            template={
                "template_id": "tpl-001",
                "version": 1,
                "auto_allowed_pairs": ["ETH/USDC"],
                "manual_allowed_pairs": [],
                "auto_allowed_dexes": ["uniswap_v3"],
                "manual_allowed_dexes": [],
                "auto_max_position_usd": "5000",
                "hard_max_position_usd": "10000",
                "auto_max_slippage_bps": 30,
                "hard_max_slippage_bps": 100,
                "auto_stop_loss_bps_range": {"min_bps": 50, "max_bps": 200},
                "manual_stop_loss_bps_range": {"min_bps": 20, "max_bps": 300},
                "auto_take_profit_bps_range": {"min_bps": 100, "max_bps": 600},
                "manual_take_profit_bps_range": {"min_bps": 50, "max_bps": 1200},
                "auto_daily_trade_limit": 2,
                "hard_daily_trade_limit": 8,
                "execution_mode": "conditional",
            },
            constraints={
                "pair": "ETH/USDC",
                "dex": "uniswap_v3",
                "max_position_usd": "5000",
                "max_slippage_bps": 30,
                "stop_loss_bps": 150,
                "take_profit_bps": 300,
                "ttl_seconds": 3600,
                "daily_trade_limit": 2,
            },
            registration_context={
                "owner": "0x0000000000000000000000000000000000000001",
                "input_token": "0x0000000000000000000000000000000000000002",
                "output_token": "0x0000000000000000000000000000000000000003",
            },
        )

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RouteBindingMissingError):
                wiring_module._build_main_chain_request_for_strategy(
                    strategy_id="strat-ctx-001",
                    runtime_store=store,
                    contract_gateway=object(),
                )

    def test_build_main_chain_request_requires_strategy_record_in_runtime_store(self) -> None:
        request_payload = {
            "decision_context": {
                "market_trend": {"direction": "up", "confidence_score": "0.7", "timeframe_minutes": 60},
                "capital_flow": {
                    "net_inflow_usd": "1000",
                    "volume_24h_usd": "10000",
                    "whale_inflow_usd": "200",
                    "retail_inflow_usd": "800",
                },
                "liquidity_depth": {"pair": "ETH/USDC", "dex": "uniswap_v3", "depth_usd_2pct": "100000", "total_tvl_usd": "1000000"},
                "onchain_flow": {"active_address_delta_24h": 10, "transaction_count_24h": 100, "gas_price_gwei": "20"},
                "risk_state": {"volatility_annualized": "0.4", "var_95_usd": "100", "correlation_to_market": "0.5"},
                "position_state": {"current_position_usd": "0", "unrealized_pnl_usd": "0"},
                "execution_state": {"daily_trades_executed": 0, "daily_volume_usd": "0"},
                "strategy_constraints": {
                    "pair": "ETH/USDC",
                    "dex": "uniswap_v3",
                    "max_position_usd": "5000",
                    "max_slippage_bps": 30,
                    "stop_loss_bps": 150,
                    "take_profit_bps": 300,
                    "ttl_seconds": 3600,
                    "daily_trade_limit": 2,
                },
                "context_id": "ctx-missing",
            },
            "strategy_template": {
                "template_id": "tpl-eth-swing",
                "version": 1,
                "auto_allowed_pairs": ["ETH/USDC"],
                "manual_allowed_pairs": [],
                "auto_allowed_dexes": ["uniswap_v3"],
                "manual_allowed_dexes": [],
                "auto_max_position_usd": "5000",
                "hard_max_position_usd": "10000",
                "auto_max_slippage_bps": 30,
                "hard_max_slippage_bps": 100,
                "auto_stop_loss_bps_range": {"min_bps": 50, "max_bps": 200},
                "manual_stop_loss_bps_range": {"min_bps": 20, "max_bps": 300},
                "auto_take_profit_bps_range": {"min_bps": 100, "max_bps": 600},
                "manual_take_profit_bps_range": {"min_bps": 50, "max_bps": 1200},
                "auto_daily_trade_limit": 2,
                "hard_daily_trade_limit": 8,
            },
            "rpc_state_snapshot": {
                "block_number": 1,
                "block_timestamp": 1710000000,
                "input_token_usd_price": "1",
                "input_token_reserve": "1000000",
                "output_token_reserve": "500",
                "wallet_input_balance": "10000",
                "wallet_input_allowance": "10000",
                "base_fee_gwei": 20,
                "max_priority_fee_gwei": 2,
                "max_gas_price_gwei": 50,
                "estimated_gas_used": 230000,
                "native_token_usd_price": "3000",
                "expected_profit_usd": "100",
                "ttl_buffer_seconds": 60,
            },
            "chain_state": {
                "base_fee_gwei": 20,
                "max_priority_fee_gwei": 2,
                "block_number": 1,
                "block_timestamp": 1710000000,
                "input_token_decimals": 6,
                "output_token_decimals": 18,
                "input_output_price": "0.0005",
                "input_token_usd_price": "1",
            },
            "registration_context": {
                "intent_id": "0x" + "1" * 64,
                "owner": "0x0000000000000000000000000000000000000001",
                "input_token": "0x0000000000000000000000000000000000000002",
                "output_token": "0x0000000000000000000000000000000000000003",
            },
            "reactive_trigger": {
                "trigger_type": "entry",
                "intent_id": "0x" + "1" * 64,
                "trade_intent_id": "ti-ctx-missing",
                "metadata": {"observed_out": 1},
            },
        }
        store = self._new_store()
        with TemporaryDirectory() as tmp_dir:
            request_path = Path(tmp_dir) / "request.json"
            request_path.write_text(json.dumps(request_payload), encoding="utf-8")
            with patch.dict(
                os.environ,
                {"REACTIVE_MAINCHAIN_REQUEST_JSON": str(request_path)},
                clear=True,
            ):
                with self.assertRaises(CLISurfaceInputError):
                    wiring_module._build_main_chain_request_for_strategy(
                        strategy_id="ctx-missing",
                        runtime_store=store,
                        contract_gateway=object(),
                    )

    def test_build_production_services_provides_default_monitor_shadow_status(self) -> None:
        services = build_production_services(
            runtime_store=self._new_store(),
            decision_run_handler=lambda strategy_id: f"decision run wired: {strategy_id}",
            decision_dry_run_handler=lambda strategy_id: f"decision dry-run wired: {strategy_id}",
        )
        payload = json.loads(services.monitor_shadow_status())
        self.assertIn(payload["status"], {"healthy", "warning", "critical"})
        self.assertIn("tracked_intents", payload)
        self.assertIn("critical_alerts", payload)

    def test_build_production_services_default_monitor_alerts_reads_store_and_filters(self) -> None:
        store = self._new_store()
        now = datetime.now(tz=timezone.utc).isoformat()
        store.create_strategy(
            strategy_id="strat-monitor-001",
            template={"template_id": "tpl-monitor", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
        )
        store.save_intent_artifact(
            IntentArtifactRecord(
                intent_id="intent-monitor-001",
                strategy_id="strat-monitor-001",
                trade_intent_id="ti-monitor-001",
                approval_status="pending",
                approval_payload={
                    "trade_intent": {
                        "trade_intent_id": "ti-monitor-001",
                        "strategy_intent_id": "si-monitor-001",
                        "pair": "ETH/USDC",
                        "dex": "uniswap_v3",
                        "position_usd": "1000",
                        "max_slippage_bps": 20,
                        "stop_loss_bps": 90,
                        "take_profit_bps": 250,
                        "entry_conditions": ["price_below:3000"],
                        "ttl_seconds": 3600,
                    },
                    "decision_meta": {
                        "trade_intent_id": "ti-monitor-001",
                        "created_at": now,
                        "ttl_seconds": 3600,
                        "ttl_source": "trade_intent.ttl_seconds",
                    },
                },
                machine_truth_json='{"decision_artifact":{},"execution_record":{}}',
                execution_record={
                    "status": "executed",
                    "chain_receipt": {"tx_hash": "0x" + "2" * 64, "status": "success", "block_number": 1, "logs": []},
                },
                export_markdown="# Audit",
                export_memo="# Memo",
                monitor_alerts=[
                    {
                        "code": "SHADOW_MONITOR_WARN",
                        "severity": "warning",
                        "message": "warn",
                        "source": "shadow_monitor",
                        "escalation_required": False,
                    },
                    {
                        "code": "SHADOW_MONITOR_CRIT",
                        "severity": "critical",
                        "message": "crit",
                        "source": "shadow_monitor",
                        "escalation_required": True,
                    },
                ],
                monitor_status={"status": "warning"},
                created_at=now,
                updated_at=now,
            )
        )

        services = build_production_services(
            runtime_store=store,
            decision_run_handler=lambda strategy_id: f"decision run wired: {strategy_id}",
            decision_dry_run_handler=lambda strategy_id: f"decision dry-run wired: {strategy_id}",
        )

        all_alerts = services.monitor_alerts(False)
        critical_only = services.monitor_alerts(True)
        self.assertEqual(len(all_alerts), 2)
        self.assertEqual(len(critical_only), 1)
        self.assertEqual(critical_only[0].code, "SHADOW_MONITOR_CRIT")

    def test_approval_show_raw_ignores_machine_truth_override(self) -> None:
        store = self._new_store()
        store.create_strategy(
            strategy_id="strat-001",
            template={"template_id": "tpl-001", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
        )
        now = datetime.now(tz=timezone.utc).isoformat()
        store.save_intent_artifact(
            IntentArtifactRecord(
                intent_id="intent-001",
                strategy_id="strat-001",
                trade_intent_id="ti-001",
                approval_status="pending",
                approval_payload={
                    "trade_intent": {
                        "trade_intent_id": "ti-001",
                        "strategy_intent_id": "si-001",
                        "pair": "ETH/USDC",
                        "dex": "uniswap_v3",
                        "position_usd": "1000",
                        "max_slippage_bps": 20,
                        "stop_loss_bps": 100,
                        "take_profit_bps": 250,
                        "entry_conditions": ["price_below:3000"],
                        "ttl_seconds": 3600,
                    },
                    "execution_plan": {
                        "trade_intent_id": "ti-001",
                        "register_payload": {
                            "intentId": "0x" + "1" * 64,
                            "owner": "0x0000000000000000000000000000000000000001",
                            "inputToken": "0x0000000000000000000000000000000000000002",
                            "outputToken": "0x0000000000000000000000000000000000000003",
                            "plannedEntrySize": 1000,
                            "entryAmountOutMinimum": 1,
                            "entryValidUntil": 4102444800,
                            "maxGasPriceGwei": 50,
                            "stopLossSlippageBps": 100,
                            "takeProfitSlippageBps": 250,
                        },
                        "hard_constraints": {
                            "max_slippage_bps": 20,
                            "ttl_seconds": 3600,
                            "stop_loss_bps": 100,
                            "take_profit_bps": 250,
                        },
                    },
                    "validation_result": {
                        "is_valid": True,
                        "validated_objects": ["StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan"],
                        "issues": [],
                        "contract_bindings": [],
                    },
                    "decision_meta": {
                        "trade_intent_id": "ti-001",
                        "created_at": now,
                        "ttl_seconds": 3600,
                        "ttl_source": "trade_intent.ttl_seconds",
                    },
                },
                machine_truth_json='{"intent_id":"intent-001","source":"store"}',
                execution_record={
                    "status": "executed",
                    "chain_receipt": {"tx_hash": "0x" + "2" * 64, "status": "success", "block_number": 1, "logs": []},
                },
                export_markdown="# Audit",
                export_memo="# Memo",
                monitor_alerts=[],
                monitor_status={"status": "healthy"},
                created_at=now,
                updated_at=now,
            )
        )
        services = build_production_services(
            runtime_store=store,
            decision_run_handler=lambda strategy_id: f"decision run wired: {strategy_id}",
            decision_dry_run_handler=lambda strategy_id: f"decision dry-run wired: {strategy_id}",
            monitor_alerts_handler=lambda _critical_only: [],
            monitor_shadow_status_handler=lambda: json.dumps(
                {"status": "healthy", "tracked_intents": 1, "critical_alerts": 0},
                ensure_ascii=False,
            ),
        )

        result = services.approval_show("intent-001", True, '{"intent_id":"attacker"}')
        self.assertIn('{"intent_id":"intent-001","source":"store"}', result)
        self.assertNotIn('{"intent_id":"attacker"}', result)

    def test_approval_status_transition_allows_only_pending_to_terminal(self) -> None:
        store = self._new_store()
        store.create_strategy(
            strategy_id="strat-001",
            template={"template_id": "tpl-001", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
        )
        now = datetime.now(tz=timezone.utc).isoformat()
        store.save_intent_artifact(
            IntentArtifactRecord(
                intent_id="intent-001",
                strategy_id="strat-001",
                trade_intent_id="ti-001",
                approval_status="pending",
                approval_payload={
                    "trade_intent": {
                        "trade_intent_id": "ti-001",
                        "strategy_intent_id": "si-001",
                        "pair": "ETH/USDC",
                        "dex": "uniswap_v3",
                        "position_usd": "1000",
                        "max_slippage_bps": 20,
                        "stop_loss_bps": 100,
                        "take_profit_bps": 250,
                        "entry_conditions": ["price_below:3000"],
                        "ttl_seconds": 3600,
                    },
                    "execution_plan": {
                        "trade_intent_id": "ti-001",
                        "register_payload": {
                            "intentId": "0x" + "1" * 64,
                            "owner": "0x0000000000000000000000000000000000000001",
                            "inputToken": "0x0000000000000000000000000000000000000002",
                            "outputToken": "0x0000000000000000000000000000000000000003",
                            "plannedEntrySize": 1000,
                            "entryAmountOutMinimum": 1,
                            "entryValidUntil": 4102444800,
                            "maxGasPriceGwei": 50,
                            "stopLossSlippageBps": 100,
                            "takeProfitSlippageBps": 250,
                        },
                        "hard_constraints": {
                            "max_slippage_bps": 20,
                            "ttl_seconds": 3600,
                            "stop_loss_bps": 100,
                            "take_profit_bps": 250,
                        },
                    },
                    "validation_result": {
                        "is_valid": True,
                        "validated_objects": ["StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan"],
                        "issues": [],
                        "contract_bindings": [],
                    },
                    "decision_meta": {
                        "trade_intent_id": "ti-001",
                        "created_at": now,
                        "ttl_seconds": 3600,
                        "ttl_source": "trade_intent.ttl_seconds",
                    },
                },
                machine_truth_json='{"intent_id":"intent-001"}',
                execution_record={
                    "status": "executed",
                    "chain_receipt": {"tx_hash": "0x" + "2" * 64, "status": "success", "block_number": 1, "logs": []},
                },
                export_markdown="# Audit",
                export_memo="# Memo",
                monitor_alerts=[],
                monitor_status={"status": "healthy"},
                created_at=now,
                updated_at=now,
            )
        )
        services = build_production_services(
            runtime_store=store,
            decision_run_handler=lambda strategy_id: f"decision run wired: {strategy_id}",
            decision_dry_run_handler=lambda strategy_id: f"decision dry-run wired: {strategy_id}",
            monitor_alerts_handler=lambda _critical_only: [],
            monitor_shadow_status_handler=lambda: json.dumps(
                {"status": "healthy", "tracked_intents": 1, "critical_alerts": 0},
                ensure_ascii=False,
            ),
        )

        services.approval_approve("intent-001")
        with self.assertRaises(CLISurfaceInputError):
            services.approval_reject("intent-001", "manual")

    def test_default_cli_app_decision_run_no_longer_returns_todo_placeholder(self) -> None:
        runner = CliRunner()
        with patch.dict(os.environ, {}, clear=True):
            app = create_default_cli_app()
            result = runner.invoke(app, ["decision", "run", "--strategy", "ctx-001"])

        self.assertEqual(result.exit_code, 2)
        self.assertNotIn('"status": "todo"', result.stdout)
        self.assertIn("decision.run requires runtime ContractGateway wiring", result.stdout)

    def test_decision_dry_run_handler_reads_runtime_request_json(self) -> None:
        request_payload = {
            "decision_context": {
                "market_trend": {"direction": "up", "confidence_score": "0.7", "timeframe_minutes": 60},
                "capital_flow": {
                    "net_inflow_usd": "1000",
                    "volume_24h_usd": "10000",
                    "whale_inflow_usd": "200",
                    "retail_inflow_usd": "800",
                },
                "liquidity_depth": {"pair": "ETH/USDC", "dex": "uniswap_v3", "depth_usd_2pct": "100000", "total_tvl_usd": "1000000"},
                "onchain_flow": {"active_address_delta_24h": 10, "transaction_count_24h": 100, "gas_price_gwei": "20"},
                "risk_state": {"volatility_annualized": "0.4", "var_95_usd": "100", "correlation_to_market": "0.5"},
                "position_state": {"current_position_usd": "0", "unrealized_pnl_usd": "0"},
                "execution_state": {"daily_trades_executed": 0, "daily_volume_usd": "0"},
                "strategy_constraints": {
                    "pair": "ETH/USDC",
                    "dex": "uniswap_v3",
                    "max_position_usd": "5000",
                    "max_slippage_bps": 30,
                    "stop_loss_bps": 150,
                    "take_profit_bps": 300,
                    "ttl_seconds": 3600,
                    "daily_trade_limit": 2,
                },
                "context_id": "ctx-001",
            },
            "strategy_template": {
                "template_id": "tpl-eth-swing",
                "version": 1,
                "auto_allowed_pairs": ["ETH/USDC"],
                "manual_allowed_pairs": [],
                "auto_allowed_dexes": ["uniswap_v3"],
                "manual_allowed_dexes": [],
                "auto_max_position_usd": "5000",
                "hard_max_position_usd": "10000",
                "auto_max_slippage_bps": 30,
                "hard_max_slippage_bps": 100,
                "auto_stop_loss_bps_range": {"min_bps": 50, "max_bps": 200},
                "manual_stop_loss_bps_range": {"min_bps": 20, "max_bps": 300},
                "auto_take_profit_bps_range": {"min_bps": 100, "max_bps": 600},
                "manual_take_profit_bps_range": {"min_bps": 50, "max_bps": 1200},
                "auto_daily_trade_limit": 2,
                "hard_daily_trade_limit": 8,
            },
            "rpc_state_snapshot": {
                "block_number": 1,
                "block_timestamp": 1710000000,
                "input_token_usd_price": "1",
                "input_token_reserve": "1000000",
                "output_token_reserve": "500",
                "wallet_input_balance": "10000",
                "wallet_input_allowance": "10000",
                "base_fee_gwei": 20,
                "max_priority_fee_gwei": 2,
                "max_gas_price_gwei": 50,
                "estimated_gas_used": 230000,
                "native_token_usd_price": "3000",
                "expected_profit_usd": "100",
                "ttl_buffer_seconds": 60,
            },
            "chain_state": {
                "base_fee_gwei": 20,
                "max_priority_fee_gwei": 2,
                "block_number": 1,
                "block_timestamp": 1710000000,
                "input_token_decimals": 6,
                "output_token_decimals": 18,
                "input_output_price": "0.0005",
                "input_token_usd_price": "1",
            },
            "registration_context": {
                "intent_id": "0x" + "1" * 64,
                "owner": "0x0000000000000000000000000000000000000001",
                "input_token": "0x0000000000000000000000000000000000000002",
                "output_token": "0x0000000000000000000000000000000000000003",
            },
            "reactive_trigger": {
                "trigger_type": "entry",
                "intent_id": "0x" + "1" * 64,
                "trade_intent_id": "ti-ctx-001",
                "metadata": {"observed_out": 1},
            },
        }

        with TemporaryDirectory() as tmp_dir:
            request_path = Path(tmp_dir) / "request.json"
            request_path.write_text(json.dumps(request_payload), encoding="utf-8")
            store = self._new_store()
            store.create_strategy(
                strategy_id="ctx-001",
                template=request_payload["strategy_template"],
                constraints=request_payload["decision_context"]["strategy_constraints"],
                registration_context=request_payload["registration_context"],
            )
            with patch.dict(
                os.environ,
                {"REACTIVE_MAINCHAIN_REQUEST_JSON": str(request_path)},
                clear=True,
            ):
                handler = build_decision_dry_run_handler_from_runtime_env(
                    runtime_store=store,
                    decision_adapter=_FakeDecisionAdapterForDryRun()
                )
                payload = json.loads(handler("ctx-001"))

        self.assertEqual(payload["strategy_id"], "ctx-001")
        self.assertEqual(payload["trade_intent"]["pair"], "ETH/USDC")


if __name__ == "__main__":
    unittest.main()
