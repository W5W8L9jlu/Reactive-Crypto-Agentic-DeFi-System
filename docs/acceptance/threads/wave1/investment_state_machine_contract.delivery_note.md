# 线程交付说明

## 基本信息
- 模块名：`investment_state_machine_contract`
- Prompt 文件：`docs/prompts/investment_state_machine_contract.prompt.md`
- Wave：`wave_1`
- 负责人：not verified yet
- 分支：not verified yet
- commit：not verified yet

## 本次交付做了什么
- 定义了 `PendingEntry`、`ActivePosition`、`Closed` 三态与 `InvestmentIntent` 接口形状
- 实现了 `registerInvestmentIntent` 与 `executeReactiveTrigger` 的最小状态流转与 require 检查
- 增加了注册态、执行态、非法重入、约束失败相关错误与事件

## 修改了哪些文件
- `backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`

## 没做什么
- 没有实现链下信号后再执行的混合模式
- 没有引入自由策略决策
- 没有补充 Solidity 测试工程或执行链上编译验证

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status --short
Get-Content docs/knowledge/01_core/01_system_invariants.md
Get-Content docs/knowledge/01_core/02_domain_models.md
Get-Content docs/knowledge/05_reactive_contracts/02_investment_state_machine.md
Get-Content docs/contracts/investment_state_machine_contract.contract.md
Get-Content docs/knowledge/04_execution/01_execution_compiler.md
Get-ChildItem docs/prompts -Recurse -File | Where-Object { $_.Name -match 'investment_state_machine_contract' }
Get-Content backend/contracts/interfaces/IReactiveInvestmentCompiler.sol
Get-Content backend/contracts/core/ReactiveInvestmentCompiler.sol
solc --version
```

## 验收证据
- 测试截图：not verified yet
- 日志：not verified yet
- 示例 payload：`intentId`、`InvestmentIntent`、`observedOut`、`runtimeExitMinOut`
- 示例输出：`InvestmentIntentRegistered` / `InvestmentStateAdvanced` 事件与状态流转

## 对下游线程的影响
- 新增输入对象：`InvestmentIntent`
- 新增输出对象：状态枚举 `PositionState`、`InvestmentStateAdvanced` 事件
- 新增异常：`IntentAlreadyRegistered`、`IntentNotRegistered`、`ClosedIntentCannotExecute`、`EntryConstraintViolation`、`ExitConstraintViolation`、`RuntimeExitMinOutTooLow`、`ActualPositionSizeNotRecorded`
- 新增命令/入口：`registerInvestmentIntent`、`executeReactiveTrigger`
- 需要下游同步更新的点：下游执行器/编译器需要按新的状态机接口提交 `intentId` 和触发参数，不得假设 Closed 后仍可再次触发
