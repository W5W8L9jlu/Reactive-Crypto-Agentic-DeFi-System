from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.cli.runtime_store import CLIRuntimeStore, IntentArtifactRecord


class CLIRuntimeStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "cli_state.db"
        self.store = CLIRuntimeStore(db_path=self.db_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_create_list_get_update_strategy(self) -> None:
        created = self.store.create_strategy(
            strategy_id="strat-001",
            template={"template_id": "tpl-001", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
            memo_brief="hello",
        )

        self.assertEqual(created.strategy_id, "strat-001")
        self.assertEqual(len(self.store.list_strategies()), 1)
        loaded = self.store.get_strategy("strat-001")
        self.assertEqual(loaded.constraints["pair"], "ETH/USDC")

        updated = self.store.update_strategy(
            "strat-001",
            constraints={"pair": "WBTC/USDC", "dex": "uniswap_v3"},
        )
        self.assertEqual(updated.constraints["pair"], "WBTC/USDC")
        self.assertNotEqual(updated.updated_at, created.updated_at)

    def test_get_strategy_raises_key_error_when_missing(self) -> None:
        with self.assertRaises(KeyError):
            self.store.get_strategy("missing")

    def test_save_and_query_intent_artifact(self) -> None:
        self.store.create_strategy(
            strategy_id="strat-001",
            template={"template_id": "tpl-001", "version": 1},
            constraints={"pair": "ETH/USDC", "dex": "uniswap_v3"},
            registration_context={"input_token": "0x1", "output_token": "0x2"},
        )
        now = datetime.now(tz=timezone.utc).isoformat()
        record = IntentArtifactRecord(
            intent_id="0x" + "1" * 64,
            strategy_id="strat-001",
            trade_intent_id="ti-001",
            approval_status="pending",
            approval_payload={"trade_intent": {"trade_intent_id": "ti-001"}},
            machine_truth_json='{"decision_artifact":{},"execution_record":{}}',
            execution_record={"status": "executed"},
            export_markdown="# Audit",
            export_memo="# Memo",
            monitor_alerts=[],
            monitor_status={"status": "healthy"},
            created_at=now,
            updated_at=now,
        )
        saved = self.store.save_intent_artifact(record)
        self.assertEqual(saved.intent_id, record.intent_id)
        self.assertEqual(len(self.store.list_pending_approval_intents()), 1)

        approved = self.store.set_approval_status(intent_id=record.intent_id, approval_status="approved")
        self.assertEqual(approved.approval_status, "approved")
        self.assertEqual(len(self.store.list_pending_approval_intents()), 0)

    def test_set_approval_status_raises_key_error_when_missing(self) -> None:
        with self.assertRaises(KeyError):
            self.store.set_approval_status(intent_id="0x" + "f" * 64, approval_status="approved")


if __name__ == "__main__":
    unittest.main()
