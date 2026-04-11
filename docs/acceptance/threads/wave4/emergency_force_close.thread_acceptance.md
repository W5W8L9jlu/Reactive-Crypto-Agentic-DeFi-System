# 线程验收清单（更新于 2026-04-09）
- 模块 / prompt: `emergency_force_close` / `docs/prompts/emergency_force_close.prompt.md`
- Wave: `wave4`
- 线程负责人: `codex（待人工签收）`
- 分支: `codex/wave5`
- HEAD commit: `8e56fbd`
- 模块相关改动目录（当前工作树）：
  - `backend/contracts/core/ReactiveInvestmentCompiler.sol`
  - `backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
  - `backend/contracts/test/ReactiveInvestmentCompiler.t.sol`
  - `backend/execution/runtime/contract_gateway.py`
  - `backend/execution/runtime/test_web3_contract_gateway_integration.py`

## A. Scope
- 已实现：
  - 新增 `emergencyForceClose(intentId, maxSlippageBps)` break-glass 入口。
  - 新增 owner / authorized relayer 权限面：`setEmergencyAuthorizedRelayer`、`isEmergencyAuthorizedRelayer`、`owner`。
  - force-close 路径先写 `Closed`，再计算 `emergencyExitMinOut` 并发出事件。
  - runtime gateway 新增 `emergency_force_close` 与 recommendation 映射入口。
- 非目标保持未实现：
  - 自动化外部紧急平仓执行适配器（真实执行编排）。

## B. Contract 对齐
- 与 `docs/contracts/emergency_force_close.contract.md` 对齐情况：
  - 输入 `intentId` / `maxSlippageBps`：`是`
  - 状态先闭合（Closed-first）：`是`
  - 权限面（owner / relayer）：`是`
  - ABI 对齐（interface 声明 + runtime 调用口）：`是`

## C. Invariants 检查
- 仅 owner/authorized relayer 调用：`verified`
- 仅 ActivePosition 时允许：`verified`
- 先写 Closed 再紧急处理：`verified`
- force-close 后迟滞回调应被拒绝：`verified`

## D. 验收证据（本次重跑）
- `forge test --root backend/contracts --contracts backend/contracts/core -vv`
  - 结果：`12 passed, 0 failed`
- `python -m unittest backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration -v`
  - 结果：`Ran 4 tests ... OK`
  - 含用例：`test_shadow_monitor_recommendation_drives_emergency_force_close`

## E. Known Gaps
- 缺少 Sepolia 实链 smoke（无链上 tx 级证据）。
- CLI 默认 wiring 的 `execution force-close` 仍是占位文案，未直接接 runtime contract gateway。
- 目前仅有本地/测试证据，尚不能作为 Mainnet 灰度前的最终运营基线。

## F. 结论
- 线程状态：`PASS_WITH_BLOCKERS`
- 是否可进入线程间对接：`可以（接口与测试证据齐备）`
- 是否可作为“生产冻结基线”交付：`否（需补 Testnet smoke）`
