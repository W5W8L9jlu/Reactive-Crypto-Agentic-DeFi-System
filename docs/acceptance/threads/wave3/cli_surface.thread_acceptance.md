# cli_surface 线程内验收清单

- 模块 / prompt：`cli_surface` / `docs/prompts/cli_surface.prompt.md`
- Wave：`wave3`
- 线程负责人：`not verified yet`
- 分支：`w3-reactive-runtime`
- commit（模块交付锚点）：`9177017`
- 改动文件（来自 `git show --name-only 9177017`）：
  - `backend/cli/app.py`
  - `backend/cli/errors.py`
  - `backend/cli/test_app.py`
  - `backend/cli/views/alerts.py`
  - `backend/cli/views/test_alerts.py`
- 是否只改允许路径：是（实现改动仅在 `backend/cli/`）

## A. 职责边界
- 本模块目标职责是否完成：是（提供 `strategy/decision/approval/execution/export/monitor` 六组命令入口）。
- 是否引入本模块外业务逻辑：否（默认仅做路由、展示、人工入口；未接入核心计算）。
- 缺规范时处理方式：是（未绑定 route 抛出显式 `RouteBindingMissingError`，不做隐式 fallback）。

## B. Contract 对齐
- 是否对齐 `docs/contracts/cli_surface.contract.md`：是。
- 对齐项：
  - CLI 仅负责路由/展示/操作入口。
  - 不承担复杂业务计算。
  - 审批 `--raw` 仅在显式提供 `--machine-truth-json` 时可用。
  - monitor 提供 alert 视图（table + snapshot）。
- 未覆盖项：
  - 真实 service adapter 绑定与端到端调用：`not verified yet`

## C. Invariants 检查
- 执行真相来源不在 CLI 层被重写：是（CLI 仅透传与展示）。
- CLI 未生成 calldata / 未签名 / 未执行链上动作：是（代码中无此逻辑）。
- CLI 未承载 provider 逻辑或状态机逻辑：是。

## D. 验证证据
- 代码状态：
  - `git diff --name-only HEAD` -> 无输出（工作树干净）
  - `git status -sb` -> `## w3-reactive-runtime...origin/w3-reactive-runtime`
  - `git log --oneline -n 10` -> 最近模块提交为 `9177017 feat: Add Typer/Rich CLI surface with route and alert tests`
- 已运行测试：
  - `python -m unittest backend.cli.test_app -v` -> `Ran 4 tests ... OK`
  - `python -m unittest backend.cli.approval.test_approval_flow -v` -> `Ran 5 tests ... OK`
  - `python -m unittest backend.cli.views.test_alerts -v` -> `Ran 2 tests ... OK`

## E. Known gaps
- CLI 到真实 strategy/decision/execution/export/monitor service 的 adapter 绑定：`not verified yet`
- Wave3 级 dry-run 主流程（context -> adapter -> validation/approval）联调证据：`not verified yet`
- 线程负责人字段：`not verified yet`

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 是否可进入线程间对接：可以

