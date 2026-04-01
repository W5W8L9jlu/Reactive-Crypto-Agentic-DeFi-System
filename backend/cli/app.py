from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Sequence

from .alerts import MonitorAlertView
from .errors import MissingCliAdapterError, MissingCliDependencyError, UnresolvedCliRouteError
from .models import ApprovalBattleCard
from .views import render_approval_battle_card_text, render_monitor_alerts_text

CommandHandler = Callable[..., Any]


class ExportArtifactKind(str, Enum):
    MACHINE_TRUTH_JSON = "machine_truth_json"
    AUDIT_MARKDOWN = "audit_markdown"
    INVESTMENT_MEMO = "investment_memo"


@dataclass(frozen=True)
class CommandRoute:
    group: str
    name: str
    help: str
    handler_name: str


@dataclass(frozen=True)
class CommandGroup:
    name: str
    help: str
    commands: tuple[CommandRoute, ...]


@dataclass(frozen=True)
class CliAdapters:
    strategy_show: CommandHandler | None = None
    decision_run: CommandHandler | None = None
    approval_show: CommandHandler | None = None
    approval_approve: CommandHandler | None = None
    approval_reject: CommandHandler | None = None
    execution_show: CommandHandler | None = None
    export_render: CommandHandler | None = None
    monitor_alerts: CommandHandler | None = None
    monitor_takeover: CommandHandler | None = None


COMMAND_GROUPS: tuple[CommandGroup, ...] = (
    CommandGroup(
        name="strategy",
        help="Strategy management entrypoints.",
        commands=(
            CommandRoute(
                group="strategy",
                name="show",
                help="Show the strategy surface through an explicit adapter.",
                handler_name="strategy_show",
            ),
        ),
    ),
    CommandGroup(
        name="decision",
        help="Decision run entrypoints.",
        commands=(
            CommandRoute(
                group="decision",
                name="run",
                help="Route into the decision run surface.",
                handler_name="decision_run",
            ),
        ),
    ),
    CommandGroup(
        name="approval",
        help="Manual approval surface.",
        commands=(
            CommandRoute(
                group="approval",
                name="show",
                help="Render ApprovalBattleCard from an explicit adapter.",
                handler_name="approval_show",
            ),
            CommandRoute(
                group="approval",
                name="approve",
                help="Manual approve entrypoint.",
                handler_name="approval_approve",
            ),
            CommandRoute(
                group="approval",
                name="reject",
                help="Manual reject entrypoint.",
                handler_name="approval_reject",
            ),
        ),
    ),
    CommandGroup(
        name="execution",
        help="Execution query surface.",
        commands=(
            CommandRoute(
                group="execution",
                name="show",
                help="Show execution state through an explicit adapter.",
                handler_name="execution_show",
            ),
        ),
    ),
    CommandGroup(
        name="export",
        help="Export surface for the three frozen artifact rails.",
        commands=(
            CommandRoute(
                group="export",
                name="render",
                help="Render machine_truth_json, audit_markdown, or investment_memo.",
                handler_name="export_render",
            ),
        ),
    ),
    CommandGroup(
        name="monitor",
        help="High-risk alert and manual takeover surface.",
        commands=(
            CommandRoute(
                group="monitor",
                name="alerts",
                help="Show monitor alerts through an explicit adapter.",
                handler_name="monitor_alerts",
            ),
            CommandRoute(
                group="monitor",
                name="takeover",
                help="Enter forced manual takeover through an explicit adapter.",
                handler_name="monitor_takeover",
            ),
        ),
    ),
)


def resolve_route(path: Sequence[str]) -> CommandRoute:
    if len(path) != 2:
        joined = " ".join(path) if path else "<empty>"
        raise UnresolvedCliRouteError(f"Unsupported CLI route: {joined}")

    group_name, command_name = path
    for group in COMMAND_GROUPS:
        if group.name != group_name:
            continue
        for command in group.commands:
            if command.name == command_name:
                return command

    raise UnresolvedCliRouteError(f"Unsupported CLI route: {group_name} {command_name}")


def _require_handler(adapters: CliAdapters, route: CommandRoute) -> CommandHandler:
    handler = getattr(adapters, route.handler_name)
    if handler is None:
        raise MissingCliAdapterError(
            f"TODO: wire an explicit adapter for '{route.group} {route.name}'. "
            "CLI surface only owns routing, presentation, and manual entrypoints."
        )
    return handler


