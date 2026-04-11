from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class StrategyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy_id: str = Field(min_length=1)
    template: dict[str, Any]
    constraints: dict[str, Any]
    registration_context: dict[str, Any]
    memo_brief: str | None = None
    created_at: str
    updated_at: str


class IntentArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    trade_intent_id: str = Field(min_length=1)
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    approval_payload: dict[str, Any]
    machine_truth_json: str = Field(min_length=2)
    execution_record: dict[str, Any]
    export_markdown: str
    export_memo: str
    monitor_alerts: list[dict[str, Any]] = Field(default_factory=list)
    monitor_status: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class CLIRuntimeStore:
    def __init__(self, *, db_path: str | Path) -> None:
        self._db_path = Path(db_path).expanduser().resolve()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def create_strategy(
        self,
        *,
        strategy_id: str,
        template: dict[str, Any],
        constraints: dict[str, Any],
        registration_context: dict[str, Any],
        memo_brief: str | None = None,
    ) -> StrategyRecord:
        now = _utc_now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO strategies (
                    strategy_id,
                    template_json,
                    constraints_json,
                    registration_context_json,
                    memo_brief,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    strategy_id,
                    _json_dumps(template),
                    _json_dumps(constraints),
                    _json_dumps(registration_context),
                    memo_brief,
                    now,
                    now,
                ),
            )
            conn.commit()
        return self.get_strategy(strategy_id)

    def list_strategies(self) -> list[StrategyRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    strategy_id,
                    template_json,
                    constraints_json,
                    registration_context_json,
                    memo_brief,
                    created_at,
                    updated_at
                FROM strategies
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [_row_to_strategy(row) for row in rows]

    def get_strategy(self, strategy_id: str) -> StrategyRecord:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    strategy_id,
                    template_json,
                    constraints_json,
                    registration_context_json,
                    memo_brief,
                    created_at,
                    updated_at
                FROM strategies
                WHERE strategy_id = ?
                """,
                (strategy_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"strategy not found: {strategy_id}")
        return _row_to_strategy(row)

    def update_strategy(
        self,
        strategy_id: str,
        *,
        template: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        registration_context: dict[str, Any] | None = None,
        memo_brief: str | None = None,
    ) -> StrategyRecord:
        existing = self.get_strategy(strategy_id)
        now = _utc_now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE strategies
                SET
                    template_json = ?,
                    constraints_json = ?,
                    registration_context_json = ?,
                    memo_brief = ?,
                    updated_at = ?
                WHERE strategy_id = ?
                """,
                (
                    _json_dumps(template if template is not None else existing.template),
                    _json_dumps(constraints if constraints is not None else existing.constraints),
                    _json_dumps(
                        registration_context
                        if registration_context is not None
                        else existing.registration_context
                    ),
                    memo_brief if memo_brief is not None else existing.memo_brief,
                    now,
                    strategy_id,
                ),
            )
            conn.commit()
        return self.get_strategy(strategy_id)

    def save_intent_artifact(self, record: IntentArtifactRecord) -> IntentArtifactRecord:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intent_artifacts (
                    intent_id,
                    strategy_id,
                    trade_intent_id,
                    approval_status,
                    approval_payload_json,
                    machine_truth_json,
                    execution_record_json,
                    export_markdown,
                    export_memo,
                    monitor_alerts_json,
                    monitor_status_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(intent_id) DO UPDATE SET
                    strategy_id = excluded.strategy_id,
                    trade_intent_id = excluded.trade_intent_id,
                    approval_status = excluded.approval_status,
                    approval_payload_json = excluded.approval_payload_json,
                    machine_truth_json = excluded.machine_truth_json,
                    execution_record_json = excluded.execution_record_json,
                    export_markdown = excluded.export_markdown,
                    export_memo = excluded.export_memo,
                    monitor_alerts_json = excluded.monitor_alerts_json,
                    monitor_status_json = excluded.monitor_status_json,
                    updated_at = excluded.updated_at
                """,
                (
                    record.intent_id,
                    record.strategy_id,
                    record.trade_intent_id,
                    record.approval_status,
                    _json_dumps(record.approval_payload),
                    record.machine_truth_json,
                    _json_dumps(record.execution_record),
                    record.export_markdown,
                    record.export_memo,
                    _json_dumps(record.monitor_alerts),
                    _json_dumps(record.monitor_status),
                    record.created_at,
                    record.updated_at,
                ),
            )
            conn.commit()
        return self.get_intent_artifact(record.intent_id)

    def get_intent_artifact(self, intent_id: str) -> IntentArtifactRecord:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    intent_id,
                    strategy_id,
                    trade_intent_id,
                    approval_status,
                    approval_payload_json,
                    machine_truth_json,
                    execution_record_json,
                    export_markdown,
                    export_memo,
                    monitor_alerts_json,
                    monitor_status_json,
                    created_at,
                    updated_at
                FROM intent_artifacts
                WHERE intent_id = ?
                """,
                (intent_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"intent artifact not found: {intent_id}")
        return _row_to_intent_artifact(row)

    def list_pending_approval_intents(self) -> list[IntentArtifactRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    intent_id,
                    strategy_id,
                    trade_intent_id,
                    approval_status,
                    approval_payload_json,
                    machine_truth_json,
                    execution_record_json,
                    export_markdown,
                    export_memo,
                    monitor_alerts_json,
                    monitor_status_json,
                    created_at,
                    updated_at
                FROM intent_artifacts
                WHERE approval_status = 'pending'
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [_row_to_intent_artifact(row) for row in rows]

    def list_intent_artifacts(self) -> list[IntentArtifactRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    intent_id,
                    strategy_id,
                    trade_intent_id,
                    approval_status,
                    approval_payload_json,
                    machine_truth_json,
                    execution_record_json,
                    export_markdown,
                    export_memo,
                    monitor_alerts_json,
                    monitor_status_json,
                    created_at,
                    updated_at
                FROM intent_artifacts
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [_row_to_intent_artifact(row) for row in rows]

    def set_approval_status(
        self,
        *,
        intent_id: str,
        approval_status: Literal["pending", "approved", "rejected"],
    ) -> IntentArtifactRecord:
        with self._connection() as conn:
            updated = conn.execute(
                """
                UPDATE intent_artifacts
                SET
                    approval_status = ?,
                    updated_at = ?
                WHERE intent_id = ?
                """,
                (approval_status, _utc_now_iso(), intent_id),
            )
            conn.commit()
        if updated.rowcount == 0:
            raise KeyError(f"intent artifact not found: {intent_id}")
        return self.get_intent_artifact(intent_id)

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS strategies (
                    strategy_id TEXT PRIMARY KEY,
                    template_json TEXT NOT NULL,
                    constraints_json TEXT NOT NULL,
                    registration_context_json TEXT NOT NULL,
                    memo_brief TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS intent_artifacts (
                    intent_id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    trade_intent_id TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    approval_payload_json TEXT NOT NULL,
                    machine_truth_json TEXT NOT NULL,
                    execution_record_json TEXT NOT NULL,
                    export_markdown TEXT NOT NULL,
                    export_memo TEXT NOT NULL,
                    monitor_alerts_json TEXT NOT NULL,
                    monitor_status_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connection(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()


def _row_to_strategy(row: sqlite3.Row) -> StrategyRecord:
    return StrategyRecord(
        strategy_id=row["strategy_id"],
        template=_json_loads(row["template_json"]),
        constraints=_json_loads(row["constraints_json"]),
        registration_context=_json_loads(row["registration_context_json"]),
        memo_brief=row["memo_brief"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_intent_artifact(row: sqlite3.Row) -> IntentArtifactRecord:
    return IntentArtifactRecord(
        intent_id=row["intent_id"],
        strategy_id=row["strategy_id"],
        trade_intent_id=row["trade_intent_id"],
        approval_status=row["approval_status"],
        approval_payload=_json_loads(row["approval_payload_json"]),
        machine_truth_json=row["machine_truth_json"],
        execution_record=_json_loads(row["execution_record_json"]),
        export_markdown=row["export_markdown"],
        export_memo=row["export_memo"],
        monitor_alerts=_json_loads(row["monitor_alerts_json"]),
        monitor_status=_json_loads(row["monitor_status_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_loads(value: str) -> Any:
    return json.loads(value)


__all__ = [
    "CLIRuntimeStore",
    "IntentArtifactRecord",
    "StrategyRecord",
]
