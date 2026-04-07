# 线程测试证据

> Canonical source for `investment_state_machine_contract` verification evidence.
> Duplicate file `investment_state_machine_contract_test_evidence.md` is retired and must not diverge from this record.

## 测试目标
- 验证状态机只能按 `PendingEntry -> ActivePosition -> Closed` 流转
- 验证 `Closed` 状态不能再次触发
- 验证 entry / exit 运行时约束分别生效，且 entry 成功后会记录 `actualPositionSize`

## 覆盖的场景
- happy path：注册后从 `PendingEntry` 进入 `ActivePosition`，再进入 `Closed`
- failure path：`EntryConstraintViolation`、`ExitConstraintViolation`、`RuntimeExitMinOutTooLow`、`ClosedIntentCannotExecute`
- edge case：初始状态必须为 `PendingEntry`，`actualPositionSize` 在入场后必须被持久化

## 输入
```json
{
  "intentId": "0x0000000000000000000000000000000000000000000000000000000000000001",
  "intent": {
    "owner": "0x0000000000000000000000000000000000000001",
    "inputToken": "0x0000000000000000000000000000000000000002",
    "outputToken": "0x0000000000000000000000000000000000000003",
    "plannedEntrySize": "1000000000000000000",
    "entryMinOut": "990000000000000000",
    "exitMinOutFloor": "950000000000000000"
  },
  "observedOut": "1000000000000000000",
  "runtimeExitMinOut": "950000000000000000"
}
```

## 断言输出
```json
{
  "tests": [
    "testRegisterStartsInPendingEntry",
    "testEntryTriggerAdvancesToActiveAndRecordsActualSize",
    "testExitTriggerAdvancesActiveToClosed",
    "testClosedIntentCannotRetrigger",
    "testEntryConstraintViolationReverts",
    "testExitConstraintViolationRevertsWhenObservedOutBelowRuntimeMin",
    "testRuntimeExitMinOutBelowFloorReverts"
  ],
  "status": "7 passed, 0 failed, 0 skipped"
}
```

## 命令
```bash
git branch --show-current
git rev-parse --short HEAD
D:\Foundry\bin\forge.exe build --root . --contracts backend/contracts
$env:FOUNDRY_CACHE_PATH='D:/reactive-crypto-agentic-DeFi-system/.foundry-cache'; D:\Foundry\bin\forge.exe test --root . --contracts backend/contracts --match-path 'backend/contracts/test/ReactiveInvestmentCompiler.t.sol' -vv
```

## 实际结果
- `git branch --show-current` -> `w1-gate-fail-fix`
- `git rev-parse --short HEAD` -> `c5afba2`
- `forge build --root . --contracts backend/contracts` -> `Compiler run successful!`
- `forge test --root . --contracts backend/contracts --match-path 'backend/contracts/test/ReactiveInvestmentCompiler.t.sol' -vv` -> `Ran 7 tests ... 7 passed; 0 failed; 0 skipped`

## 已验证的 invariant
- `PendingEntry -> ActivePosition -> Closed` 是唯一被测试覆盖的状态流转
- `Closed` 再次触发会以 `ClosedIntentCannotExecute` revert
- entry 约束与 exit 约束是分开的，分别以 `EntryConstraintViolation` / `ExitConstraintViolation` / `RuntimeExitMinOutTooLow` 表达
- 入场成功后会记录并保留 `actualPositionSize`
- 当前模块没有实现链下信号后再执行的混合决策路径

## 环境限制与非阻塞告警
- `forge` 运行时会打印全局 signature cache / etherscan 配置告警，因为沙箱无法写入 `C:\Users\CodexSandboxOffline\.foundry\cache`
- 上述告警不影响本模块的编译和 7 个本地测试用例通过
- 当前证据仍不包含链上部署回执、外部消费者集成、或 Wave 级 happy path
