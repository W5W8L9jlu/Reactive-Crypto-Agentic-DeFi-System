from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MonitorAlertSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class MonitorAlertView(BaseModel):
    """CLI-facing alert view for the monitor surface."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    alert_id: str
    severity: MonitorAlertSeverity
    summary: str
    source: str
    grace_state: str = Field(min_length=1)
    requires_manual_action: bool = Field(default=False)
