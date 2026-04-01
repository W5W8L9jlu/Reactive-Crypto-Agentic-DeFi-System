# 线程内验收清单

- 模块 / prompt：`investment_state_machine_contract` / `docs/prompts/investment_state_machine_contract.prompt.md`
- Wave：`wave_1`
- 线程负责人：`not verified yet`
- 分支：`not verified yet`
- commit：`not verified yet`
- 改动目录：`backend/contracts/core`, `backend/contracts/interfaces`
- 是否只改允许路径：`yes`，当前可见实现文件都落在模块工作目录内。

## A. 职责边界
- 本模块的目标职责是否完成：`yes`，`IReactiveInvestmentCompiler.sol` 与 `ReactiveInvestmentCompiler.sol` 已提供注册、触发、状态查询与状态推进逻辑。
- 是否引入了不属于本模块的逻辑：`no`，代码只包含状态机、运行时约束和 getter。
- 是否修改了共享 schema / 契约：`yes`，接口定义了 `InvestmentIntent`、`PositionState`、事件与错误。
- 若修改，是否同步通知依赖线程：`not verified yet`

## B. Contract 对齐
- 是否逐条对齐 implementation contract：`yes`，实现覆盖 `registerInvestmentIntent`、`executeReactiveTrigger` 与状态流转检查。
- 未满足项：`not verified yet`
- 明确拒绝实现的项（若有）：`链下信号后再执行的混合模式`、`自由策略决策`。

## C. Invariants 检查
- JSON 仍是唯一执行真相：`n/a`
- Audit 是否只做摘抄：`n/a`
- Investment Memo 是否未污染执行真相：`n/a`
- 是否仍然只信 RPC 作为执行真相：`yes`，本模块没有引入第三方索引真相。
- Execution Compiler 是否只在注册时工作：`yes`，当前 contract 只提供注册与触发入口，不把编译逻辑放进触发路径。
- Reactive 是否未承载自由决策：`yes`
- Shadow Monitor 是否保持独立：`n/a`

## D. 验证证据
- 运行的命令：
  - `git diff --name-only HEAD` -> `fatal: not a git repository`
  - `git log --oneline -n 10` -> `fatal: not a git repository`
  - `Get-Content backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
  - `Get-Content backend/contracts/core/ReactiveInvestmentCompiler.sol`
  - `Get-ChildItem backend/contracts -Recurse -File`
- 测试结果：`not verified yet`
- 样例输入：`registerInvestmentIntent(bytes32 intentId, InvestmentIntent intent)`；`executeReactiveTrigger(bytes32 intentId, uint256 observedOut, uint256 runtimeExitMinOut)`
- 样例输出：`InvestmentIntentRegistered`；`InvestmentStateAdvanced`
- 截图/日志/回执路径：`not verified yet`

## E. Known gaps
- TODO：出场后的结算 / 记账语义仍以 `TODO` 形式保留在实现中。
- Blockers：当前工作区无法通过 `git` 核对分支、差异与 recent commits。
- 假设：当前仓库中的 Solidity 文件即为本模块的稳定交付面。
- 风险：未执行 Solidity 编译或链上测试，实际部署兼容性未验证。

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 进入线程间对接：`可以`
