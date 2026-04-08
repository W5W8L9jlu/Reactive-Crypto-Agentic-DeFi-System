# cli_surface 线程测试证据

## 测试目标
- 验证六组命令入口已接入 CLI 路由层。
- 验证审批展示命令默认/`--raw` 行为与参数约束。
- 验证 monitor alert 视图输出（含空状态与优先级排序）。

## 覆盖场景
- 命令路由：
  - `--help` 包含 `strategy/decision/approval/execution/export/monitor`
  - 各命令组子命令可调用到注入 handler
- 审批显示：
  - 默认模式输出 battle card 文本
  - `--raw --machine-truth-json` 输出原始 JSON
  - `--raw` 缺少 machine truth 参数时返回错误码 `2`
- alert 视图：
  - critical 在 warning 前排序
  - 空告警显示 `No active alerts`

## 执行命令（本线程实测）
```bash
python -m unittest backend.cli.test_app -v
python -m unittest backend.cli.approval.test_approval_flow -v
python -m unittest backend.cli.views.test_alerts -v
```

## 输入与输出样例（来自测试代码）
- 输入样例：
  - `approval show --raw --machine-truth-json '{"id":"ti-001"}'`
  - `monitor alerts --critical-only`
- 期望输出片段：
  - `Approval Battle Card`
  - `{"id":"ti-001"}`
  - `CRIT_GRACE_TIMEOUT`
  - `No active alerts`

## 实际结果
- `python -m unittest backend.cli.test_app -v`
  - `Ran 4 tests in 0.394s`
  - `OK`
- `python -m unittest backend.cli.approval.test_approval_flow -v`
  - `Ran 5 tests in 0.002s`
  - `OK`
- `python -m unittest backend.cli.views.test_alerts -v`
  - `Ran 2 tests in 0.032s`
  - `OK`

## 未验证项
- 真实业务 service adapter 绑定后的命令执行结果：`not verified yet`
- Wave3 级端到端 dry-run（context -> adapter -> validation/approval）：`not verified yet`

