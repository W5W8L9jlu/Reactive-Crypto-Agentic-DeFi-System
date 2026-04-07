# 线程间对接单

> Canonical source for `investment_state_machine_contract` handoff evidence.
> Duplicate file `investment_state_machine_contract_thread_to_thread_handoff.md` is retired and must only point here.

- 上游线程：`investment_state_machine_contract`
- 下游线程：`not verified yet`
- Wave：`wave_1`
- handoff 日期：`2026-04-01`
- 上游 commit：`c5afba2`
- authoritative acceptance：`docs/acceptance/threads/wave1/investment_state_machine_contract.thread_acceptance.md`
- authoritative test evidence：`docs/acceptance/threads/wave1/investment_state_machine_contract.test_evidence.md`

## 1. 上游已经稳定的东西
- 接口：`registerInvestmentIntent`、`executeReactiveTrigger`、`getPositionState`、`getActualPositionSize`、`getInvestmentIntent`
- 对象：`InvestmentIntent`
- 枚举：`PositionState.PendingEntry`、`PositionState.ActivePosition`、`PositionState.Closed`
- 错误：`IntentAlreadyRegistered`、`IntentNotRegistered`、`ClosedIntentCannotExecute`、`EntryConstraintViolation`、`ExitConstraintViolation`、`RuntimeExitMinOutTooLow`、`ActualPositionSizeNotRecorded`
- 文件路径：`backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`、`backend/contracts/core/ReactiveInvestmentCompiler.sol`
- 验证命令：`forge build --root . --contracts backend/contracts` 与 `forge test --root . --contracts backend/contracts --match-path 'backend/contracts/test/ReactiveInvestmentCompiler.t.sol' -vv`

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
  "events": [
    "InvestmentIntentRegistered",
    "InvestmentStateAdvanced"
  ]
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
- 不允许：`Closed` 之后再次触发；链下信号后再执行的混合模式；自由策略决策
- 仅允许：注册时写入意图，触发时按状态机做硬约束检查
- 单位与精度约定：`uint256` 原样传递，精度由上游编译器 / 运行时保持一致
- 空值 / 默认值约定：未注册 intent 必须报 `IntentNotRegistered`，不能静默返回默认值

## 4. 示例
- sample request：`registerInvestmentIntent(intentId, intent)`，随后 `executeReactiveTrigger(intentId, observedOut, runtimeExitMinOut)`
- sample response：状态从 `PendingEntry` 进入 `ActivePosition`，入场成功后记录 `actualPositionSize`，退出后进入 `Closed`
- sample failure：`executeReactiveTrigger` 在 `Closed` 状态再次调用时抛出 `ClosedIntentCannotExecute`

## 5. 未完成项
- TODO：出场后的结算 / 记账语义未在当前 contract 中展开
- 非本线程范围风险：Wave 级 upstream-to-contract 映射与 downstream consumer 证据仍需其他线程提供
- 环境说明：Foundry 有非阻塞 cache 告警，但本地 compile / test 已实际通过
