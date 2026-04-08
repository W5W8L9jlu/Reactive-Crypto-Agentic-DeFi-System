# cli_surface 线程间对接单

- 上游线程：`cli_surface`
- 建议下游线程：`cryptoagents_adapter`、`execution_layer`、`reactive_runtime` 及 CLI 编排线程
- Wave：`wave3`
- handoff 日期：`2026-04-08`
- 上游 commit：`9177017`

## 1. 上游已稳定产出
- 命令面（Typer）：
  - `strategy list`
  - `decision run`
  - `approval show`
  - `approval approve`
  - `approval reject`
  - `execution status`
  - `export bundle`
  - `monitor alerts`
- 路由装配入口：
  - `create_cli_app(services=CLISurfaceServices(...)) -> typer.Typer`
- monitor 视图对象与渲染：
  - `AlertView`
  - `build_alerts_table(...)`
  - `render_alerts_snapshot(...)`
- CLI 错误模型：
  - `CLISurfaceError`
  - `RouteBindingMissingError`
  - `CLISurfaceInputError`

## 2. 下游消费契约
### 输入（CLI surface 接口）
```json
{
  "user_command": "string",
  "services": {
    "strategy_list": "() -> str",
    "decision_run": "(context_id: str) -> str",
    "approval_show": "(raw: bool, machine_truth_json: str|null) -> str",
    "approval_approve": "(trade_intent_id: str) -> str",
    "approval_reject": "(trade_intent_id: str, reason: str) -> str",
    "execution_status": "(trade_intent_id: str) -> str",
    "export_bundle": "(trade_intent_id: str) -> str",
    "monitor_alerts": "(critical_only: bool) -> Sequence[AlertView]"
  }
}
```

### 输出
```json
{
  "route_output": "Rendered Rich panel text",
  "monitor_output": "Rich table + snapshot text",
  "error_exit": "typer.Exit(code=2) for CLI surface input/route errors"
}
```

### 错误模型
```text
CLISurfaceError
RouteBindingMissingError
CLISurfaceInputError
```

## 3. 约束
- 不允许：
  - 在 CLI 模块承载业务核心计算
  - 在 CLI 模块承载状态机逻辑
  - 在 CLI 模块承载 provider 逻辑
- 仅允许：
  - 命令路由
  - 展示渲染
  - 人工审批/运维入口
- 参数约束：
  - `approval show --raw` 必须同时提供 `--machine-truth-json`

## 4. 示例
- sample request：
```bash
python -m backend.cli.app approval show --raw --machine-truth-json "{\"id\":\"ti-001\"}"
```
- sample response（测试环境桩）：
```text
{"id":"ti-001"}
```
- sample failure：
  - `approval show --raw` 缺失 `--machine-truth-json`
  - 结果：CLI 输出错误面板并 `exit code = 2`

## 5. 剩余问题
- 真实下游 service adapter 绑定：`not verified yet`
- 真实跨模块命令链路联调：`not verified yet`
- 生产级 CLI 入口命令（打包/安装方式）：`not verified yet`

