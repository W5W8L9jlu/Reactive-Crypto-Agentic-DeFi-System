# 线程间对接单

- 上游线程：`investment_state_machine_contract`
- 下游线程：`not verified yet`
- Wave：`wave_1`
- handoff 日期：`2026-03-31`
- 上游 commit：`not verified yet`

## 1. 上游已经稳定的东西
- 接口：`registerInvestmentIntent`, `executeReactiveTrigger`, `getPositionState`, `getActualPositionSize`, `getInvestmentIntent`
- 对象：`InvestmentIntent`, `PositionState`
- 枚举：`PositionState.PendingEntry`, `PositionState.ActivePosition`, `PositionState.Closed`
- 命令：`registerInvestmentIntent`, `executeReactiveTrigger`
- 文件路径：`backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`, `backend/contracts/core/ReactiveInvestmentCompiler.sol`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "intentId": "bytes32",
  "intent": {
    "owner": "address",
    "inputToken": "address",
    "outputToken": "address",
    "plannedEntrySize": "uint256",
    "entryMinOut": "uint256",
    "exitMinOutFloor": "uint256"
  },
  "observedOut": "uint256",
  "runtimeExitMinOut": "uint256"
}
```

### 输出对象
```json
{
  "positionState": "PendingEntry | ActivePosition | Closed",
  "actualPositionSize": "uint256",
  "event": "InvestmentIntentRegistered | InvestmentStateAdvanced"
}
```

### 异常模型
```text
IntentAlreadyRegistered
IntentNotRegistered
ClosedIntentCannotExecute
EntryConstraintViolation
ExitConstraintViolation
RuntimeExitMinOutTooLow
ActualPositionSizeNotRecorded
```

## 3. 约束
- 不允许：链下信号后再执行的混合模式、自由策略决策。
- 仅允许：注册时落地 intent，触发时按状态机硬约束推进。
- 单位与精度约定：`uint256` 原样传递，不在本模块内做额外精度转换。
- 空值 / 默认值约定：未注册 intent 必须报错，不能静默返回默认值。

## 4. 示例
- sample request：`registerInvestmentIntent(intentId, intent)`，随后 `executeReactiveTrigger(intentId, observedOut, runtimeExitMinOut)`
- sample response：`emit InvestmentStateAdvanced(intentId, fromState, toState, observedOut, actualPositionSize)`
- sample failure：`revert ClosedIntentCannotExecute(intentId)`

## 5. 未完成项
- TODO：`not verified yet`
- 临时 workaround：`not verified yet`
- 风险提示：当前工作区无法通过 `git` 核对分支与提交历史，也没有 Solidity 测试/编译证据。
