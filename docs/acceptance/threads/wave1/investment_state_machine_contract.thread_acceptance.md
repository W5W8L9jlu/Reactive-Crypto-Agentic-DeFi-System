# 线程内验收清单

> Canonical source for `investment_state_machine_contract` thread acceptance.
> Duplicate file `investment_state_machine_contract_thread_acceptance.md` is retired and must only point here.

- 模块 / prompt：`investment_state_machine_contract` / `docs/prompts/investment_state_machine_contract.prompt.md`
- Wave：`wave_1`
- 线程负责人：`Worker 5`
- 分支：`w1-gate-fail-fix`
- commit：`c5afba2`
- 改动目录：`backend/contracts/**` 与本模块 acceptance / handoff 文档
- 是否只改允许路径：`yes`

## A. 职责边界
- 本模块的目标职责是否完成：`yes`
- 是否引入了不属于本模块的逻辑：`no`
- 是否修改了共享 schema / 契约：`no`
- 是否把重复 evidence 收敛成单一权威来源：`yes`

## B. Contract 对齐
- 是否逐条对齐 implementation contract：`yes`
- 已验证项：`registerInvestmentIntent`、`executeReactiveTrigger`、状态流转与 require 检查
- 未满足项：无新增未满足项；出场后的结算 / 记账语义仍保持原实现中的 `TODO(domain)`
- 明确拒绝实现的项：`链下信号后再执行的混合模式`、`自由策略决策`

## C. Invariants 检查
- 状态只能是 `PendingEntry -> ActivePosition -> Closed`：`yes`，由 Foundry 测试覆盖
- `Closed` 不得再次触发：`yes`，由 `ClosedIntentCannotExecute` 测试覆盖
- 入场成功后记录 `actualPositionSize`：`yes`
- 入场和出场运行时检查不同：`yes`
- 是否存在 hybrid offchain-then-execute decision model：`no`

## D. 验证证据
- authoritative 测试文档：`docs/acceptance/threads/wave1/investment_state_machine_contract.test_evidence.md`
- 运行的命令：
  - `git branch --show-current` -> `w1-gate-fail-fix`
  - `git rev-parse --short HEAD` -> `c5afba2`
  - `D:\Foundry\bin\forge.exe build --root . --contracts backend/contracts` -> `Compiler run successful!`
  - `$env:FOUNDRY_CACHE_PATH='D:/reactive-crypto-agentic-DeFi-system/.foundry-cache'; D:\Foundry\bin\forge.exe test --root . --contracts backend/contracts --match-path 'backend/contracts/test/ReactiveInvestmentCompiler.t.sol' -vv` -> `7 passed; 0 failed; 0 skipped`
- 测试结果：`pass`
- 样例输入：`intentId` + `InvestmentIntent` + `observedOut` + `runtimeExitMinOut`
- 样例输出：`InvestmentIntentRegistered` / `InvestmentStateAdvanced` 与状态流转

## E. Known gaps
- TODO：出场后的结算 / 记账语义仍未在当前 contract 中展开
- 非模块 blocker：Wave 级 upstream-to-contract 映射与 downstream consumer 证明不在本线程范围内
- 环境告警：Foundry 的全局 signature cache / etherscan config 写入受沙箱限制，但不影响本地编译和测试通过

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 进入线程间对接：`可以`
- 结论说明：本线程自己的 canonical evidence 冲突已消除，且已有可复跑 compile/test 证据
