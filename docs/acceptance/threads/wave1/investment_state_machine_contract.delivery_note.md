# 线程交付说明

> Canonical source for `investment_state_machine_contract` delivery notes.
> Duplicate file `investment_state_machine_contract_delivery_note.md` is retired and must only point here.

## 基本信息
- 模块名：`investment_state_machine_contract`
- Prompt 文件：`docs/prompts/investment_state_machine_contract.prompt.md`
- Wave：`wave_1`
- 负责人：`Worker 5`
- 分支：`w1-gate-fail-fix`
- commit：`c5afba2`

## 本次交付做了什么
- 保持 `IReactiveInvestmentCompiler.sol` 与 `ReactiveInvestmentCompiler.sol` 的现有状态机语义不变，没有为“过门”而发明新行为
- 新增 `backend/contracts/test/ReactiveInvestmentCompiler.t.sol`，把模块 contract 要求转成 7 个可复跑的 Foundry 测试
- 将本模块的 acceptance / handoff 证据收敛为单一 authoritative source，并退休冲突的下划线重复版本

## 修改了哪些文件
- `backend/contracts/test/ReactiveInvestmentCompiler.t.sol`
- `docs/acceptance/threads/wave1/investment_state_machine_contract.delivery_note.md`
- `docs/acceptance/threads/wave1/investment_state_machine_contract.test_evidence.md`
- `docs/acceptance/threads/wave1/investment_state_machine_contract.thread_acceptance.md`
- `docs/acceptance/handoffs/wave1/investment_state_machine_contract.thread_to_thread_handoff.md`
- `docs/acceptance/threads/wave1/investment_state_machine_contract_delivery_note.md`
- `docs/acceptance/threads/wave1/investment_state_machine_contract_test_evidence.md`
- `docs/acceptance/threads/wave1/investment_state_machine_contract_thread_acceptance.md`
- `docs/acceptance/handoffs/wave1/investment_state_machine_contract_thread_to_thread_handoff.md`

## 运行了哪些命令
```bash
git status --short --branch
git log --oneline -n 5
git branch --show-current
git rev-parse --short HEAD
D:\Foundry\bin\forge.exe build --root . --contracts backend/contracts
$env:FOUNDRY_CACHE_PATH='D:/reactive-crypto-agentic-DeFi-system/.foundry-cache'; D:\Foundry\bin\forge.exe test --root . --contracts backend/contracts --match-path 'backend/contracts/test/ReactiveInvestmentCompiler.t.sol' -vv
```

## 验收证据
- authoritative 测试记录：`docs/acceptance/threads/wave1/investment_state_machine_contract.test_evidence.md`
- authoritative 线程验收：`docs/acceptance/threads/wave1/investment_state_machine_contract.thread_acceptance.md`
- authoritative 线程交接：`docs/acceptance/handoffs/wave1/investment_state_machine_contract.thread_to_thread_handoff.md`
- compile / test 结果：`forge build` 成功；`forge test` 7/7 通过

## 没做什么
- 没有引入链下信号后再执行的混合模式
- 没有加入自由策略决策
- 没有补造链上部署回执或不存在的下游集成证据

## 对下游线程的影响
- 下游现在应只引用 canonical evidence 文件，不能再从下划线重复版本读取事实
- 接口和异常模型不变：`InvestmentIntent`、`PositionState`、`registerInvestmentIntent`、`executeReactiveTrigger`
- 下游仍必须遵守 `Closed` 不能再次触发，且不能把本模块理解为“链下先决定、链上再执行”的混合模型
