from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .design_system import (
    ASCII_REACTIVE_AGENTS,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    build_module_statuses,
)
from .theme import resolve_cli_theme_from_env


@dataclass
class CLISurfaceRenderer:
    console: Console

    def print_success(self, route: str, result: object) -> None:
        theme = resolve_cli_theme_from_env()
        normalized_result = _normalize_result(result)
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="welcome", size=12),
            Layout(name="main", size=14),
            Layout(name="report"),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="progress"),
            Layout(name="messages"),
        )

        layout["welcome"].update(
            Panel(
                Text(ASCII_REACTIVE_AGENTS.strip("\n"), style=theme.primary),
                title=f"[{theme.title_style}]Welcome to ReactiveAgents[/]",
                border_style=theme.panel_border,
            )
        )
        layout["progress"].update(_build_progress_panel(route=route))
        layout["messages"].update(_build_messages_panel(route=route, result=normalized_result))
        layout["report"].update(
            Panel(
                normalized_result,
                title=f"[{theme.title_style}]Current Report[/]",
                border_style=theme.panel_border,
            )
        )
        layout["footer"].update(
            Panel(
                f"Route: {route} | Status: SUCCESS | Theme: {theme.name}",
                border_style=theme.secondary,
            )
        )
        self.console.print(layout)
        self.console.print(
            Panel.fit(
                normalized_result,
                title=f"Route: {route}",
                subtitle="Machine Truth Output",
                border_style=theme.panel_border,
            )
        )

    def print_error(self, error: Exception) -> None:
        theme = resolve_cli_theme_from_env()
        title = f"[bold {theme.error}]CLI Surface Error[/]"
        self.console.print(
            Panel.fit(
                str(error),
                title=title,
                border_style=theme.error_border,
            )
        )


def _build_progress_panel(*, route: str) -> Panel:
    theme = resolve_cli_theme_from_env()
    statuses = build_module_statuses(route=route)
    table = Table(show_header=True, box=None, expand=True)
    table.add_column("Module", style=theme.secondary)
    table.add_column("Status")
    for name, status in statuses.items():
        table.add_row(
            name,
            _render_status(status=status, theme=theme),
        )
    return Panel(
        table,
        title=f"[{theme.title_style}]Progress[/]",
        border_style=theme.panel_border,
    )


def _build_messages_panel(*, route: str, result: str) -> Panel:
    theme = resolve_cli_theme_from_env()
    now = datetime.now().strftime("%H:%M:%S")
    table = Table(show_header=True, box=None, expand=True)
    table.add_column("Time", width=10, style=theme.secondary)
    table.add_column("Type", width=10, style=theme.secondary)
    table.add_column("Content")
    table.add_row(now, "Route", route)
    table.add_row(now, "Output", _first_line(result))
    if "\n" in result:
        table.add_row(now, "Details", "multi-line report rendered below")
    return Panel(
        table,
        title=f"[{theme.title_style}]Messages & Tools[/]",
        border_style=theme.secondary,
    )


def _render_status(*, status: str, theme: Any) -> Text:
    if status == STATUS_COMPLETED:
        return Text(status, style=f"bold {theme.success}")
    if status == STATUS_IN_PROGRESS:
        return Text(status, style=f"bold {theme.warning}")
    if status == STATUS_PENDING:
        return Text(status, style=theme.muted)
    return Text(status, style=theme.muted)


def _normalize_result(result: object) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, indent=2)
    return str(result)


def _first_line(value: str) -> str:
    line = value.splitlines()[0] if value else ""
    return line[:120]
