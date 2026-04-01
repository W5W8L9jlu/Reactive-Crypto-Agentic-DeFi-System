# 线程测试证据

## 测试目标
- 验证状态机接口的输入 / 输出形状是否与 contract 一致。
- 验证 entry / exit 两条路径的约束项是否在实现中显式存在。

## 覆盖的场景
- happy path：`registerInvestmentIntent` 成功注册后，`executeReactiveTrigger` 可推进状态。
- failure path：重复注册、未注册、Closed 重入、entry / exit 约束不满足时均会 revert。
- edge case：`actualPositionSize` 在 entry 成功后必须被记录，exit 阶段还需检查 `runtimeExitMinOut` 下限。

## 输入
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

## 输出
```json
{
  "event": "InvestmentIntentRegistered | InvestmentStateAdvanced",
  "state": "PendingEntry | ActivePosition | Closed",
  "error": "IntentAlreadyRegistered | IntentNotRegistered | ClosedIntentCannotExecute | EntryConstraintViolation | ExitConstraintViolation | RuntimeExitMinOutTooLow | ActualPositionSizeNotRecorded"
}
```

## 命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
Get-Content backend/contracts/interfaces/IReactiveInvestmentCompiler.sol
Get-Content backend/contracts/core/ReactiveInvestmentCompiler.sol
Get-ChildItem backend/contracts -Recurse -File
```

## 实际结果
- 通过：`not verified yet`
- 失败：`git diff --name-only HEAD` 和 `git log --oneline -n 10` 都返回 `fatal: not a git repository`
- 未覆盖：Solidity 编译、链上测试、事件回执、历史 test run 产物

## 备注
- 当前仓库没有可执行的 test evidence 产物；本文件只记录源码层面可确认的约束和接口形状。
