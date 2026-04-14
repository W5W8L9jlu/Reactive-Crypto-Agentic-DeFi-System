from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.cli.runtime_store import CLIRuntimeStore, IntentArtifactRecord
from backend.cli.wiring import build_production_services


class Phase1GateCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = TemporaryDirectory()
        self.store = CLIRuntimeStore(db_path=Path(self.tmp_dir.name) / "cli_state.db")
        self.store.create_strategy(
            strategy_id="strat-001",
            template={"template_id": "tpl-001", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
        )
        now = datetime.now(tz=timezone.utc).isoformat()
        self.store.save_intent_artifact(
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
                machine_truth_json='{"decision_artifact":{"x":1},"execution_record":{"y":2}}',
                execution_record={
                    "status": "executed",
                    "chain_receipt": {"tx_hash": "0x" + "2" * 64, "status": "success", "block_number": 1, "logs": []},
                },
                export_markdown="# Audit Markdown Excerpt",
                export_memo="# Investment Memo",
                monitor_alerts=[],
                monitor_status={"status": "healthy"},
                created_at=now,
                updated_at=now,
            )
        )

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_strategy_and_export_routes_are_not_placeholder_outputs(self) -> None:
        services = build_production_services(
            runtime_store=self.store,
            decision_run_handler=lambda strategy_id: strategy_id,
            decision_dry_run_handler=lambda strategy_id: strategy_id,
        )

        strategy_list_payload = json.loads(services.strategy_list())
        self.assertIsInstance(strategy_list_payload, list)
        self.assertEqual(strategy_list_payload[0]["strategy_id"], "strat-001")
        self.assertNotIn("route ready", services.strategy_list())

        export_json_payload = json.loads(services.export_json("intent-001"))
        self.assertIn("decision_artifact", export_json_payload)
        self.assertIn("execution_record", export_json_payload)

    def test_monitor_shadow_status_returns_structured_status(self) -> None:
        services = build_production_services(
            runtime_store=self.store,
            decision_run_handler=lambda strategy_id: strategy_id,
            decision_dry_run_handler=lambda strategy_id: strategy_id,
            monitor_alerts_handler=lambda _critical_only: [],
            monitor_shadow_status_handler=lambda: json.dumps(
                {"status": "healthy", "tracked_intents": 1, "critical_alerts": 0},
                ensure_ascii=False,
            ),
        )

        payload = json.loads(services.monitor_shadow_status())
        self.assertIn(payload["status"], {"healthy", "critical"})
        self.assertEqual(payload["tracked_intents"], 1)


if __name__ == "__main__":
    unittest.main()