def _render_result(result: Any, *, show_raw: bool = False) -> str:
    if isinstance(result, ApprovalBattleCard):
        return render_approval_battle_card_text(result, show_raw=show_raw)

    if isinstance(result, list) and all(isinstance(item, MonitorAlertView) for item in result):
        return render_monitor_alerts_text(result)

    if isinstance(result, tuple) and all(isinstance(item, MonitorAlertView) for item in result):
        return render_monitor_alerts_text(result)

    if result is None:
        return "TODO: adapter returned no CLI view."

    return str(result)


def _load_typer() -> Any:
    try:
        import typer
    except ModuleNotFoundError as exc:
        raise MissingCliDependencyError(
            "Typer is required to build the CLI app. Install 'typer' in the runtime environment."
        ) from exc
    return typer


def _load_console(console: Any | None) -> Any:
    if console is not None:
        return console

    try:
        from rich.console import Console
    except ModuleNotFoundError as exc:
        raise MissingCliDependencyError(
            "Rich is required to build the CLI app. Install 'rich' in the runtime environment."
        ) from exc

    return Console()


def build_app(
    *,
    adapters: CliAdapters | None = None,
    console: Any | None = None,
) -> Any:
    typer = _load_typer()
    rich_console = _load_console(console)
    wired_adapters = adapters or CliAdapters()

    def run_and_render(path: tuple[str, str], **kwargs: Any) -> None:
        route = resolve_route(path)
        handler = _require_handler(wired_adapters, route)
        handler_kwargs = dict(kwargs)
        show_raw = bool(handler_kwargs.pop("show_raw", False))
        rich_console.print(_render_result(handler(**handler_kwargs), show_raw=show_raw))

    def guarded(path: tuple[str, str], **kwargs: Any) -> None:
        try:
            run_and_render(path, **kwargs)
        except MissingCliAdapterError as exc:
            typer.echo(f"ERROR: {exc}", err=True)
            raise typer.Exit(code=2) from exc

    app = typer.Typer(
        help="CryptoAgents-inspired CLI surface for routing, display, and manual operations.",
        no_args_is_help=True,
        add_completion=False,
    )

    strategy_app = typer.Typer(help="Strategy management entrypoints.", no_args_is_help=True, add_completion=False)
    decision_app = typer.Typer(help="Decision run entrypoints.", no_args_is_help=True, add_completion=False)
    approval_app = typer.Typer(help="Manual approval surface.", no_args_is_help=True, add_completion=False)
    execution_app = typer.Typer(help="Execution query surface.", no_args_is_help=True, add_completion=False)
    export_app = typer.Typer(help="Export surface for frozen artifact rails.", no_args_is_help=True, add_completion=False)
    monitor_app = typer.Typer(help="High-risk alert surface.", no_args_is_help=True, add_completion=False)

    @strategy_app.command("show", help=resolve_route(("strategy", "show")).help)
    def strategy_show() -> None:
        guarded(("strategy", "show"))

    @decision_app.command("run", help=resolve_route(("decision", "run")).help)
    def decision_run() -> None:
        guarded(("decision", "run"))

    @approval_app.command("show", help=resolve_route(("approval", "show")).help)
    def approval_show(
        raw: bool = typer.Option(
            False,
            "--raw",
            help="Expose machine truth reference only through the explicit raw path.",
        ),
    ) -> None:
        guarded(("approval", "show"), show_raw=raw)

    @approval_app.command("approve", help=resolve_route(("approval", "approve")).help)
    def approval_approve() -> None:
        guarded(("approval", "approve"))

    @approval_app.command("reject", help=resolve_route(("approval", "reject")).help)
    def approval_reject() -> None:
        guarded(("approval", "reject"))

    @execution_app.command("show", help=resolve_route(("execution", "show")).help)
    def execution_show() -> None:
        guarded(("execution", "show"))

    @export_app.command("render", help=resolve_route(("export", "render")).help)
    def export_render(
        kind: ExportArtifactKind = typer.Option(
            ...,
            "--kind",
            case_sensitive=False,
            help="Frozen export rail to render.",
        ),
    ) -> None:
        guarded(("export", "render"), kind=kind)

    @monitor_app.command("alerts", help=resolve_route(("monitor", "alerts")).help)
    def monitor_alerts() -> None:
        guarded(("monitor", "alerts"))

    @monitor_app.command("takeover", help=resolve_route(("monitor", "takeover")).help)
    def monitor_takeover() -> None:
        guarded(("monitor", "takeover"))

    app.add_typer(strategy_app, name="strategy")
    app.add_typer(decision_app, name="decision")
    app.add_typer(approval_app, name="approval")
    app.add_typer(execution_app, name="execution")
    app.add_typer(export_app, name="export")
    app.add_typer(monitor_app, name="monitor")
    return app


def main() -> None:
    app = build_app()
    app()
