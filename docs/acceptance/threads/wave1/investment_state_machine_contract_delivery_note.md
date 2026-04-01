# 线程交付说明

## 基本信息
- 模块名：`investment_state_machine_contract`
- Prompt 文件：`docs/prompts/investment_state_machine_contract.prompt.md`
- Wave：`wave_1`
- 负责人：`not verified yet`
- 分支：`not verified yet`
- commit：`not verified yet`

## 本次交付做了什么
- 实现了投资状态机的接口与核心合约实现，覆盖注册、触发、状态查询与事件输出。
- 将状态流转限制为 `PendingEntry -> ActivePosition -> Closed`，并在 entry / exit 两条路径上分别做运行时约束。
- 在触发路径中保留了 `runtimeExitMinOut` 下限校验和 `actualPositionSize` 记录。

## 修改了哪些文件
- `backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`

## 没做什么
- 没有引入链下信号后再执行的混合模式。
- 没有加入自由策略决策。
- 没有补充 Solidity 测试工程或链上编译验证记录。

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
Get-Content -Path 'docs/acceptance/threads/investment_state_machine_contract_thread_acceptance.md' -Encoding utf8
Get-Content -Path 'docs/contracts/investment_state_machine_contract.contract.md' -Encoding utf8
Get-Content -Path 'backend/contracts/interfaces/IReactiveInvestmentCompiler.sol' -Encoding utf8
Get-Content -Path 'backend/contracts/core/ReactiveInvestmentCompiler.sol' -Encoding utf8
Get-ChildItem -Path 'backend/contracts' -Recurse -File
```

## 验收证据
- 测试截图：`not verified yet`
- 日志：`not verified yet`
- 示例 payload：`registerInvestmentIntent(bytes32 intentId, InvestmentIntent calldata intent)`
- 示例输出：`InvestmentIntentRegistered`, `InvestmentStateAdvanced`

## 对下游线程的影响
- 新增输入对象：`InvestmentIntent`
- 新增输出对象：`PositionState`, `InvestmentStateAdvanced` 事件, `getPositionState`, `getActualPositionSize`, `getInvestmentIntent`
- 新增异常：`IntentAlreadyRegistered`, `IntentNotRegistered`, `ClosedIntentCannotExecute`, `EntryConstraintViolation`, `ExitConstraintViolation`, `RuntimeExitMinOutTooLow`, `ActualPositionSizeNotRecorded`
- 新增命令/入口：`registerInvestmentIntent`, `executeReactiveTrigger`
- 需要下游同步更新的点：下游必须按新的接口形状传入 `intentId`、`InvestmentIntent` 与触发参数，不能再假设 Closed 状态可再次触发。
