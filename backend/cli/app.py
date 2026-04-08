from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

import typer
from rich.console import Console
from rich.panel import Panel

from .errors import CLISurfaceError, CLISurfaceInputError, RouteBindingMissingError
from .views.alerts import AlertView, build_alerts_table, render_alerts_snapshot


StrategyListHandler = Callable[[], str]
DecisionRunHandler = Callable[[str], str]
ApprovalShowHandler = Callable[[bool, str | None], str]
ApprovalApproveHandler = Callable[[str], str]
ApprovalRejectHandler = Callable[[str, str], str]
ExecutionStatusHandler = Callable[[str], str]
ExportBundleHandler = Callable[[str], str]
MonitorAlertsHandler = Callable[[bool], Sequence[AlertView]]


def _missing_binding(route: str) -> Callable[..., object]:
    def _raise_missing(*_args: object, **_kwargs: object) -> object:
        raise RouteBindingMissingError(
            f"TODO: CLI route `{route}` 未绑定服务适配器。请在 CLI surface 中显式注入 interface/adapter。"
        )

    return _raise_missing


@dataclass(frozen=True)
class CLISurfaceServices:
    strategy_list: StrategyListHandler = field(default_factory=lambda: _missing_binding("strategy.list"))
    decision_run: DecisionRunHandler = field(default_factory=lambda: _missing_binding("decision.run"))
    approval_show: ApprovalShowHandler = field(default_factory=lambda: _missing_binding("approval.show"))
    approval_approve: ApprovalApproveHandler = field(default_factory=lambda: _missing_binding("approval.approve"))
    approval_reject: ApprovalRejectHandler = field(default_factory=lambda: _missing_binding("approval.reject"))
    execution_status: ExecutionStatusHandler = field(default_factory=lambda: _missing_binding("execution.status"))
    export_bundle: ExportBundleHandler = field(default_factory=lambda: _missing_binding("export.bundle"))
    monitor_alerts: MonitorAlertsHandler = field(default_factory=lambda: _missing_binding("monitor.alerts"))


def create_cli_app(
    *,
    services: CLISurfaceServices | None = None,
    console: Console | None = None,
) -> typer.Typer:
    routed_services = services or CLISurfaceServices()
    render_console = console or Console()
    app = typer.Typer(help="Reactive DeFi CLI surface")

    strategy_app = typer.Typer(help="Strategy commands")
    decision_app = typer.Typer(help="Decision commands")
    approval_app = typer.Typer(help="Approval commands")
    execution_app = typer.Typer(help="Execution commands")
    export_app = typer.Typer(help="Export commands")
    monitor_app = typer.Typer(help="Monitor commands")

    @strategy_app.command("list")
    def strategy_list() -> None:
        _print_result(
            render_console,
            "strategy.list",
            _invoke_route_or_exit(render_console, routed_services.strategy_list),
        )

    @decision_app.command("run")
    def decision_run(
        context_id: str = typer.Option(..., "--context-id", help="Decision context id"),
    ) -> None:
        _print_result(
            render_console,
            "decision.run",
            _invoke_route_or_exit(render_console, routed_services.decision_run, context_id),
        )

    @approval_app.command("show")
    def approval_show(
        raw: bool = typer.Option(False, "--raw", help="Show machine truth JSON directly"),
        machine_truth_json: str | None = typer.Option(
            None,
            "--machine-truth-json",
            help="Machine Truth JSON when --raw is enabled",
        ),
    ) -> None:
        if raw and machine_truth_json is None:
            _raise_cli_error(
                render_console,
                CLISurfaceInputError("`approval show --raw` requires `--machine-truth-json`."),
            )
        _print_result(
            render_console,
            "approval.show",
            _invoke_route_or_exit(render_console, routed_services.approval_show, raw, machine_truth_json),
        )

    @approval_app.command("approve")
    def approval_approve(
        trade_intent_id: str = typer.Option(..., "--trade-intent-id", help="Trade intent id"),
    ) -> None:
        _print_result(
            render_console,
            "approval.approve",
            _invoke_route_or_exit(render_console, routed_services.approval_approve, trade_intent_id),
        )

    @approval_app.command("reject")
    def approval_reject(
        trade_intent_id: str = typer.Option(..., "--trade-intent-id", help="Trade intent id"),
        reason: str = typer.Option(..., "--reason", help="Explicit operator rejection reason"),
    ) -> None:
        _print_result(
            render_console,
            "approval.reject",
            _invoke_route_or_exit(render_console, routed_services.approval_reject, trade_intent_id, reason),
        )

    @execution_app.command("status")
    def execution_status(
        trade_intent_id: str = typer.Option(..., "--trade-intent-id", help="Trade intent id"),
    ) -> None:
        _print_result(
            render_console,
            "execution.status",
            _invoke_route_or_exit(render_console, routed_services.execution_status, trade_intent_id),
        )

    @export_app.command("bundle")
    def export_bundle(
        trade_intent_id: str = typer.Option(..., "--trade-intent-id", help="Trade intent id"),
    ) -> None:
        _print_result(
            render_console,
            "export.bundle",
            _invoke_route_or_exit(render_console, routed_services.export_bundle, trade_intent_id),
        )

    @monitor_app.command("alerts")
    def monitor_alerts(
        critical_only: bool = typer.Option(
            False,
            "--critical-only",
            help="Only show critical alerts",
        ),
    ) -> None:
        alerts = _invoke_route_or_exit(render_console, routed_services.monitor_alerts, critical_only)
        render_console.print(build_alerts_table(alerts))
        render_console.print(render_alerts_snapshot(alerts))

    app.add_typer(strategy_app, name="strategy")
    app.add_typer(decision_app, name="decision")
    app.add_typer(approval_app, name="approval")
    app.add_typer(execution_app, name="execution")
    app.add_typer(export_app, name="export")
    app.add_typer(monitor_app, name="monitor")
    return app


def _invoke_route_or_exit(console: Console, handler: Callable[..., object], *args: object) -> object:
    try:
        return handler(*args)
    except CLISurfaceError as exc:
        _raise_cli_error(console, exc)


def _print_result(console: Console, route: str, result: object) -> None:
    message = str(result)
    console.print(
        Panel.fit(
            message,
            title=f"Route: {route}",
            border_style="cyan",
        )
    )


def _raise_cli_error(console: Console, error: CLISurfaceError) -> None:
    console.print(
        Panel.fit(
            str(error),
            title="CLI Surface Error",
            border_style="red",
        )
    )
    raise typer.Exit(code=2)


app = create_cli_app()
