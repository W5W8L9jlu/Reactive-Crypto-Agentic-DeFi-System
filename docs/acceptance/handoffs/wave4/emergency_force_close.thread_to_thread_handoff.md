# emergency_force_close 线程间对接单

- 上游线程：`emergency_force_close`
- 建议下游线程：`shadow_monitor`、`cli_surface`、`reactive_runtime`、运行时编排线程
- Wave：`wave4`
- handoff 日期：`2026-04-08`
- 当前分支：`codex/wave4`
- 当前 HEAD：`4297287`
- 上游 commit：`not verified yet`

## 1. 上游当前已实现（工作树）
- 合约新增 break-glass 接口：
  - `emergencyForceClose(bytes32 intentId, uint256 maxSlippageBps) returns (uint256 emergencyExitMinOut)`
- 紧急权限管理：
  - `owner()`
  - `setEmergencyAuthorizedRelayer(address relayer, bool authorized)`
  - `isEmergencyAuthorizedRelayer(address relayer)`
- 关键事件：
  - `EmergencyRelayerAuthorizationUpdated(relayer, authorized)`
  - `EmergencyForceCloseExecuted(intentId, caller, actualPositionSize, maxSlippageBps, emergencyExitMinOut)`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "intentId": "bytes32",
  "maxSlippageBps": "uint256 (0..10000)",
  "caller": "owner | authorized relayer",
  "pre_state": "ActivePosition"
}
```

### 输出对象
```json
{
  "post_state": "Closed",
  "emergencyExitMinOut": "uint256",
  "events": [
    "InvestmentStateAdvanced(intentId, ActivePosition, Closed, 0, actualPositionSize)",
    "EmergencyForceCloseExecuted(...)"
  ]
}
```

## 3. 异常模型
```text
IntentNotRegistered
UnauthorizedEmergencyForceCloseCaller
EmergencyForceCloseOnlyActivePosition
EmergencySlippageBpsOutOfRange
ActualPositionSizeNotRecorded
UnauthorizedRelayerConfigCaller
ZeroAddressRelayer
ClosedIntentCannotExecute (用于后续迟滞普通触发)
```

## 4. 约束
- 不允许：
  - 把 emergency 路径当作日常执行路径
  - 用 emergency 路径替代正常 reactive callback
  - 假设当前模块已包含外部执行适配器与回执落库
- 仅允许：
  - break-glass 关闭仓位
  - 输出紧急平仓约束（`emergencyExitMinOut`）与事件供下游消费

## 5. 示例
- sample request：
```solidity
compiler.setEmergencyAuthorizedRelayer(relayer, true);
uint256 minOut = compiler.emergencyForceClose(intentId, 1500);
```
- sample response（合约语义）：
```json
{
  "return": {
    "emergencyExitMinOut": "actualPositionSize * (10000-1500)/10000"
  },
  "state_after": "Closed",
  "event": "EmergencyForceCloseExecuted"
}
```
- sample failure：
  - caller 非 owner/authorized relayer -> `UnauthorizedEmergencyForceCloseCaller`
  - `pre_state != ActivePosition` -> `EmergencyForceCloseOnlyActivePosition`
  - force-close 后再走普通触发 -> `ClosedIntentCannotExecute`

## 6. 剩余问题
- emergency 专项测试证据（权限/非 Active 拒绝/force-close 后迟滞回调）：`not verified yet`
- 与 `shadow_monitor` 的真实告警联动链路：`not verified yet`
- 上游 commit 锚点（已提交 SHA）: `not verified yet`
- `IReactiveInvestmentCompiler` 对 emergency 新接口的统一声明：`not verified yet`
