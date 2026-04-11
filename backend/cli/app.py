from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import typer
from rich.console import Console
from rich.panel import Panel

from .errors import CLISurfaceError, RouteBindingMissingError
from .views.alerts import (
    AlertView,
    build_alerts_table,
    build_critical_force_close_banner,
    render_alerts_snapshot,
)


StrategyCreateHandler = Callable[[], str]
StrategyListHandler = Callable[[], str]
StrategyShowHandler = Callable[[str], str]
StrategyEditHandler = Callable[[str], str]
DecisionRunHandler = Callable[[str], str]
DecisionDryRunHandler = Callable[[str], str]
ApprovalListHandler = Callable[[], str]
ApprovalShowHandler = Callable[[str, bool, Optional[str]], str]
ApprovalApproveHandler = Callable[[str], str]
ApprovalRejectHandler = Callable[[str, str], str]
ExecutionShowHandler = Callable[[str], str]
ExecutionLogsHandler = Callable[[str], str]
ExecutionForceCloseHandler = Callable[[str], str]
ExecutionForkReplayHandler = Callable[[str, int, int], str]
ExportJsonHandler = Callable[[str], str]
ExportMarkdownHandler = Callable[[str], str]
ExportMemoHandler = Callable[[str], str]
MonitorAlertsHandler = Callable[[bool], Sequence[AlertView]]
MonitorShadowStatusHandler = Callable[[], str]
DoctorHandler = Callable[[], str]


def _missing_binding(route: str) -> Callable[..., object]:
    def _raise_missing(*_args: object, **_kwargs: object) -> object:
        raise RouteBindingMissingError(
            f"TODO: CLI route `{route}` 未绑定服务适配器。请在 CLI surface 中显式注入 interface/adapter。"
        )

    return _raise_missing


