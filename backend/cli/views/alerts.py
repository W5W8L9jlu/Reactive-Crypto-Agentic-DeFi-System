from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence

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
    intent_id: Optional[str] = None
    observed_price: Optional[str] = None
    threshold_price: Optional[str] = None
    breach_blocks: Optional[int] = None
    estimated_additional_loss_usd: Optional[str] = None
    detected_at: Optional[datetime] = None


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


def build_critical_force_close_banner(alert: AlertView) -> str:
    if alert.intent_id is None:
        return "CRITICAL ALERT: missing intent id for force-close command"
    observed_price = alert.observed_price or "not-verified"
    threshold_price = alert.threshold_price or "not-verified"
    breach_blocks = str(alert.breach_blocks) if alert.breach_blocks is not None else "not-verified"
    estimated_loss = alert.estimated_additional_loss_usd or "not-verified"
    return (
        "=====================================================================\n"
        "CRITICAL ALERT: 影子监控器触发防线击穿警报！\n"
        "=====================================================================\n"
        f"[意图 ID] {alert.intent_id}\n"
        f"[致命异常] 现价 ${observed_price} 已突破阈值 (${threshold_price}) 达 {breach_blocks} 个区块\n"
        f"[预估额外损失] -${estimated_loss}\n"
        "可执行紧急预案：\n"
        f"agent-cli execution force-close {alert.intent_id}\n"
        "====================================================================="
    )


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
    "build_critical_force_close_banner",
    "render_alerts_snapshot",
]

