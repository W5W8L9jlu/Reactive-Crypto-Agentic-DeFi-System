from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .shadow_monitor import (
    ActivePositionIntent,
    BackupRPCSnapshot,
    ForceCloseRecommendation,
    MonitorAlert,
    ShadowMonitor,
    ShadowMonitorResult,
)


def _frozen_config() -> ConfigDict:
    return ConfigDict(extra="forbid", frozen=True)


class ActivePositionSourcePort(Protocol):
    def list_active_positions(self) -> Sequence[ActivePositionIntent | dict[str, Any]]: ...


class BackupRPCPort(Protocol):
    def get_position_snapshot(self, *, intent_id: str) -> BackupRPCSnapshot | dict[str, Any]: ...


class ReconciliationDaemonCycle(BaseModel):
    model_config = _frozen_config()

    started_at: datetime
    finished_at: datetime
    checked_positions: int = Field(ge=0)
    alerts: list[MonitorAlert] = Field(default_factory=list)
    force_close_recommendations: list[ForceCloseRecommendation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_time_window(self) -> "ReconciliationDaemonCycle":
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware")
        if self.finished_at.tzinfo is None or self.finished_at.utcoffset() is None:
            raise ValueError("finished_at must be timezone-aware")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must be >= started_at")
        return self


class ReconciliationDaemon:
    """
    Independent monitor daemon.

    It only reads ActivePosition intents and backup RPC snapshots, then emits alerts
    and force-close recommendations. It does not execute trades or callbacks.
    """

    def __init__(
        self,
        *,
        active_position_source: ActivePositionSourcePort,
        backup_rpc: BackupRPCPort,
        monitor: ShadowMonitor,
        poll_interval_seconds: int = 15,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        self._active_position_source = active_position_source
        self._backup_rpc = backup_rpc
        self._monitor = monitor
        self._poll_interval_seconds = poll_interval_seconds
        self._clock = clock or _utc_now
        self._sleeper = sleeper or time.sleep

    @property
    def poll_interval_seconds(self) -> int:
        return self._poll_interval_seconds

    def run_cycle(self) -> ReconciliationDaemonCycle:
        started_at = self._clock()
        raw_positions = self._active_position_source.list_active_positions()
        active_positions = [ActivePositionIntent.model_validate(item) for item in raw_positions]

        snapshots: list[BackupRPCSnapshot | dict[str, Any]] = []
        for position in active_positions:
            snapshots.append(
                self._backup_rpc.get_position_snapshot(intent_id=position.intent_id)
            )

        monitor_result: ShadowMonitorResult = self._monitor.reconcile_positions(
            active_positions=active_positions,
            snapshots=snapshots,
            checked_at=started_at,
        )
        finished_at = self._clock()
        return ReconciliationDaemonCycle(
            started_at=started_at,
            finished_at=finished_at,
            checked_positions=len(active_positions),
            alerts=monitor_result.alerts,
            force_close_recommendations=monitor_result.force_close_recommendations,
        )

    def run_forever(
        self,
        *,
        max_cycles: int | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> list[ReconciliationDaemonCycle]:
        if max_cycles is not None and max_cycles <= 0:
            raise ValueError("max_cycles must be > 0 when provided")

        completed_cycles: list[ReconciliationDaemonCycle] = []
        cycle_count = 0
        while True:
            if should_stop is not None and should_stop():
                break

            completed_cycles.append(self.run_cycle())
            cycle_count += 1
            if max_cycles is not None and cycle_count >= max_cycles:
                break

            self._sleeper(self._poll_interval_seconds)

        return completed_cycles


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


__all__ = [
    "ActivePositionSourcePort",
    "BackupRPCPort",
    "ReconciliationDaemon",
    "ReconciliationDaemonCycle",
]