@dataclass(frozen=True)
class CLISurfaceServices:
    strategy_create: StrategyCreateHandler = field(default_factory=lambda: _missing_binding("strategy.create"))
    strategy_list: StrategyListHandler = field(default_factory=lambda: _missing_binding("strategy.list"))
    strategy_show: StrategyShowHandler = field(default_factory=lambda: _missing_binding("strategy.show"))
    strategy_edit: StrategyEditHandler = field(default_factory=lambda: _missing_binding("strategy.edit"))
    decision_run: DecisionRunHandler = field(default_factory=lambda: _missing_binding("decision.run"))
    decision_dry_run: DecisionDryRunHandler = field(default_factory=lambda: _missing_binding("decision.dry-run"))
    approval_list: ApprovalListHandler = field(default_factory=lambda: _missing_binding("approval.list"))
    approval_show: ApprovalShowHandler = field(default_factory=lambda: _missing_binding("approval.show"))
    approval_approve: ApprovalApproveHandler = field(default_factory=lambda: _missing_binding("approval.approve"))
    approval_reject: ApprovalRejectHandler = field(default_factory=lambda: _missing_binding("approval.reject"))
    execution_show: ExecutionShowHandler = field(default_factory=lambda: _missing_binding("execution.show"))
    execution_logs: ExecutionLogsHandler = field(default_factory=lambda: _missing_binding("execution.logs"))
    execution_force_close: ExecutionForceCloseHandler = field(
        default_factory=lambda: _missing_binding("execution.force-close")
    )
    execution_fork_replay: ExecutionForkReplayHandler = field(
        default_factory=lambda: _missing_binding("execution.fork-replay")
    )
    export_json: ExportJsonHandler = field(default_factory=lambda: _missing_binding("export.json"))
    export_markdown: ExportMarkdownHandler = field(default_factory=lambda: _missing_binding("export.markdown"))
    export_memo: ExportMemoHandler = field(default_factory=lambda: _missing_binding("export.memo"))
    monitor_alerts: MonitorAlertsHandler = field(default_factory=lambda: _missing_binding("monitor.alerts"))
    monitor_shadow_status: MonitorShadowStatusHandler = field(
        default_factory=lambda: _missing_binding("monitor.shadow-status")
    )
    doctor_check: DoctorHandler = field(default_factory=lambda: _missing_binding("doctor"))


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

    @strategy_app.command("create")
    def strategy_create() -> None:
        _print_result(
            render_console,
            "strategy.create",
            _invoke_route_or_exit(render_console, routed_services.strategy_create),
        )

    @strategy_app.command("list")
    def strategy_list() -> None:
        _print_result(
            render_console,
            "strategy.list",
            _invoke_route_or_exit(render_console, routed_services.strategy_list),
        )

    @strategy_app.command("show")
    def strategy_show(strategy_id: str) -> None:
        _print_result(
            render_console,
            "strategy.show",
            _invoke_route_or_exit(render_console, routed_services.strategy_show, strategy_id),
        )

    @strategy_app.command("edit")
    def strategy_edit(strategy_id: str) -> None:
        _print_result(
            render_console,
            "strategy.edit",
            _invoke_route_or_exit(render_console, routed_services.strategy_edit, strategy_id),
        )

    @decision_app.command("run")
    def decision_run(
        strategy_id: str = typer.Option(..., "--strategy", help="Strategy id"),
    ) -> None:
        _print_result(
            render_console,
            "decision.run",
            _invoke_route_or_exit(render_console, routed_services.decision_run, strategy_id),
        )

    @decision_app.command("dry-run")
    def decision_dry_run(
        strategy_id: str = typer.Option(..., "--strategy", help="Strategy id"),
    ) -> None:
        _print_result(
            render_console,
            "decision.dry-run",
            _invoke_route_or_exit(render_console, routed_services.decision_dry_run, strategy_id),
        )

    @approval_app.command("list")
    def approval_list() -> None:
        _print_result(
            render_console,
            "approval.list",
            _invoke_route_or_exit(render_console, routed_services.approval_list),
        )

    @approval_app.command("show")
    def approval_show(
        intent_id: str,
        raw: bool = typer.Option(False, "--raw", help="Show machine truth JSON directly"),
        machine_truth_json: Optional[str] = typer.Option(
            None,
            "--machine-truth-json",
            help="Machine Truth JSON when --raw is enabled",
        ),
    ) -> None:
        _print_result(
            render_console,
            "approval.show",
            _invoke_route_or_exit(render_console, routed_services.approval_show, intent_id, raw, machine_truth_json),
        )

    @approval_app.command("approve")
    def approval_approve(
        intent_id: str,
    ) -> None:
        _print_result(
            render_console,
            "approval.approve",
            _invoke_route_or_exit(render_console, routed_services.approval_approve, intent_id),
        )

    @approval_app.command("reject")
    def approval_reject(
        intent_id: str,
        reason: str = typer.Option(..., "--reason", help="Explicit operator rejection reason"),
    ) -> None:
        _print_result(
            render_console,
            "approval.reject",
            _invoke_route_or_exit(render_console, routed_services.approval_reject, intent_id, reason),
        )

    @execution_app.command("show")
    def execution_show(
        intent_id: str,
    ) -> None:
        _print_result(
            render_console,
            "execution.show",
            _invoke_route_or_exit(render_console, routed_services.execution_show, intent_id),
        )

    @execution_app.command("logs")
    def execution_logs(
        intent_id: str,
    ) -> None:
        _print_result(
            render_console,
            "execution.logs",
            _invoke_route_or_exit(render_console, routed_services.execution_logs, intent_id),
        )

    @execution_app.command("force-close")
    def execution_force_close(
        intent_id: str,
    ) -> None:
        _print_result(
            render_console,
            "execution.force-close",
            _invoke_route_or_exit(render_console, routed_services.execution_force_close, intent_id),
        )

    @execution_app.command("fork-replay")
    def execution_fork_replay(
        intent_id: str,
        from_block: int = typer.Option(..., "--from-block", min=0, help="Fork replay start block"),
        to_block: int = typer.Option(..., "--to-block", min=0, help="Fork replay end block"),
    ) -> None:
        _print_result(
            render_console,
            "execution.fork-replay",
            _invoke_route_or_exit(
                render_console,
                routed_services.execution_fork_replay,
                intent_id,
                from_block,
                to_block,
            ),
        )

    @export_app.command("json")
    def export_json(intent_id: str) -> None:
        _print_result(
            render_console,
            "export.json",
            _invoke_route_or_exit(render_console, routed_services.export_json, intent_id),
        )

    @export_app.command("markdown")
    def export_markdown(intent_id: str) -> None:
        _print_result(
            render_console,
            "export.markdown",
            _invoke_route_or_exit(render_console, routed_services.export_markdown, intent_id),
        )

    @export_app.command("memo")
    def export_memo(intent_id: str) -> None:
        _print_result(
            render_console,
            "export.memo",
            _invoke_route_or_exit(render_console, routed_services.export_memo, intent_id),
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
        for alert in alerts:
            if alert.severity.value == "critical" and alert.escalation_required and alert.intent_id:
                render_console.print(build_critical_force_close_banner(alert))

    @monitor_app.command("shadow-status")
    def monitor_shadow_status() -> None:
        _print_result(
            render_console,
            "monitor.shadow-status",
            _invoke_route_or_exit(render_console, routed_services.monitor_shadow_status),
        )

    @app.command("doctor")
    def doctor() -> None:
        _print_result(
            render_console,
            "doctor",
            _invoke_route_or_exit(render_console, routed_services.doctor_check),
        )

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


def create_default_cli_app(*, console: Console | None = None) -> typer.Typer:
    from .wiring import (
        build_contract_gateway_from_runtime_env,
        build_decision_dry_run_handler_from_runtime_env,
        build_decision_run_handler_from_runtime_env,
        build_production_services,
        build_runtime_store_from_env,
    )

    runtime_store = build_runtime_store_from_env()
    contract_gateway = None
    force_close_missing_reason = "execution.force-close requires runtime ContractGateway wiring"
    decision_run_handler = None
    decision_missing_reason = "decision.run requires runtime ContractGateway wiring"
    decision_dry_run_handler = build_decision_dry_run_handler_from_runtime_env(runtime_store=runtime_store)
    try:
        contract_gateway = build_contract_gateway_from_runtime_env()
        decision_run_handler = build_decision_run_handler_from_runtime_env(
            contract_gateway=contract_gateway,
            runtime_store=runtime_store,
        )
        decision_dry_run_handler = build_decision_dry_run_handler_from_runtime_env(
            runtime_store=runtime_store,
            contract_gateway=contract_gateway,
        )
        decision_missing_reason = None
    except RouteBindingMissingError as exc:
        force_close_missing_reason = str(exc)
        decision_missing_reason = f"decision.run requires runtime ContractGateway wiring: {exc}"
    return create_cli_app(
        services=build_production_services(
            contract_gateway=contract_gateway,
            runtime_store=runtime_store,
            decision_run_handler=decision_run_handler,
            decision_dry_run_handler=decision_dry_run_handler,
            decision_missing_reason=decision_missing_reason,
            force_close_missing_reason=force_close_missing_reason,
        ),
        console=console,
    )


app = create_default_cli_app()
