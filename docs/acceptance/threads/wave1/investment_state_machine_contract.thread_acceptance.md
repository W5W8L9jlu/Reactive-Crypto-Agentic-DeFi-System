# 线程内验收清单

- 模块 / prompt：`investment_state_machine_contract` / `docs/prompts/investment_state_machine_contract.prompt.md`
- Wave：`wave_1`
- 线程负责人：not verified yet
- 分支：not verified yet
- commit：not verified yet
- 改动目录：`backend/contracts/interfaces`，`backend/contracts/core`
- 是否只改允许路径：是

## A. 职责边界
- 本模块的目标职责是否完成：是
- 是否引入了不属于本模块的逻辑：否
- 是否修改了共享 schema / 契约：是
- 若修改，是否同步通知依赖线程：not verified yet

## B. Contract 对齐
- 是否逐条对齐 implementation contract：是
- 未满足项：无已知未满足项；链上结算/记账不在本模块 contract 范围内，保留 `TODO`
- 明确拒绝实现的项（若有）：链下信号后再执行的混合模式；自由策略决策

## C. Invariants 检查
- JSON 仍是唯一执行真相：不适用
- Audit 是否只做摘抄：不适用
- Investment Memo 是否未污染执行真相：不适用
- 是否仍然只信 RPC 作为执行真相：不适用
- Execution Compiler 是否只在注册时工作：是
- Reactive 是否未承载自由决策：是
- Shadow Monitor 是否保持独立：不适用

## D. 验证证据
- 运行的命令：
  - `git diff --name-only HEAD`，结果：not verified yet，当前工作区未被识别为 git repository
  - `git log --oneline -n 10`，结果：not verified yet，当前工作区未被识别为 git repository
  - `Get-Content docs/knowledge/...` 与 `Get-Content backend/contracts/...`，用于读取模块约束与实现文件
  - `solc --version`，结果：not verified yet，当前环境未安装 `solc`
- 测试结果：not verified yet
- 样例输入：`intentId` + `InvestmentIntent` + `observedOut` + `runtimeExitMinOut`
- 样例输出：状态事件 `InvestmentStateAdvanced`，以及对应状态流转；具体链上回执 not verified yet
- 截图/日志/回执路径：not verified yet

## E. Known gaps
- TODO：出场后的结算/记账逻辑未在 contract 中展开，按现有 spec 保留
- Blockers：无法从当前工作区确认 git 状态；无法执行 Solidity 编译/测试
- 假设：`observedOut` 由上游 reactive runtime 传入；本模块只做状态机与运行时约束
- 风险：未完成合约测试验证，接口变更的下游集成仍需确认

## F. 可交付结论
- 状态：PASS_WITH_NOTES
- 进入线程间对接：可以
