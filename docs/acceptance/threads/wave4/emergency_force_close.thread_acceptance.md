# 线程验收清单
- 模块 / prompt: `emergency_force_close` / `docs/prompts/emergency_force_close.prompt.md`
- Wave: `wave4`
- 线程负责人: `not verified yet`
- 分支: `codex/wave4`
- HEAD commit: `4297287`
- 模块相关历史 commit: `not verified yet`（当前 emergency 改动尚未提交）
- 改动目录: `backend/contracts/core`
- 是否只改允许路径: `是（tracked diff 仅包含 backend/contracts/core/ReactiveInvestmentCompiler.sol）`

## A. Scope
- 已实现（合约工作树）：
  - 新增 `emergencyForceClose(intentId, maxSlippageBps)` break-glass 入口。
  - 新增 owner / authorized relayer 权限面：`setEmergencyAuthorizedRelayer`、`isEmergencyAuthorizedRelayer`、`owner`。
  - force-close 路径先写 `Closed`，再计算 `emergencyExitMinOut` 并发出事件。
- 非目标保持未实现：
  - 日常执行路径。
  - 替代正常 reactive callback。

## B. Contract 对齐
- 与 `docs/contracts/emergency_force_close.contract.md` 对齐情况：
  - 仅改 canonical 文件 `backend/contracts/core/ReactiveInvestmentCompiler.sol`：`是`
  - 输入 `intentId` / `maxSlippageBps`：`是`
  - 输出 `state set to Closed first`：`是`
  - 输出 `forced close tx`：`部分（当前为合约函数调用与事件输出；外部紧急卖出执行适配器为 TODO，not verified yet）`

## C. Invariants 检查
- 仅 owner/authorized relayer 调用：`是（代码检查存在）`
- 仅 ActivePosition 时允许：`是（代码检查存在）`
- 先写 Closed 再紧急卖出：`是（状态先写 Closed，再导出 emergencyExitMinOut）`
- 后续迟滞回调必须 Revert：`代码路径满足（Closed 后 executeReactiveTrigger 会 revert），专项用例 not verified yet`

## D. 验收证据（当前分支）
- `git diff --name-only HEAD`：
  - `backend/contracts/core/ReactiveInvestmentCompiler.sol`
- `git status --short --branch`：
  - `## codex/wave4`
  - ` M backend/contracts/core/ReactiveInvestmentCompiler.sol`
  - `?? backend/contracts/cache/`
  - `?? backend/contracts/out/`
  - `?? backend/monitor/`
- `git log --oneline -n 10`（最近两条）：
  - `4297287 docs: Freeze W3 to W4 wave handoff truths and assumptions`
  - `e80a4b8 docs: 回填W3波次集成矩阵风控Gate与退出报告`
- 测试命令：
  - `forge test --root backend/contracts --contracts backend/contracts/core -vv`
  - 结果：`Ran 8 tests ... 8 passed, 0 failed`

## E. Known Gaps
- emergency 专项最小验证（权限/非 Active 拒绝/force-close 后迟滞回调 revert）：`not verified yet`
- 与 `shadow_monitor` 的真实联动链路（告警->操作）: `not verified yet`
- `IReactiveInvestmentCompiler` 接口未声明 emergency 新增函数，对下游 interface 级调用兼容性：`not verified yet`
- 上游提交锚点（emergency 代码提交 SHA）：`not verified yet`

## F. 结论
- 线程状态：`IMPLEMENTED_IN_WORKTREE_WITH_NOTES`
- 是否可进入线程间对接：`可以（以当前工作树合约 ABI 行为为准）`
- 是否可作为“已提交冻结基线”交付：`not verified yet`
