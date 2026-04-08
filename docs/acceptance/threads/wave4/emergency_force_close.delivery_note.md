# 线程交付说明

## 基本信息
- 模块名: `emergency_force_close`
- Prompt 文件: `docs/prompts/emergency_force_close.prompt.md`
- Wave: `wave4`
- 负责人: `not verified yet`
- 分支: `codex/wave4`
- HEAD commit: `4297287`

## 本次交付做了什么
- 在 `ReactiveInvestmentCompiler` 增加 break-glass 闭环接口：
  - `emergencyForceClose(bytes32 intentId, uint256 maxSlippageBps) returns (uint256 emergencyExitMinOut)`
- 增加紧急权限控制能力：
  - owner 初始化与查询：`constructor` + `owner()`
  - relayer 授权：`setEmergencyAuthorizedRelayer` / `isEmergencyAuthorizedRelayer`
- 增加紧急相关错误与事件：
  - `UnauthorizedEmergencyForceCloseCaller`
  - `EmergencyForceCloseOnlyActivePosition`
  - `EmergencySlippageBpsOutOfRange`
  - `EmergencyRelayerAuthorizationUpdated`
  - `EmergencyForceCloseExecuted`

## 模块实现文件（实际改动）
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`

## 未交付项
- emergency 专项测试用例（权限/非 ActivePosition 拒绝/force-close 后迟滞回调 revert）：`not verified yet`
- `shadow_monitor` 到 force-close 的真实运行链路：`not verified yet`
- external execution adapter / settlement receipt schema：`not verified yet`（代码中保留 `TODO(domain)`）
- emergency 改动的提交锚点（commit SHA）：`not verified yet`

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status --short --branch
git rev-parse --short HEAD
forge test --root backend/contracts --contracts backend/contracts/core -vv
```

## 命令结果摘要
- `git diff --name-only HEAD`：仅 `backend/contracts/core/ReactiveInvestmentCompiler.sol`
- `git status --short --branch`：`## codex/wave4`，且存在 `backend/contracts/cache/`、`backend/contracts/out/`、`backend/monitor/` 未跟踪目录
- `git rev-parse --short HEAD`：`4297287`
- `forge test ...`：`Ran 8 tests ... 8 passed, 0 failed`

## 对下游影响
- 下游可直接通过合约实例调用 `emergencyForceClose` 执行 break-glass 关闭并消费 `EmergencyForceCloseExecuted` 事件。
- 下游不可假设 emergency 专项回归测试已完备。
- 下游不可假设已存在 shadow monitor 自动联动与执行适配器闭环。
