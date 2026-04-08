from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from rich.table import Table


class AlertSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class AlertView:
    code: str
    severity: AlertSeverity
    message: str
    source: str
    escalation_required: bool


def render_alerts_snapshot(alerts: Sequence[AlertView]) -> str:
    if not alerts:
        return "Active Alerts: none"

    lines = ["Active Alerts:"]
    for alert in _sorted_alerts(alerts):
        escalation = "yes" if alert.escalation_required else "no"
        lines.append(
            f"- [{alert.severity.value}] {alert.code} | source={alert.source} | escalation={escalation} | {alert.message}"
        )
    return "\n".join(lines)


def build_alerts_table(alerts: Sequence[AlertView]) -> Table:
    table = Table(title="Monitor Alerts", show_lines=False)
    table.add_column("Severity")
    table.add_column("Code")
    table.add_column("Source")
    table.add_column("Escalation")
    table.add_column("Message")

    if not alerts:
        table.add_row("-", "-", "-", "-", "No active alerts")
        return table

    for alert in _sorted_alerts(alerts):
        table.add_row(
            alert.severity.value,
            alert.code,
            alert.source,
            "yes" if alert.escalation_required else "no",
            alert.message,
        )
    return table


def _sorted_alerts(alerts: Sequence[AlertView]) -> list[AlertView]:
    rank = {
        AlertSeverity.CRITICAL: 0,
        AlertSeverity.WARNING: 1,
    }
    return sorted(alerts, key=lambda item: (rank[item.severity], item.code))


__all__ = [
    "AlertSeverity",
    "AlertView",
    "build_alerts_table",
    "render_alerts_snapshot",
]

